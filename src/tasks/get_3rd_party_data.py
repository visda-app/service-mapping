import os
import googleapiclient.discovery
import pprint
from schema import Schema
import requests

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
from models.job_text_mapping import JobTextMapping
from lib.cache import cache_region


pp = pprint.PrettyPrinter().pprint
DEVELOPER_KEY = ThirdParty.GOOGLE_API_KEY
MAX_RESULTS_PER_REQUEST = 100


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

    def _download_youtube_data_page(self, video_id, page_token=None):
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

        params = {
            'part': 'snippet',
            'maxResults': MAX_RESULTS_PER_REQUEST,
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

    def _publish_texts_on_message_bus(self, snippets, sequence_id):
        """
        Publish text snippets to the Pulsar message bus

        Args:
            snippets (list): a list of input text snippets
                [
                    {"id": ..., "text": ...}
                ]
            sequence_id (str): an id for the job
        """
        mb = MessageBroker(
            broker_service_url=PulsarConf.client,
            producer=Producer(
                PulsarConf.text_topic,
                schema_class=TextSchema
            )
        )
        logger.info("Producer created.")

        sync_async_divider = 100
        for snippet in snippets[:sync_async_divider]:
            msg = TextSchema(
                uuid=snippet['id'],
                text=snippet['text'],
                sequence_id=sequence_id
            )
            mb.producer_send(msg)

        for snippet in snippets[sync_async_divider:]:
            msg = TextSchema(
                uuid=snippet['id'],
                text=snippet['text'],
                sequence_id=sequence_id
            )
            mb.producer_send_async(msg)

        mb.close()

    # def _record_job_text_relationship(self, snippets, job_id):
    #     """
    #     Save the relationship between a job and its texts in
    #     the db
    #     """
    #     for snippet in snippets:
    #         JobTextMapping(
    #             job_id=job_id,
    #             text_id=snippet['id']
    #         ).save_to_db()

    def _extract_comments(self, youtube_data):
        results = []
        for item in youtube_data.get('items', []):
            text = item['snippet']['topLevelComment']['snippet']['textDisplay']
            id = item['snippet']['topLevelComment']['id']
            results.append({
                "text": text,
                "id": id
            })
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
                result.get('nextPageToken')
            )
            num_downloaded_comments = int(result.get("pageInfo", {}).get("resultsPerPage", 0))

            logger.debug(f"num_downloaded_comments={num_downloaded_comments} ")

            remaining_allowed_limit = int(cache_region.get(limit_cache_key)) - num_downloaded_comments
            cache_region.set(limit_cache_key, remaining_allowed_limit)
            self._save_youtube_response_to_db(result)
            comments.extend(self._extract_comments(result))
            
            self._progress += 1
            self.record_progress(self._progress, self._total_steps)

            is_first_run = False
        if remaining_allowed_limit <= 0:
            self.append_an_event("Number of comments exceeds allowed limit.")
        return comments
    
    def get_events(self):
        events = super().get_events()
        return events

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
        self._update_num_downloaded_texts(total_num_texts_cache_key, comments)
        logger.debug(f"Number of comments={len(comments)}, job_id={self.job_id}")

        self._publish_texts_on_message_bus(comments, self.job_id)
        self.record_progress(self._total_steps, self._total_steps)

        # self._record_job_text_relationship(comments, self.job_id)
        # self.record_progress(3, self._total_steps)

        # if self.kwargs.get('test'):
        #     with open('tests/data/youtube_comments.json', 'w') as f:
        #         f.write(json.dumps(result, indent=4))

