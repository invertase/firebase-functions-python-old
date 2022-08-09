"""
Unit tests for Pub/Sub triggers.
"""

import logging
import yaml
import pytest

import datetime as dt

from firebase_functions import options
from firebase_functions.pubsub import Message, on_message_published, CloudEvent, MessagePublishedData
from firebase_functions.serving import serve_admin, serve_triggers

import cloudevents.http

LOGGER = logging.getLogger(__name__)
attributes = {
    "specversion": "1.0",
    "id": "5320408004945103",
    "source": "pubsub.googleapis.com/projects/"
              "python-functions-testing/topics/test-topic",
    "type": "google.cloud.pubsub.topic.v1.messagePublished",
    "datacontenttype": "application/json",
    "time": "2022-08-05T12:42:07.148Z"
}
data_1 = {
    "message": {
        "data": "eyJkYXRhIjogIkhlbGxvIHdvcmxkIn0=",
        "messageId": "5320408004945103",
        "message_id": "5320408004945103",
        "publishTime": "2022-08-05T12:42:07.148Z",
        "publish_time": "2022-08-05T12:42:07.148Z"
    },
    "subscription": "projects/python-functions-testing/subscriptions/"
                    "eventarc-us-central1-hellofunctiononmessage-632859-sub-203"
}

data_2 = {
    "message": {
        "messageId": "5320408004945103",
        "message_id": "5320408004945103",
        "publishTime": "2022-08-05T12:42:07.148Z",
        "publish_time": "2022-08-05T12:42:07.148Z",
        "attributes": "{'foo': 'bar'}",
        "orderingKey": "123"
    },
    "subscription": "projects/python-functions-testing/subscriptions/"
                    "eventarc-us-central1-hellofunctiononmessage-632859-sub-203"
}

data_3 = {
    "message": {
        "data": "aGVsbG8=",
        "messageId": "5320408004945103",
        "message_id": "5320408004945103",
        "publishTime": "2022-08-05T12:42:07.148Z",
        "publish_time": "2022-08-05T12:42:07.148Z",
    },
    "subscription": "projects/python-functions-testing/subscriptions/"
                    "eventarc-us-central1-hellofunctiononmessage-632859-sub-203"
}


@on_message_published(
    topic="my-awesome-topic",
    memory=options.Memory.MB_512,
    region="europe-west2",
    ingress=options.USE_DEFAULT,
)
def on_message_published_function(event: CloudEvent[MessagePublishedData]):
    assert isinstance(event.time, dt.datetime), \
      "Event time is a datetime object"
    assert event.time.date() == dt.date(2022, 8, 5), \
      "Event date matches expected date"
    assert isinstance(event.data.message, Message), \
      "Event data is a Message object"
    assert isinstance(event.data.message.json, dict), \
      "Event data is a Message object"
    assert event.data.message.json == {"data": "Hello world"}, \
      "Message data is a dict"

    message_as_dict = event.data.message.asdict()
    assert message_as_dict["message_id"] == "5320408004945103", \
      "Message asdict() has same values as original data"
    assert not hasattr(message_as_dict, "attributes"), \
      "Message does not have attributes"
    assert not hasattr(message_as_dict, "ordering_key") , \
      "Message does not have ordering key"


@on_message_published(
    topic="my-awesome-topic",
    memory=options.Memory.MB_512,
    region="europe-west2",
    ingress=options.USE_DEFAULT,
)
def on_message_published_function_no_message_data(
        event: CloudEvent[MessagePublishedData]):
    assert event.data.message.json is None, \
      "Message data is None when no data is passed in the event"

    message_as_dict = event.data.message.asdict()

    assert "attributes" in message_as_dict, \
      "Message has attributes"
    assert "ordering_key" in message_as_dict, \
      "Message has ordering key"


@on_message_published(
    topic="my-awesome-topic",
    memory=options.Memory.MB_512,
    region="europe-west2",
    ingress=options.USE_DEFAULT,
)
def on_message_published_function_data_is_not_parsable(
        event: CloudEvent[MessagePublishedData]):
    with pytest.raises(Exception):
        assert isinstance(event.data.message.json, dict), \
          "The message data is not parsable to json"


triggers = {}
triggers["on_message_published_function"] = on_message_published_function
triggers["on_message_published_function_no_message_data"] = \
      on_message_published_function_no_message_data
triggers["on_message_published_function_data_is_not_parsable"] = \
      on_message_published_function_data_is_not_parsable


def test_sepc_pubsub():
    """Tests for pubsub specification"""
    with serve_admin(triggers=triggers).test_client() as client:
        res = client.get("/__/functions.yaml")
        assert res.status_code == 200, "Failure, response status code !=200"
        assert (yaml.safe_load(res.get_data())["endpoints"]
                ["onmessagepublishedfunction"]["eventTrigger"]
                is not None), "Failure, eventTrigger is none "


def test_trigger_pubsub():

    with serve_triggers(triggers=triggers).test_client() as client:
        event = cloudevents.http.CloudEvent(attributes, data_1)
        headers, body = cloudevents.http.to_structured(event)

        res_call = client.post(
            "/on_message_published_function",
            data=body,
            headers=headers,
        )

        assert res_call.status_code == 200, \
          "Response status code is 200"

        event = cloudevents.http.CloudEvent(attributes, data_2)
        headers, body = cloudevents.http.to_structured(event)

        res_call = client.post(
            "/on_message_published_function_no_message_data",
            data=body,
            headers=headers,
        )


def test_trigger_pubsub_no_data():

    with serve_triggers(triggers=triggers).test_client() as client:
        event = cloudevents.http.CloudEvent(attributes, data_2)
        headers, body = cloudevents.http.to_structured(event)

        res_call = client.post(
            "/on_message_published_function_no_message_data",
            data=body,
            headers=headers,
        )

        assert res_call.status_code == 200, \
          "Response status code is 200"


def test_trigger_pubsub_data_is_not_parsable():

    with serve_triggers(triggers=triggers).test_client() as client:
        event = cloudevents.http.CloudEvent(attributes, data_3)
        headers, body = cloudevents.http.to_structured(event)

        res_call = client.post(
            "/on_message_published_function_data_is_not_parsable",
            data=body,
            headers=headers,
        )

        assert res_call.status_code == 200, \
          "Response status code is 200"
