import logging
import yaml
import datetime as dt

from firebase_functions import options
from firebase_functions.pubsub import Message, on_message_published, CloudEvent, MessagePublishedData
from firebase_functions.serving import serve_admin, serve_triggers

import cloudevents.http

LOGGER = logging.getLogger(__name__)
attributes = {
    'specversion': '1.0',
    'id': '5320408004945103',
    'source': 'pubsub.googleapis.com/projects/'
              'python-functions-testing/topics/test-topic',
    'type': 'google.cloud.pubsub.topic.v1.messagePublished',
    'datacontenttype': 'application/json',
    'time': '2022-08-05T12:42:07.148Z'
}
data = {
    'message': {
        'data': 'eyJkYXRhIjogIkhlbGxvIHdvcmxkIn0=',
        'messageId': '5320408004945103',
        'message_id': '5320408004945103',
        'publishTime': '2022-08-05T12:42:07.148Z',
        'publish_time': '2022-08-05T12:42:07.148Z'
    },
    'subscription': 'projects/python-functions-testing/subscriptions/'
                    'eventarc-us-central1-hellofunctiononmessage-632859-sub-203'
}


@on_message_published(
    topic='my-awesome-topic',
    memory=options.Memory.MB_512,
    region='europe-west2',
    ingress=options.USE_DEFAULT,
)
def on_message_published_function(event: CloudEvent[MessagePublishedData]):
  assert isinstance(event.time, dt.datetime), \
    'Event time is a datetime object'
  assert event.time.date() == dt.date(2022, 8, 5), \
    'Event date matches expected date'
  assert isinstance(event.data.message, Message), \
    'Event data is a Message object'
  assert event.data.message.json == {'data': 'Hello world'}, \
    'Message data is a dict'


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
    event = cloudevents.http.CloudEvent(attributes, data)
    headers, body = cloudevents.http.to_structured(event)

    res_call = client.post(
        '/on_message_published_function',
        data=body,
        headers=headers,
    )

    assert res_call.status_code == 200, \
      'Response status code is 200'
