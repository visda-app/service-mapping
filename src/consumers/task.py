import json

from lib.logger import logger
from lib.exceptions import ExternalDependencyNotCompleted
from lib.utils import get_class_from_string
from lib import messaging
from configs.app import (
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


def consumer_loop():
    """
    Infinite loop. Consume tasks one by one and perform the required actions.
    """
    while True:
        msg = messaging.pull_a_task_from_queue()
        if msg is None:
            continue

        logger.debug(
            f"task_class={msg.task_class}, "
            f"task_id={msg.task_id}, "
            f"job_id={msg.job_id}, "
            f"args={msg.args}, "
            f"kwargs='{msg.kwargs}'"
            "  Received! 🤓"
        )
        try:
            _execute_task(
                msg.task_class,
                msg.job_id,
                msg.task_id,
                msg.args,
                msg.kwargs
            )
            logger.debug(
                "✅ Task execution was successful "
                f"task_class={msg.task_class}, "
                f"task_id={msg.task_id}, "
                f"job_id={msg.job_id}, "
                f"args={msg.args}, "
                f"kwargs='{msg.kwargs}'"
            )
        except Exception as e:
            logger.exception(
                f"❌ Task failed 👎 "
                f"task_class={msg.task_class}, "
                f"task_id={msg.task_id}, "
                f"args={msg.args}, "
                f"kwargs='{msg.kwargs}' "
                f"error_msg= {str(e)}"
            )
            # TODO: Should it retry the task?


def main():
    logger.info("⌛ Loading NLP modules...")
    from lib import nlp
    with open(k8s_readiness_probe_file, 'w') as f:
        f.write('🍌 I am healthy 🥑')
    logger.info("✅ NLP models are loaded.")

    logger.info("🔁 Starting the infinite loop ... ")
    consumer_loop()


main()
