"""Test the functions that serve the admin and triggers."""

import dataclasses
import json
import os
import pytest
import yaml

from firebase_functions import options
from firebase_functions.https import Response, on_call, on_request
from firebase_functions.manifest import Manifest
from firebase_functions.serving import (
    clean_nones_and_set_defult,
    serve_admin,
    serve_triggers,
)

# Environment variable used for pubsub topic name.
os.environ["GCLOUD_PROJECT"] = "test-project"


@on_request(
    memory=options.Memory.MB_256,
    region="us-central-1",
    min_instances=1,
    max_instances=options.USE_DEFAULT,
    vpc=options.VpcOptions(
        connector="myConnector",
        egress_settings=options.VpcEgressSettings.ALL_TRAFFIC,
    ),
)
def http_request_function(_, res: Response):
    """Gather HTTP request response"""
    res.set_data("Hello World!")


@on_call(memory=options.Memory.MB_256)
def http_callable_function(_):
    return "Hello World, again!"


triggers = {}

triggers["http_request_function"] = http_request_function
triggers["http_callable_function"] = http_callable_function


def test_admin_view_func():
    """Tests admin view function response"""
    with serve_admin(triggers=triggers).test_client() as client:
        res = client.get("/__/functions.yaml")
        assert res.status_code == 200, "response failure, status_code != 200 "
        assert (yaml.safe_load(
            res.get_data())["endpoints"]["httprequestfunction"]["httpsTrigger"]
                is not None), "Failure, httpsTrigger is none"
        assert (yaml.safe_load(res.get_data())["endpoints"]
                ["httpcallablefunction"]["callableTrigger"]
                is not None), "Failure, callableTrigger is none"


def test_trigger_view_func():
    """Tests for trigger view functions authentication, responses and requests"""
    with serve_triggers(triggers=triggers).test_client() as client:
        res_request = client.post(
            "/http_request_function",
            data=json.dumps(dict(foo="bar")),
            content_type="application/json",
        )

        assert (res_request.data.decode("utf-8") == "Hello World!"
               ), "Discrepancy found, response data != 'Hello World!'"

        res_call = client.post(
            "/http_callable_function",
            data=json.dumps({"data": "bar"}),
            content_type="application/json",
        )

        # Authenticated missing request
        assert (
            json.loads(res_call.data.decode("utf-8")).get(
                "data") == "Hello World, again!"
        ), "Unauthenticated response or found request, response data != 'Hello World!, again!'"

        res_call = client.post(
            "/http_callable_function",
            data=json.dumps({"data": "bar"}),
            headers={"Authorization": "bar"},
            content_type="application/json",
        )
        # Unauthenticated request
        assert (json.loads(res_call.data.decode("utf-8")).get(
            "error")["message"] == "Unauthenticated"
               ), "Authenticated response, error message != 'Unauthenticated'"


def test_quit_view_func():
    """Tests for quit view function response"""
    with serve_admin(triggers=triggers).test_client() as client:
        assert (client.get("/__/quitquitquit").status_code == 200
               ), "response failure, status_code != 200"


def test_asdict_factory_cleanup():
    """Tests factory cleanups as dictionaries"""
    endpoints: dict = {
        name.replace("_", "").lower(): trigger.__firebase_endpoint__
        for name, trigger in triggers.items()
    }

    manifest = dataclasses.asdict(
        Manifest(endpoints=endpoints),
        dict_factory=clean_nones_and_set_defult,
    )

    assert (manifest["endpoints"]["httprequestfunction"]["maxInstances"] is
            None), "Failure, maxInstances is not none"
    with pytest.raises(KeyError):
        assert (manifest["endpoints"]["httpcallablefunction"]["vpc"] is
                None), "Failure, vpc is not none"
