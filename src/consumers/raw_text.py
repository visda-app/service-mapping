from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TextSchema

from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
)
from models.text import RawText
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
    try:
        logger.debug(
            f"uuid={msg.value().uuid}, "
            f"text='{text_tip(msg.value().text)}' "
            f"sequence_id='{msg.value().sequence_id}'"
            "Received! 🤓"
        )
        RawText(
            uuid=msg.value().uuid,
            text=msg.value().text,
            sequence_id=msg.value().sequence_id
        ).save_to_db()
        mb.consumer_acknowledge(msg)
    except Exception as e:
        # Message failed to be processed
        logger.error('❌ message "{}" failed 👎'.format(msg.value().text))
        logger.exception(e)
        mb.consumer_negative_acknowledge(msg)

mb.close()