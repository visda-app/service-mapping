import json
from typing import List
from dataclasses import dataclass
from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TaskSchema


from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TextSchema
from chapar.schema_repo import TextItem as TextSchemaItem


from lib.logger import logger
from configs.app import PulsarConf


TEXT_BATCH_SIZE = 25


@dataclass
class TextItem:
    id: str
    text: str


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



def publish_texts_on_message_bus(text_items: List[TextItem], sequence_id: str):
    """
    Publish text text_items to the Pulsar message bus
    """
    num_items = len(text_items)
    logger.debug(
        f"Publishing messages to the message bus "
        f"num_texts={num_items}"
    )

    mb = MessageBroker(
        broker_service_url=PulsarConf.client,
        producer=Producer(
            PulsarConf.text_topic,
            schema_class=TextSchema
        )
    )
    logger.info("Producer created.")

    for i in range(0, num_items, TEXT_BATCH_SIZE):
        msg_items = [
            TextSchemaItem(
                uuid=text_item.id,
                text=text_item.text,
                sequence_id=sequence_id
            )
            for text_item in text_items[i : i + TEXT_BATCH_SIZE]
        ]
        msg = TextSchema(items=msg_items)
        mb.producer_send(msg)
        # TODO: Check if sending async causes any problems
        # mb.producer_send_async(msg)

    # TODO We should close connection, but I am not sure if closing it would terminate the async send
    logger.debug("Closing connection to Pulsar")
    mb.close()
