"""Test RTDB(Real Time Data Base) functions"""
import datetime as dt

import cloudevents.http
import yaml

from firebase_functions import options, params
from firebase_functions.db import (
    DbData,
    on_value_written,
    on_value_updated,
    on_value_created,
    on_value_deleted,
    Event,
    Change,
    PublishedDbData,
)

from firebase_functions.serving import serve_admin

instance = params.StringParam(
    "RTDB_INSTANCE",
    label="Which database instance to listen to",
    default=params.DATABASE_INSTANCE,
)

attributes = {
    "specversion": "1.0",
    "id": "5320408004945103",
    "source": "type.googleapis.com/google.events.firebase.database.v1.ReferenceEventData",
    "type": "google.firebase.database.ref.v1.created",
    "datacontenttype": "application/json",
    "time": "2022-08-05T12:42:07.148Z",
}
raw_db_event = {
    "data": {
        "type": "google.firebase.database.ref.v1.created",
        "data": {},
        "delta": {},
        "publishTime": "2022-08-05T12:42:07.148Z",
        "publish_time": "2022-08-05T12:42:07.148Z",
    },
    "firebase_database_host": "firebaseio.com",
    "instance": "instance",
    "reference": "foo/bar",
    "location": "us-central1",
    "params": {"type": "type"},
}


@on_value_written(
    reference="foo/bar",
)
def on_value_written_function(event: Event[Change]):
    """Test on data published function"""
    assert isinstance(event.time, dt.datetime), "Event time is not a datetime object"
    assert event.time.date() == dt.date(
        2022, 8, 5
    ), "Event date not matches expected date"
    assert isinstance(event.data, DbData), "Event data is not a json object"
    assert isinstance(event.data.json, dict), "Event data is not a json object"
    assert event.data.json == {"data": "Hello world"}, "Data is not a dict"

    data_as_dict = event.data.as_dict()
    assert (
        data_as_dict["message_id"] == "5320408004945103a"
    ), "Message as_dict() has same values as original data"
    assert not hasattr(data_as_dict, "attributes"), "Message does not have attributes"
    assert not hasattr(
        data_as_dict, "ordering_key"
    ), "Message does not have ordering key"


@on_value_updated(reference="users/{uid}")
def function_on_value_updated():
    """function_on_value_updated"""


@on_value_created(
    reference="foo/bar",
    instance=instance,
    memory=options.Memory.MB_512,
    region="europe-west2",
    ingress=options.USE_DEFAULT,
)
def on_value_created_function(event: Event[PublishedDbData]):
    """function_on_value_created"""
    assert isinstance(event.time, dt.datetime), "Event time is not a datetime object"
    assert event.time.date() == dt.date(
        2022, 8, 5
    ), "Event date not matches expected date"
    assert isinstance(event.data, DbData), "Event data is not a json object"
    assert isinstance(event.data.json, dict), "Event data is not a json object"
    assert event.data.json == {"data": "Hello world"}, "Data is not a dict"

    data_as_dict = event.data.as_dict()
    assert (
        data_as_dict["message_id"] == "5320408004945103a"
    ), "Message as_dict() has same values as original data"
    assert not hasattr(data_as_dict, "attributes"), "Message does not have attributes"
    assert not hasattr(
        data_as_dict, "ordering_key"
    ), "Message does not have ordering key"


@on_value_deleted(reference="users/{uid}")
def function_on_value_deleted():
    """function_on_value_deleted"""


triggers = {
    "on_value_written_function": on_value_written_function,
    "on_value_created_function": on_value_created_function,
}


def test_db_spec():
    """Test database specs"""
    with serve_admin(triggers=triggers).test_client() as client:
        for test_func in triggers.keys():
            assert (
                client.get("/__/functions.yaml").status_code == 200
            ), "Failure, response status code !=200"
            assert (
                yaml.safe_load(client.get("/__/functions.yaml").get_data())
                ["endpoints"][test_func.replace("_", "")]["eventTrigger"]
                is not None
            ), "Failure, eventTrigger is none "
