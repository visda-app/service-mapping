import json
from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TaskSchema

from lib.logger import logger
from lib.utils import get_module_and_class_from_string
from configs.app import (
    PulsarConf,
)


def _execute_task(
    task_class,
    job_id,
    task_id,
    args,
    kwargs
):
    logger.debug(
        f"🏃‍♀️ executing task_class={task_class}, "
        f"job_id={job_id}, "
        f"task_id={task_id}, "
        f"args={args}, "
        f"kwargs={kwargs}, "
    )
    if not args:
        args = '[]'
    if not kwargs:
        kwargs = "{}"
    args = json.loads(args)
    kwargs = json.loads(kwargs)
    if job_id:
        kwargs['job_id'] = job_id
    if task_id:
        kwargs['task_id'] = task_id

    task_module, task_class_name = get_module_and_class_from_string(task_class)

    getattr(task_module, task_class_name)().execute(*args, **kwargs)


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
            f"task_id={msg.value().job_id}, "
            f"args={msg.value().args}, "
            f"kwargs='{msg.value().kwargs}'"
            "Received! 🤓"
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
