from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TaskSchema

from lib.logger import logger
from lib.utils import get_module_from_string
from configs.app import (
    PulsarConf,
)
from models.job import Job, JobStatus
from models.db import create_all_tables


create_all_tables()


def _execute_task(
    task_class,
    task_id,
    args,
    kwargs
):
    logger.debug(
        f"executing task_class={task_class}, "
        f"task_id={task_id}, "
        f"args={args}, "
        f"kwargs={kwargs}, "
    )


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
            f"args={msg.value().args}, "
            f"kwargs='{msg.value().kwargs}'"
            "Received! 🤓"
        )
        try:
            _execute_task(
                msg.value().task_class,
                msg.value().task_id,
                msg.value().args,
                msg.value().kwargs
            )
        except Exception as e:
            logger.error(
                f"❌ Task failed 👎 "
                f"task_class={msg.value().task_class}, "
                f"task_id={msg.value().task_id}, "
                f"args={msg.value().args}, "
                f"kwargs='{msg.value().kwargs}'"
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
