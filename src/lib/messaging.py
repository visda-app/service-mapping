import json
from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TaskSchema

from lib.logger import logger
from configs.app import PulsarConf


def publish_task(
    task_class,
    task_args=None,
    task_kwargs=None,
    task_id=None,
    job_id=None,
    deliver_after_ms=0,
):
    """
    Publish a task on the message bus

    Args:
        task_args (list): a list of args for task
        task_kwargs (dict): a dictionary of args for the task
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
    if task_id:
        params['task_id'] = task_id
    if job_id:
        params['job_id'] = job_id
    if task_args:
        if type(task_args) not in [list, tuple]:
            raise ValueError('Args must be a list.')
        params['args'] = json.dumps(task_args)
    if task_kwargs:
        if type(task_kwargs) is not dict:
            raise ValueError('kwargs must a be a dict.')
        params['kwargs'] = json.dumps(task_kwargs)

    msg = TaskSchema(**params)

    mb.producer_send(msg, deliver_after_ms=deliver_after_ms)

    mb.close()
