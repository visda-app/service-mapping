"""
A task to watch the status of text embeddings
to see when it is finished for a job
"""

from tasks.base import Base
from lib.logger import logger
from lib.messaging import publish_task
from models.job import JobTextRelation


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
    def execute(self, *args, **kwargs):
        logger.debug("👀 Watch Dog is checking...")
        job_id = kwargs['job_id']
        JobTextRelation.get_unprocessed_texts_by_job_id(job_id)
        import pdb; pdb.set_trace()
