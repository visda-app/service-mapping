"""
A task to watch the status of text embeddings
to see when it is finished for a job
"""
from asbool import asbool
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from lib.logger import logger
from models.job_text_mapping import JobTextMapping
from lib.exceptions import ExternalDependencyNotCompleted
from lib.cache import cache_region, CacheKeys


class AwaitEmbedding(BaseTask):
    """
    Awaits the embedding task to finish.
    """

    public_description = "Embedding texts."

    @record_start_finish_time_in_db
    def execute(self):
        logger.debug("👀 watching for embeddings to finish...")
        job_id = self.job_id
        total_texts_cache_key = self.kwargs['total_num_texts_cache_key']
        total_num_texts = int(cache_region.get(total_texts_cache_key))
        done = JobTextMapping.get_processed_texts_count_by_job_id(job_id)
        logger.debug(f"Done={done} Total={total_num_texts}")
        
        stop_looping = asbool( cache_region.get(CacheKeys.get_stop_job_key(job_id)) )
        if stop_looping:
            logger.debug(
                f"Job job_id={job_id} is stopped due to stop signal on the cache. "
                f"CacheKey={CacheKeys.get_stop_job_key(job_id)}"
            )
            return
        # total = JobTextMapping.get_total_texts_count_by_job_id(job_id)
        self.record_progress(done, total_num_texts)
        if done < total_num_texts:
            raise ExternalDependencyNotCompleted
