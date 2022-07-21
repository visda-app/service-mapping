import json
from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TaskSchema

from lib.logger import logger
from lib.exceptions import ExternalDependencyNotCompleted
from lib.utils import get_class_from_string
from configs.app import (
    PulsarConf,
    k8s_readiness_probe_file,
)


def _execute_task(
    task_class_string,
    job_id,
    task_id,
    args,
    kwargs
):
    logger.debug(
        f"🏃‍♀️ executing task_class_string={task_class_string}, "
        f"job_id={job_id}, "
        f"task_id={task_id}, "
        f"args={args}, "
        f"kwargs={kwargs}, "
    )
    task_class = get_class_from_string(task_class_string)
    task = task_class(task_id=task_id)
    try:
        task.execute()
        task.submit_next_to_queue()
    except ExternalDependencyNotCompleted:
        task.retry_with_delay()


def consumer_loop(message_broker):
    """
    Infinite loop. Consume tasks one by one and perform the required actions.
    """
    mb = message_broker
    while True:
        msg = mb.consumer_receive()
        mb.consumer_acknowledge(msg)
        logger.debug(
            f"task_class={msg.value().task_class}, "
            f"task_id={msg.value().task_id}, "
            f"job_id={msg.value().job_id}, "
            f"args={msg.value().args}, "
            f"kwargs='{msg.value().kwargs}'"
            "  Received! 🤓"
        )
        try:
            _execute_task(
                msg.value().task_class,
                msg.value().job_id,
                msg.value().task_id,
                msg.value().args,
                msg.value().kwargs
            )
        except Exception as e:
            logger.exception(
                f"❌ Task failed 👎 "
                f"task_class={msg.value().task_class}, "
                f"task_id={msg.value().task_id}, "
                f"args={msg.value().args}, "
                f"kwargs='{msg.value().kwargs}' "
                f"error_msg= {str(e)}"
            )
            logger.exception(e)
            # TODO: Should it retry the task?


def main():
    logger.info("⌛ Loading NLP modules...")
    from lib import nlp
    with open(k8s_readiness_probe_file, 'w') as f:
        f.write('🍌 I am healthy 🥑')
    logger.info("✅ NLP models are loaded.")

    logger.info("⌛ Connecting to the message broker...")
    mb = MessageBroker(
        broker_service_url=PulsarConf.client,
        consumer=Consumer(
            PulsarConf.task_topic,
            PulsarConf.subscription_name,
            schema_class=TaskSchema
        ),
    )
    logger.info("✅ Connection to the message broker established.")

    logger.info("🔁 Starting the infinite loop ... ")
    consumer_loop(mb)

    mb.close()


main()
