import os
import googleapiclient.discovery
import pprint

from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TextSchema
from lib.logger import logger
from configs.app import (
    PulsarConf,
    ThirdParty
)
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from models.job_text_mapping import JobTextMapping


pp = pprint.PrettyPrinter().pprint


class Get3rdPartyData(BaseTask):
    """
    Get third party data such as YouTube.
    """

    public_description = "Getting YouTube comments."

    def __init__(self, *args, **kwargs):
        logger.debug(kwargs)
        if 'kwargs' in kwargs and 'video_id' not in kwargs['kwargs']:
                raise ValueError('Missing video_id in params.')
        super().__init__(*args, **kwargs)

    def _download_youtube_data_page(self, video_id, page_token=None):
        # Disable OAuthlib's HTTPS verification when running locally.
        # TODO: *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        aggregated_data = []

        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = ThirdParty.GOOGLE_API_KEY

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version,
            developerKey=DEVELOPER_KEY
        )

        params = {
            'part': 'snippet',
            'maxResults': 1000,
            'textFormat': 'plainText',
            'videoId': video_id
        }
        if page_token:
            params['pageToken'] = page_token

        request = youtube.commentThreads().list(**params)
        response = request.execute()

        return response

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
            mb.producer_send_async(msg)

        for snippet in snippets[sync_async_divider:]:
            msg = TextSchema(
                uuid=snippet['id'],
                text=snippet['text'],
                sequence_id=sequence_id
            )
            mb.producer_send(msg)

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

    def _get_comments_from_video(self, video_id):
        result = self._download_youtube_data_page(video_id)
        comments = self._extract_comments(result)
        while result.get('nextPageToken'):
            result = self._download_youtube_data_page(
                video_id,
                result.get('nextPageToken')
            )
            comments.extend(self._extract_comments(result))
        return comments


    @record_start_finish_time_in_db
    def execute(self):
        video_id = self.kwargs['video_id']

        TOTAL_STEPS = 2
        self.record_progress(0, TOTAL_STEPS)

        comments = self._get_comments_from_video(video_id)
        self.record_progress(1, TOTAL_STEPS)

        self._publish_texts_on_message_bus(comments, self.job_id)
        self.record_progress(2, TOTAL_STEPS)

        # self._record_job_text_relationship(comments, self.job_id)
        # self.record_progress(3, TOTAL_STEPS)

        # if self.kwargs.get('test'):
        #     with open('tests/data/youtube_comments.json', 'w') as f:
        #         f.write(json.dumps(result, indent=4))

