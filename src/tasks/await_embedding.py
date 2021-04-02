"""
A task to watch the status of text embeddings
to see when it is finished for a job
"""
from tasks.base_task import BaseTask
from task.base_task import record_start_finish_time_in_db
from lib.logger import logger
from models.job_text_mapping import JobTextMapping
from lib.exceptions import ExternalDependencyNotCompleted


class AwaitEmbedding(BaseTask):
    """
    Awaits the embedding task to finish.
    """

    @record_start_finish_time_in_db
    def execute(self):
        logger.debug("👀 Watch Dog is checking...")
        job_id = self.job_id
        count = JobTextMapping.get_unprocessed_texts_count_by_job_id(job_id)
        if count > 0:
            raise ExternalDependencyNotCompleted
