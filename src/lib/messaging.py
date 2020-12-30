from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TaskSchema

from lib.logger import logger
from configs.app import PulsarConf


def publish_task(
    task_class,
    task_args=None,
    task_kwargs=None,
    task_id=None
):
    """
    Publish a task on the message bus

    """
    mb = MessageBroker(
        broker_service_url=PulsarConf.client,
        producer=Producer(
            PulsarConf.task_topic,
            schema_class=TaskSchema
        )
    )
    logger.info("Producer created.")

    # task_class = String(required=True)
    # task_id = String()
    # args = String()
    # kwargs = String()
    params = {
        "task_class": task_class,
    }
    if task_args:
        params['args'] = task_args
    if task_id:
        params['task_id'] = task_id
    if task_args:
        params['args'] = task_args
    if task_kwargs:
        params['kwargs'] = task_kwargs

    msg = TaskSchema(**params)

    mb.producer_send(msg)

    mb.close()
