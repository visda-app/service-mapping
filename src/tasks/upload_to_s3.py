"""
A task to watch the status of text embeddings
to see when it is finished for a job
"""
from asbool import asbool
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from lib.logger import logger
from lib import s3 as s3_client
from models.clustered_text import ClusteredText


class UploadToS3(BaseTask):
    """
    Upload the clustering data to S3 for future use. 
    """

    public_description = "Uploading results to the cloud storage"

    def _load_data_from_db(self, sequence_id):
        """
        Load clustering data from the DB
        """
        clustering = ClusteredText.get_last_by_sequence_id(sequence_id)
        return clustering


    def _upload_data_to_s3(self, sequence_id, data):
        """
        Upload clustering data to S3
        """
        s3_client.upload_clustering_data_to_s3(sequence_id, data)
        
    def _clear_data_from_db(self, sequence_id):
        """
        After uploading to S3 delete the clustering data from the DB
        """
        ClusteredText.delete_by_sequence_id(sequence_id)

    @record_start_finish_time_in_db
    def execute(self):
        job_id = self.job_id
        logger.debug(f" 🌩️ Uploading data to S3 job_id={job_id}")

        sequence_id = self.kwargs['sequence_id']

        total_num_steps = 3
        progress = 0

        progress += 1
        self.record_progress(progress, total_num_steps)
        data = self._load_data_from_db(sequence_id)

        progress += 1
        self.record_progress(progress, total_num_steps)
        self._upload_data_to_s3(sequence_id, data)

        progress += 1
        self.record_progress(progress, total_num_steps)
        self._clear_data_from_db(sequence_id)
