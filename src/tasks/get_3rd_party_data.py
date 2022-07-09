import os
from typing import Text
import googleapiclient.discovery
import pprint
from dataclasses import dataclass
from schema import Schema
import requests
from uuid import uuid4

from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TextSchema
from lib.logger import logger
from configs.app import (
    PulsarConf,
    ThirdParty
)
from lib import utils
from lib.cache import cache_region
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from models.text import Text as TextModelDB
from models.job_text_mapping import (
    JobTextMapping, TextTypes
)
from lib.cache import cache_region
from lib import nlp


pp = pprint.PrettyPrinter().pprint
DEVELOPER_KEY = ThirdParty.GOOGLE_API_KEY
MAX_RESULTS_PER_REQUEST = 100


@dataclass
class TextItem:
    id: str
    text: str


KWARGS_SCHEMA = {
    'source_url': str,
    'limit_cache_key': str,  # keeps the limit on the number of comments to be downloaded 
    'total_num_texts_cache_key': str,  # After the download, this gets set to the total downloaded texts
}


class Get3rdPartyData(BaseTask):
    """
    Get third party data such as YouTube.
    """
    public_description = "Downloading data from external source"

    def __init__(self, *args, **kwargs):
        logger.debug(kwargs)
        super().__init__(*args, **kwargs)

    def _download_youtube_data_page(self, video_id, page_token=None, max_results=None):
        # Disable OAuthlib's HTTPS verification when running locally.
        # TODO: *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        aggregated_data = []

        api_service_name = "youtube"
        api_version = "v3"

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version,
            developerKey=DEVELOPER_KEY
        )

        num_max_results = MAX_RESULTS_PER_REQUEST
        try:
            num_max_results = min(
                int(float(max_results)),
                MAX_RESULTS_PER_REQUEST
            )
        except ValueError as e:
            logger.exception(e)

        params = {
            'part': 'snippet',
            'maxResults': num_max_results,
            'textFormat': 'plainText',
            'videoId': video_id
        }
        if page_token:
            params['pageToken'] = page_token

        request = youtube.commentThreads().list(**params)
        try:
            response = request.execute()
            return response
        except Exception as e:
            logger.exception(e)
            return {}

    def _publish_texts_on_message_bus(self, text_items, sequence_id):
        """
        Publish text text_items to the Pulsar message bus

        Args:
            text_items (list): a list of input text TextItems
                [
                    TextItem(id='an_id', text='a_text')
                ]
            sequence_id (str): an id for the job
        """
        num_messages = len(text_items)
        logger.debug(
            f"Publishing messages to the message bus "
            f"num_messages={num_messages}"
        )
        mb = MessageBroker(
            broker_service_url=PulsarConf.client,
            producer=Producer(
                PulsarConf.text_topic,
                schema_class=TextSchema
            )
        )
        logger.info("Producer created.")

        for text_item in text_items:
            msg = TextSchema(
                uuid=text_item.id,
                text=text_items.text,
                sequence_id=sequence_id
            )
            mb.producer_send(msg)
            # mb.producer_send_async(msg)

        # TODO We should close connection, but I am not sure if closing it would terminate the async send
        logger.info("Closing connection to Pulsar")
        mb.close()

    def _record_job_text_relationship(self, text_items, job_id, text_type):
        """
        Save the relationship between a job and its texts in
        the db
        """
        for text_item in text_items:
            JobTextMapping(
                job_id=job_id,
                text_id=text_item.id,
                text_type=text_type,
            ).save_to_db()
    
    def _get_not_embedded_texts(self, text_items):
        """
        Searches DB for the text and embedding to find ones without
        embeddings
        """
        not_embedded_texts = []
        for text_item in text_items:
            if TextModelDB.get_embedding_by_text(text_item.text) is None:
                not_embedded_texts.append(text_item)
        return not_embedded_texts

    def _porcess_and_publish(self, text_items, sequence_id):
        """
        Gets an array of comments, and tokeninze and publishes them to messagebus
        """
        words = []
        for text_item in text_items:
            words = words.append( nlp.get_tokens(text_item.text) )
        words = list(set(words))
        word_items = [TextItem(id=str(uuid4()), text=word) for word in words]

        not_embedded_words = self._get_not_embedded_texts(word_items)

        self._record_job_text_relationship(
            not_embedded_words,
            sequence_id,
            TextTypes.WORD.value,
        )
        self._publish_texts_on_message_bus(not_embedded_words, sequence_id)
        self._record_job_text_relationship(
            text_items,
            sequence_id,
            TextTypes.SENTENCE.value
        )
        self._publish_texts_on_message_bus(text_items, sequence_id)

    def _extract_comments(self, youtube_data):
        results = []
        for item in youtube_data.get('items', []):
            text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            id = item['snippet']['topLevelComment']['id']
            results.append(TextItem(id=id, text=text))
        return results

    def _save_youtube_response_to_db(self, yt_resp):
        """
        Save youtube comment objects to DB
        """
        # TODO: Save comments to DB
        pass

    def _get_comments_for_source_url(self, source_url, limit_cache_key):
        num_downloaded_comments = 0

        comments = []
        video_id = utils.get_youtube_video_id(source_url)
        if not video_id:
            return comments

        remaining_allowed_limit = int(cache_region.get(limit_cache_key))

        is_first_run = True
        result = {}
        while (
            is_first_run
            or (result.get('nextPageToken') and remaining_allowed_limit > 0)
        ):
            logger.debug(f"remaining_allowed_limit={remaining_allowed_limit} ")            
            result = self._download_youtube_data_page(
                video_id,
                result.get('nextPageToken'),
                max_results=remaining_allowed_limit,
            )
            self._save_youtube_response_to_db(result)
            just_downloaded_comments = self._extract_comments(result)
            comments.extend(just_downloaded_comments)
            # Update the cache for keeping track of remaining limit
            num_downloaded_comments = len(just_downloaded_comments)
            logger.debug(f"num_downloaded_comments={num_downloaded_comments} ")
            remaining_allowed_limit = int(cache_region.get(limit_cache_key)) - num_downloaded_comments
            cache_region.set(limit_cache_key, remaining_allowed_limit)
            
            self._progress += 1
            self.record_progress(self._progress, self._total_steps)

            is_first_run = False
        if remaining_allowed_limit <= 0:
            self.append_event(
                event_lookup_key='text_count_exceeds_limit',
                source_url=source_url,
            )
        return comments


    def _test_get_comments_for_source_url(self, source_url, limit_cache_key):
        from tasks.test_youtube_comments import test_comments
        from uuid import uuid4
        comments = []
        for c in test_comments[:100]:
            comments.append(
                {
                    'id': str(uuid4()),
                    'text': c,
                }
            )

        return comments


    def _update_num_downloaded_texts(self, cache_key, comments):
        num_dls = cache_region.get(cache_key)
        if not num_dls:
            cache_region.set(cache_key, len(comments))
        else:
            cache_region.set(cache_key, num_dls + len(comments))



    @record_start_finish_time_in_db
    def execute(self):
        # Validate schema
        schema = Schema(KWARGS_SCHEMA)
        try:
            schema.validate(self.kwargs)
        except Exception as e:
            logger.exception(str(e))
            raise

        source_url = self.kwargs['source_url']
        limit_cache_key = self.kwargs['limit_cache_key']
        total_num_texts_cache_key = self.kwargs['total_num_texts_cache_key']
        limit = float(cache_region.get(limit_cache_key))

        self._total_steps = int(min(limit / MAX_RESULTS_PER_REQUEST, 100) + 1)
        self._progress = 0
        self.record_progress(self._progress, self._total_steps)

        comments = self._get_comments_for_source_url(source_url, limit_cache_key)
        # comments = self._test_get_comments_for_source_url(source_url, limit_cache_key)
        self._update_num_downloaded_texts(total_num_texts_cache_key, comments)
        logger.debug(f"Number of comments={len(comments)}, job_id={self.job_id}")
        self.append_event(
            event_lookup_key='text_download_finished',
            source_url=source_url,
            num_downloaded_texts=len(comments),
            job_id=self.job_id,
        )

        self._porcess_and_publish(comments, self.job_id)
        self.record_progress(self._total_steps, self._total_steps)

        # self._record_job_text_relationship(comments, self.job_id)
        # self.record_progress(3, self._total_steps)

        # if self.kwargs.get('test'):
        #     with open('tests/data/youtube_comments.json', 'w') as f:
        #         f.write(json.dumps(result, indent=4))

