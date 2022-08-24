"""Test RTDB(Real Time Data Base) functions"""
import datetime as dt

from firebase_functions import options
from firebase_functions.db import (
    DbData,
    on_value_written,
    on_value_updated,
    on_value_created,
    on_value_deleted,
    Event,
    Change,
)

from firebase_functions.serving import serve_admin


@on_value_written(
    reference="users/{uid}",
    region="europe-west2",
    ingress=options.USE_DEFAULT,
)
def on_value_written_function(event: Event[Change]):
    """Test on data published function"""

    assert isinstance(event.time, dt.datetime), "Event time is a datetime object"
    assert event.time.date() == dt.date(2022, 8, 5), "Event date matches expected date"
    assert isinstance(event.data, DbData), "Event data is a Message object"
    assert isinstance(event.data.json, dict), "Event data is a Message object"
    assert event.data.json == {"data": "Hello world"}, "Message data is a dict"

    message_as_dict = event.data.as_dict()
    assert (
            message_as_dict["message_id"] == "5320408004945103"
    ), "Message as_dict() has same values as original data"
    assert not hasattr(
        message_as_dict, "attributes"
    ), "Message does not have attributes"
    assert not hasattr(
        message_as_dict, "ordering_key"
    ), "Message does not have ordering key"
    return event


@on_value_updated(reference="users/{uid}")
def function_on_value_updated():
    """function_on_value_updated"""


@on_value_created(reference="users/{uid}")
def function_on_value_created():
    """function_on_value_created"""


@on_value_deleted(reference="users/{uid}")
def function_on_value_deleted():
    """function_on_value_deleted"""


triggers = {"on_value_written_function": on_value_written_function}


def test_on_value_written():
    """Test written value"""
    with serve_admin(triggers=triggers).test_client() as client:
        res = client.get("/__/functions.yaml")
        assert res.status_code == 200, "Failure, response status code !=200"
