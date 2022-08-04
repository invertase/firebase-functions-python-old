import json
import logging
import yaml

from firebase_functions import CloudEvent, options
from firebase_functions.pubsub import on_message_published
from firebase_functions.serving import serve_admin, serve_triggers

LOGGER = logging.getLogger(__name__)


@on_message_published(
    topic='my-awesome-topic',
    memory=options.Memory.MB_512,
    region='europe-west2',
    ingress=options.USE_DEFAULT,
)
def on_message_published_function(event: CloudEvent):
  LOGGER.debug(event)


triggers = {}
triggers['on_message_published_function'] = on_message_published_function


def test_sepc_pubsub():
  with serve_admin(triggers=triggers).test_client() as client:
    res = client.get('/__/functions.yaml')
    assert res.status_code == 200
    result = yaml.safe_load(res.get_data())
    assert result['endpoints']['onmessagepublishedfunction'][
        'eventTrigger'] is not None


def test_trigger_pubsub():

  with serve_triggers(triggers=triggers).test_client() as client:
    res_call = client.post(
        '/on_message_published_function',
        data=json.dumps({'foo': 'bar_pub_sub'}),
        content_type='application/json',
    )

    LOGGER.debug(res_call)