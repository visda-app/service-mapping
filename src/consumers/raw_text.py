from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TextSchema

from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
)
from models.text import Text as TextModel
from models.job_text_mapping import JobTextMapping
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
    for item in msg.value().items:
        try:
            logger.debug(
                f"uuid={item.uuid}, "
                f"text='{text_tip(item.text)}' "
                f"sequence_id='{item.sequence_id}' "
                "Received! 🤓"
            )
            text_record = TextModel(
                id=item.uuid,
                text=item.text,
            ).save_or_update()

        except Exception as e:
            # Message failed to be processed
            logger.error(
                "❌ message failed 👎"
                f"uuid={item.uuid}, "
                f"text='{text_tip(item.text)}' "
            )
            logger.exception(e)

mb.close()
