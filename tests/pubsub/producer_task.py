import json
from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TaskSchema

from lib.logger import logger
from configs.app import PulsarConf
import pulsar, _pulsar
from uuid import uuid4


# import pdb; pdb.set_trace()


mb = MessageBroker(
    broker_service_url=PulsarConf.client,
    producer=Producer(
        "apache/pulsar/task-topic",
        schema_class=TaskSchema
    )
)

logger.info("Producer created.")

# msg = TaskSchema(
#     task_class="tasks.base.Base",
#     kwargs=json.dumps({
#         'video_id': 'a random video id'
#     })
# )
job_id = str(uuid4())
task_id = str(uuid4())
task_class = "tasks.get_3rd_party_data.Get3rdPartyData"
msg = TaskSchema(
    task_class=task_class,
    job_id=job_id,
    task_id=task_id,
    kwargs=json.dumps({
        'video_id': 'oieNTzEeeX0'
    })
)
logger.info(f"Job submitted. task_class= {task_class}, job_id= {job_id}, task_id= {task_id}")

mb.producer_send(msg)

mb.close()
