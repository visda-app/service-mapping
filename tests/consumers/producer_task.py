import json
from chapar.message_broker import MessageBroker, Producer
from chapar.schema_repo import TaskSchema

from lib.logger import logger
from configs.app import PulsarConf
import pulsar, _pulsar
from uuid import uuid4


# import pdb; pdb.set_trace()


mb = MessageBroker(
    broker_service_url=PulsarConf.client,
    producer=Producer(
        "apache/pulsar/task-topic",
        schema_class=TaskSchema
    )
)

logger.info("Producer created.")

# movie_review = 'I admit, the great majority of films released before say 1933 are just not for me. Of the dozen or so "major" silents I have viewed, one I loved (The Crowd), and two were very good (The Last Command and City Lights, that latter Chaplin circa 1931).<br /><br />So I was apprehensive about this one, and humor is often difficult to appreciate (uh, enjoy) decades later. I did like the lead actors, but thought little of the film.<br /><br />One intriguing sequence. Early on, the guys are supposed to get "de-loused" and for about three minutes, fully dressed, do some schtick. In the background, perhaps three dozen men pass by, all naked, white and black (WWI ?), and for most, their butts, part or full backside, are shown. Was this an early variation of beefcake courtesy of Howard Hughes?'
movie_review = 'I admit, the great majority Howard Hughes?'
# msg = {"uuid": str(uuid4()), "text": movie_review, "embedding": [3, 2.1, 0.34]}
msg = TaskSchema(
    task_class="a_task_class",
    kwargs=json.dumps({
        'video_id': 'a random video id'
    })
)

for i in range(1):
    mb.producer_send(msg)


mb.close()
