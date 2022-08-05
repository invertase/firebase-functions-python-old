import logging
import yaml

from firebase_functions import options
from firebase_functions.pubsub import on_message_published, CloudEventPublishedMessage
from firebase_functions.serving import serve_admin, serve_triggers

from cloudevents.http import to_structured, CloudEvent

LOGGER = logging.getLogger(__name__)
attributes = {
    'specversion':
        '1.0',
    'id':
        '5320408004945103',
    'source':
        '''pubsub.googleapis.com/projects/
        python-functions-testing/topics/test-topic''',
    'type':
        'google.cloud.pubsub.topic.v1.messagePublished',
    'datacontenttype':
        'application/json',
    'time':
        '2022-08-05T12:42:07.148Z'
}
data = {
    'message': {
        'data': 'aGVsbG8=',
        'messageId': '5320408004945103',
        'message_id': '5320408004945103',
        'publishTime': '2022-08-05T12:42:07.148Z',
        'publish_time': '2022-08-05T12:42:07.148Z'
    },
    'subscription':
        '''projects/python-functions-testing/subscriptions/
        eventarc-us-central1-hellofunctiononmessage-632859-sub-203'''
}


@on_message_published(
    topic='my-awesome-topic',
    memory=options.Memory.MB_512,
    region='europe-west2',
    ingress=options.USE_DEFAULT,
)
def on_message_published_function(event: CloudEventPublishedMessage):
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
    event = CloudEvent(attributes, data)
    headers, body = to_structured(event)

    res_call = client.post(
        '/on_message_published_function',
        data=body,
        headers=headers,
    )

    assert res_call.status_code == 200
