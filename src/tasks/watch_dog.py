"""
A task to watch the status of text embeddings
to see when it is finished for a job
"""
import time
from tasks.base import Base
from lib.logger import logger
from lib.messaging import publish_task
from models.job import JobTextRelation

SLEEP_BEFORE_REPUBLISH_SELF = 1


def _publish_clustering_task(text_embedding):
    """
    Publish a task for the clustering on the message bus

    """
    sequence_id = text_embedding.get_sequence_id()

    task_class = 'tasks.cluster_texts.ClusterTexts'
    task_id = sequence_id
    args = ''
    kwargs = json.dumps({
        "sequence_ids": [sequence_id]
    })
    publish_task(
        task_class,
        task_args=args,
        task_kwargs=kwargs,
        task_id=task_id
    )


class WatchDog(Base):
    """
    Watches for the previous task to finish. If finished, launches the next
    task. If not, re-submit self to keep watching.
    """
    def _publish_self(self, *args, **kwargs):
        task_class = 'tasks.watch_dog.WatchDog'
        publish_task(
            task_class,
            task_kwargs=kwargs,
        )

    def _publish_next_task(self, *args, **kwargs):
        task_class = kwargs['next_task']
        next_kwargs = kwargs['next_task_kwargs']
        publish_task(
            task_class,
            task_kwargs=next_kwargs,
        )

    def execute(self, *args, **kwargs):
        logger.debug("👀 Watch Dog is checking...")
        job_id = kwargs['job_id']
        count = JobTextRelation.get_unprocessed_texts_count_by_job_id(job_id)
        if count > 0:
            time.sleep(SLEEP_BEFORE_REPUBLISH_SELF)
            self._publish_self(*args, **kwargs)
        else:
            self._publish_next_task(*args, **kwargs)
        import pdb; pdb.set_trace()
