import json

from lib.logger import logger
from uuid import uuid4
from lib import messaging


logger.info("Producer created.")

job_id = str(uuid4())
task_id = str(uuid4())
task_class = "tasks.dummy_task.DummyTask"

logger.info(f"Job submitted. task_class= {task_class}, job_id= {job_id}, task_id= {task_id}")

messaging.publish_task(
    task_class,
    job_id=job_id,
    task_kwargs={
        'video_id': 'oieNTzEeeX0'
    },
)
