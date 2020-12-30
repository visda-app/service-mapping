import json
from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TextSchema

from lib.logger import logger
from configs.app import PulsarConf



mb = MessageBroker(
    broker_service_url=PulsarConf.client,
    consumer=Consumer(
        PulsarConf.text_topic, "sub-01",
        schema_class=TextSchema
    )
)


while True:
    try:
        msg = mb.consumer_receive()
        mb.consumer_acknowledge(msg)
    except KeyboardInterrupt:
        break
    try:
        # in_text = json.loads(msg.data().decode())
        logger.debug(f"Received message{msg} with data: {msg.data()} ✅")
        logger.debug(f"{msg.value().uuid}, {msg.value().text}")
    except Exception as e:
        # Message failed to be processed
        logger.info("❌ message '{}' 👎".format(msg.data()))
        logger.exception(e)
        # mb.consumer_negative_acknowledge(msg)

mb.close()
