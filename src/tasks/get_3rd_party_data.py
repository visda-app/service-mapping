import os
import json
import googleapiclient.discovery
from uuid import uuid4

from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TextSchema
from lib.logger import logger
from configs.app import (
    PulsarConf,
    ThirdParty
)
from tasks.base import Base
from models.job import Job as JobModel
from models.job import (
    JobStatus,
    JobTextRelation
)
from lib.messaging import publish_task


class Get3rdPartyData(Base):
    """
    Get third party data such as YouTube.
    """
    def _download_youtube_data(self, video_id):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
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
            'maxResults': 1000,
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
            JobTextRelation(
                job_id=job_id,
                text_id=snippet['id']
            ).save_to_db()

    def _submit_watch_dog_task(self, job_id):
        """
        Submits a task to watch when the embedding is done for all
        texts for a job_id
        """
        task_class = 'tasks.watch_dog.WatchDog'
        kwargs = json.dumps({
            "job_id": job_id,
            "next_task": "tasks.cluster_texts.ClusterTexts",
            "next_task_kwargs": {
                "sequence_ids": [job_id]
            }
        })
        publish_task(
            task_class,
            task_args=None,
            task_kwargs=kwargs,
            task_id=None
        )

    def _extract_comments(self, youtube_data):
        results = []
        for item in youtube_data.get('items', []):
            text = item['snippet']['topLevelComment']['snippet']['textOriginal']
            id = item['snippet']['topLevelComment']['id']
            results.append({
                "text": text,
                "id": id
            })
        return results

    def execute(self, *args, **kwargs):
        video_id = kwargs['video_id']
        job_id = str(uuid4())

        result = self._download_youtube_data(video_id)
        comments = self._extract_comments(result)

        JobModel.log_status(
            job_id,
            JobStatus.third_party_data_acquired,
        )

        self._publish_texts_on_message_bus(comments, job_id)
        self._record_job_text_relationship(comments, job_id)
        self._submit_watch_dog_task(job_id)

        # if kwargs.get('test'):
        #     with open('tests/data/youtube_comments.json', 'w') as f:
        #         f.write(json.dumps(result, indent=4))

