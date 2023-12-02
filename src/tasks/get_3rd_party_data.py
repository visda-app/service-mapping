import os
import math
import googleapiclient.discovery
import pprint
from schema import Schema, Optional
import requests
from uuid import uuid4


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
from lib.messaging import publish_texts_on_message_bus, TextItem


pp = pprint.PrettyPrinter().pprint
DEVELOPER_KEY = ThirdParty.GOOGLE_API_KEY
MAX_RESULTS_PER_REQUEST = 100


KWARGS_SCHEMA = {
    'source_url': str,
    'limit_cache_key': str,  # keeps the limit on the number of comments to be downloaded 
    'total_num_texts_cache_key': str,  # After the download, this gets set to the total downloaded texts
    Optional('use_test_data'): bool,
}


class Get3rdPartyData(BaseTask):
    """
    Get third party data such as YouTube.
    """
    public_description = "Downloading data"

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

    def _record_job_text_relationship(self, text_items, job_id, text_type):
        """
        Save the relationship between a job and its texts in
        the db
        """
        for text_item in text_items:
            JobTextMapping(
                job_id=job_id,
                text_id=text_item.uuid,
                text_type=text_type,
            ).save_to_db()
    
    def _get_not_embedded_texts(self, text_items):
        """
        Searches DB for the text and embedding to find ones without
        embeddings
        """
        not_embedded_texts = []
        # TODO: speed this up by batching
        for text_item in text_items:
            if TextModelDB.get_embedding_by_text(text_item.text) is None:
                not_embedded_texts.append(text_item)
        return not_embedded_texts

    def _tokenize_and_record_and_publish(self, text_items, sequence_id):
        """
        Gets an array of comments, and tokeninze and publishes them to messagebus
        """
        words = []
        sentences = []
        for text_item in text_items:
            words.extend( nlp.get_tokens(text_item.text) )

        for text_item in text_items:
            sentences.extend( nlp.get_sentences(text_item.text) )

        # remove redundancies while keeping order
        words_unique = list(dict.fromkeys(words))
        word_items = [TextItem(uuid=str(uuid4()), text=word) for word in words_unique]

        sentences_unique = list(dict.fromkeys(sentences))
        sentence_items = [TextItem(uuid=str(uuid4()), text=sentence) for sentence in sentences_unique]

        not_embedded_words = self._get_not_embedded_texts(word_items)
        not_embedded_senteces = self._get_not_embedded_texts(sentence_items)

        self._record_job_text_relationship(
            not_embedded_words,
            sequence_id,
            TextTypes.EXTRACTED_WORD.value,
        )
        self._record_job_text_relationship(
            not_embedded_senteces,
            sequence_id,
            TextTypes.EXTRACTED_SENTENCE.value,
        )
        self._record_job_text_relationship(
            text_items,
            sequence_id,
            TextTypes.RAW_TEXT.value
        )

        publish_texts_on_message_bus(not_embedded_words, sequence_id)
        publish_texts_on_message_bus(not_embedded_senteces, sequence_id)
        publish_texts_on_message_bus(text_items, sequence_id)

    def _extract_comments(self, youtube_data):
        results = []
        for item in youtube_data.get('items', []):
            text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            id = item['snippet']['topLevelComment']['id']
            results.append(TextItem(uuid=id, text=text))
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
            comments.append(TextItem(uuid=str(uuid4()), text=c))

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

        self._total_steps = math.ceil(limit / MAX_RESULTS_PER_REQUEST) + 2
        self._progress = 0
        self.record_progress(self._progress, self._total_steps)

        if self.kwargs.get('use_test_data'):
            comments = self._test_get_comments_for_source_url(source_url, limit_cache_key)
        else:
            comments = self._get_comments_for_source_url(source_url, limit_cache_key)
        self._update_num_downloaded_texts(total_num_texts_cache_key, comments)
        logger.debug(f"Number of comments={len(comments)}, job_id={self.job_id}")
        self.append_event(
            event_lookup_key='text_download_finished',
            source_url=source_url,
            num_downloaded_texts=len(comments),
            job_id=self.job_id,
        )
        self.record_progress(self._total_steps - 1, self._total_steps)

        self._tokenize_and_record_and_publish(comments, self.job_id)
        self.record_progress(self._total_steps, self._total_steps)

        # self._record_job_text_relationship(comments, self.job_id)
        # self.record_progress(3, self._total_steps)

        # if self.kwargs.get('test'):
        #     with open('tests/data/youtube_comments.json', 'w') as f:
        #         f.write(json.dumps(result, indent=4))

