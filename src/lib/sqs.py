import boto3
import pprint
import inspect
# from dataclasses import dataclass, fields, asdict
from uuid import uuid4
from lib.logger import logger
from time import time

from configs.app import AWS as aws_configs


DEFAULT_VISIBILITY_TIMEOUT_SEC = '60'  # max: 43,200 (12 hours)
DEFAULT_MESSAGE_GROUP_ID = 'groupA'

queue_urls = {}
client = boto3.client(
    'sqs',
    aws_access_key_id=aws_configs.access_key_id,
    aws_secret_access_key=aws_configs.secret_access_key,
    region_name=aws_configs.region,
)


class Queues:
    """
    Application wide queues.

    ** only add the name of queues to the class attributes
    """
    tasks = 'tasks.fifo'
    raw_texts = 'raw_texts.fifo'    # For write in DB
    texts = 'texts.fifo'    # For being embedded by the deep learning model
    text_embeddings = 'text_embeddings.fifo'
    test = 'just_for_test.fifo'

    @classmethod
    def get_all_queue_names(cls):
        """
        Returns the queue names. E.g., 
            [
                'raw_text_queue.fifo', 
                'task_queue.fifo',
                'text_embedding_queue.fifo'
            ]
        """
        queue_names = []
        for attr_name, val in inspect.getmembers(cls):
            if not attr_name.startswith("_") and not inspect.ismethod(val):
                queue_names.append(val)
        return queue_names


def create_queue(queue_name):
    visibility_timeout_sec = DEFAULT_VISIBILITY_TIMEOUT_SEC
    try:
        create_resp = client.create_queue(
            QueueName=queue_name,
            Attributes={
                'ReceiveMessageWaitTimeSeconds': '0',
                'VisibilityTimeout': visibility_timeout_sec,
                'FifoQueue': 'true',
            },
            tags={
                'string': 'string'
            }
        )
    except Exception as e:
        logger.exception(e)
        raise
    queue_url = create_resp['QueueUrl']

    return queue_url


def create_all_queues():
    for q in Queues.get_all_queue_names():
        q_url = create_queue(q)
        queue_urls[q] = q_url


def get_queue_url(queue_name):
    return queue_urls[queue_name]


def send_message(
        queue_name: str,
        msg: str,
        message_group_id: str=DEFAULT_MESSAGE_GROUP_ID,
        ):
    queue_url = get_queue_url(queue_name)
    send_resp = client.send_message(
        QueueUrl=queue_url,
        MessageBody=msg,
        # DelaySeconds=i,
        MessageGroupId=message_group_id,
        MessageDeduplicationId=str(uuid4()),
    )
    status_code = send_resp["ResponseMetadata"]["HTTPStatusCode"]
    return status_code


def receive_messages(
        queue_name:str,
        max_number_of_messages=1,
        visibility_timeout_sec=DEFAULT_VISIBILITY_TIMEOUT_SEC,
        ):
    queue_url = get_queue_url(queue_name)
    receive_request_attempt_id = str(uuid4())

    receive_resp = client.receive_message(
        QueueUrl=queue_url,
        AttributeNames=['All'],
        MaxNumberOfMessages=max_number_of_messages,
        VisibilityTimeout=int(visibility_timeout_sec),
        WaitTimeSeconds=0,
        ReceiveRequestAttemptId=receive_request_attempt_id,
    )

    receipt_handles = [ e["ReceiptHandle"] for e in  receive_resp.get("Messages", [])]

    msgs = [ e["Body"] for e in receive_resp.get("Messages", []) ]
    return receipt_handles, msgs


def delete_messages(
        queue_name: str,
        receipt_handles: list[str]
        ):
    queue_url = get_queue_url(queue_name)
    if not receipt_handles:
        return
    try:
        del_resp = client.delete_message_batch(
            QueueUrl=queue_url,
            Entries=[
                {
                    'Id': str(uuid4()),
                    'ReceiptHandle': handle
                } 
                for handle in receipt_handles
            ]
        )
    except Exception as e:
        logger.exception(e)
        raise

    success = del_resp.get("Successful", [])
    fail = del_resp.get("Failed", [])

    return success, fail


create_all_queues()


def test_sqs_health():
    q_name = Queues.test

    expected_message = f"A test message uuid={str(uuid4())} "
    try:
        # send messages 
        status = send_message(q_name, expected_message)
        if status != 200:
            raise Exception(f"Sending message to queue={q_name} failed.")

        # receive messages
        receipt_handles, msgs = receive_messages(
            q_name,
            max_number_of_messages=10,
            visibility_timeout_sec=3
        )
        msgs_len = len(msgs)
        if msgs_len != 1: 
            raise Exception(f"Expected '1' message but '{msgs_len}' messages received.")
        actual_message = msgs[0]
        if expected_message != actual_message:
            raise Exception(f"Expected message={expected_message}, but message={actual_message} received.")

        # delete message
        success, fail = delete_messages(q_name, receipt_handles)
        if len(success) != 1 or len(fail) != 0:
            raise Exception("Failed to delete message.")
    except:
        client.purge_queue(QueueUrl=get_queue_url(q_name))
        raise
    logger.info("🫥 . AWS SQS seems to be healthy...")


test_sqs_health()

