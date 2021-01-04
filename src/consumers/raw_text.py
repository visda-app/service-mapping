from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TextSchema

from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
)
from models.text import Text as TextModel
from models.db import create_all_tables


create_all_tables()

logger.info("⌛ Connecting to the message broker...")
mb = MessageBroker(
    broker_service_url=PulsarConf.client,
    consumer=Consumer(
        PulsarConf.text_topic,
        PulsarConf.subscription_name,
        schema_class=TextSchema
    ),
)
logger.info("✅ Connection to the message broker established.")


logger.info("🔁 Starting the infinite loop ... ")
while True:
    msg = mb.consumer_receive()
    mb.consumer_acknowledge(msg)
    try:
        logger.debug(
            f"uuid={msg.value().uuid}, "
            f"text='{text_tip(msg.value().text)}' "
            f"sequence_id='{msg.value().sequence_id}'"
            "Received! 🤓"
        )

        TextModel(
            id=msg.value().uuid,
            text=msg.value().text,
        ).save_or_update()

    except Exception as e:
        # Message failed to be processed
        logger.error(
            "❌ message failed 👎"
            f"uuid={msg.value().uuid}, "
            f"text='{text_tip(msg.value().text)}' "
        )
        logger.exception(e)

mb.close()
