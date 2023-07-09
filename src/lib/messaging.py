import json
from dataclasses import dataclass, asdict

from lib.logger import logger
from lib import sqs


TEXT_BATCH_SIZE = 1
TASK_MAX_PROCESSING_TIME_SEC = 300
NUM_RAW_TEXT_READ_FROM_Q = 10
NUM_TEXT_EMBEDDING_READ_FROM_Q = 10


@dataclass
class TaskItem:
    task_class: str
    job_id: str = None
    task_id: str = None
    args: tuple = None
    kwargs: dict = None


@dataclass
class TextItem:
    uuid: str
    text: str
    sequence_id: str = None


@dataclass
class TextEmbeddingItem:
    uuid: str
    text: str = None
    embedding: list[float] = None


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

    # task_class = String(required=True)
    # task_id = String()
    # args = String()
    # kwargs = String()
    task_item = TaskItem(task_class=task_class)
    if task_id:
        task_item.task_id = task_id
    if job_id:
        task_item.job_id = job_id
    if task_args:
        if type(task_args) not in [list, tuple]:
            raise ValueError('Args must be a list.')
        task_item.args = tuple(task_args)
    if task_kwargs:
        if type(task_kwargs) is not dict:
            raise ValueError('kwargs must a be a dict.')
        task_item.kwargs = task_kwargs

    msg = json.dumps(asdict(task_item))

    sqs.send_message(sqs.Queues.tasks, msg)


def pull_a_task_from_queue():
    
    q_name = sqs.Queues.tasks

    handles, msgs = sqs.receive_messages(
        q_name,
        max_number_of_messages=1,
        visibility_timeout_sec=TASK_MAX_PROCESSING_TIME_SEC
    )
    sqs.delete_messages(q_name, receipt_handles=handles)

    if len(msgs) == 0:
        return
    
    task_dict = json.loads(msgs[0])

    return TaskItem(**task_dict)


def _publish_texts_on_message_bus(
        queue_name: str,
        text_items: list[TextItem],
        sequence_id: str
        ):
    num_items = len(text_items)

    logger.debug(
        f"Publishing messages to the message bus "
        f"num_texts={num_items}"
    )

    for text_item in text_items:
        msg = {
            "uuid": text_item.uuid,
            "text": text_item.text,
            "sequence_id": sequence_id,
        }
        sqs.send_message(queue_name, json.dumps(msg))



def publish_texts_on_message_bus(text_items: list[TextItem], sequence_id: str):
    """
    Publish text text_items to the Pulsar message bus
    """
    q_name = sqs.Queues.raw_texts
    _publish_texts_on_message_bus(q_name, text_items, sequence_id)


def publish_text_for_embedding(text_item: TextItem):
    """
    Publish text text_item to the Pulsar message bus
    """
    q_name = sqs.Queues.texts
    _publish_texts_on_message_bus(q_name, [text_item], text_item.sequence_id)


def pull_raw_texts_from_queue():
    """
    """
    q_name = sqs.Queues.raw_texts

    handles, msgs = sqs.receive_messages(
        q_name,
        max_number_of_messages=NUM_RAW_TEXT_READ_FROM_Q,
        visibility_timeout_sec=TASK_MAX_PROCESSING_TIME_SEC
    )
    sqs.delete_messages(q_name, receipt_handles=handles)

    text_items = []
    for msg in msgs:
        raw_text_dict = json.loads(msg)
        text_items.append(TextItem(**raw_text_dict))

    return text_items


def pull_embeddings_from_queue():
    """
    """
    q_name = sqs.Queues.text_embeddings

    handles, msgs = sqs.receive_messages(
        q_name,
        max_number_of_messages=NUM_TEXT_EMBEDDING_READ_FROM_Q,
        visibility_timeout_sec=TASK_MAX_PROCESSING_TIME_SEC
    )
    
    sqs.delete_messages(q_name, receipt_handles=handles)

    text_embeddings = []
    for msg in msgs:
        text_embedding_dict = json.loads(msg)
        text_embeddings.append(TextEmbeddingItem(**text_embedding_dict))

    return text_embeddings
