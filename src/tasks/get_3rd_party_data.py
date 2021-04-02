import os
import googleapiclient.discovery

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


class Get3rdPartyData(BaseTask):
    """
    Get third party data such as YouTube.
    """
    def _download_youtube_data(self, video_id):
        # Disable OAuthlib's HTTPS verification when running locally.
        # TODO: *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = ThirdParty.GOOGLE_API_KEY

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version,
            developerKey=DEVELOPER_KEY
        )

        params = {
            'part': 'snippet',
            'maxResults': 10,
            'textFormat': 'plainText',
            'videoId': video_id
        }
        # if kwargs.get('page_token'):
        #     params['pageToken'] = kwargs['page_token']

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

        for snippet in snippets:
            msg = TextSchema(
                uuid=snippet['id'],
                text=snippet['text'],
                sequence_id=sequence_id
            )
            mb.producer_send(msg)

        mb.close()

    def _record_job_text_relationship(self, snippets, job_id):
        """
        Save the relationship between a job and its texts in
        the db
        """
        for snippet in snippets:
            JobTextMapping(
                job_id=job_id,
                text_id=snippet['id']
            ).save_to_db()

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

    @record_start_finish_time_in_db
    def execute(self):
        video_id = self.kwargs['video_id']

        result = self._download_youtube_data(video_id)
        comments = self._extract_comments(result)

        self._publish_texts_on_message_bus(comments, self.job_id)
        self._record_job_text_relationship(comments, self.job_id)

        # if self.kwargs.get('test'):
        #     with open('tests/data/youtube_comments.json', 'w') as f:
        #         f.write(json.dumps(result, indent=4))

