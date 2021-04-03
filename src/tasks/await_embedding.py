"""
A task to watch the status of text embeddings
to see when it is finished for a job
"""
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from lib.logger import logger
from models.job_text_mapping import JobTextMapping
from lib.exceptions import ExternalDependencyNotCompleted


class AwaitEmbedding(BaseTask):
    """
    Awaits the embedding task to finish.
    """

    @record_start_finish_time_in_db
    def execute(self):
        logger.debug("👀 watching for embeddings to finish...")
        job_id = self.job_id
        not_done = JobTextMapping.get_unprocessed_texts_count_by_job_id(job_id)
        logger.debug(f"NotDone={not_done}")
        total = JobTextMapping.get_total_texts_count_by_job_id(job_id)
        self.record_progress(total - not_done, total)
        if not_done > 0:
            raise ExternalDependencyNotCompleted
