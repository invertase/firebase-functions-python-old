"""Tests serving unknown triggers"""
import json

import pytest
import yaml
from firebase_functions.manifest import ManifestEndpoint
from firebase_functions.serving import serve_admin, serve_triggers


def unknown_trigger(func):
    """Makes "unknown_trigger" decorator"""
    func.__firebase_endpoint__ = ManifestEndpoint(entryPoint=func.__name__)
    return func


@unknown_trigger
def unknown_function():
    """Makes 'unknown_function'"""


triggers: dict = {"unknown_function": unknown_function}


def test_spec_unknown():
    """Test unknown specification"""
    with serve_admin(triggers=triggers).test_client() as client:
        assert (
            "uknownfunction"
            not in yaml.safe_load(client.get("/__/functions.yaml").get_data())[
                "endpoints"
            ]
        ), "Failure, function is known"


def test_unknown_trigger_type():
    """Test unknown trigger type"""
    with pytest.raises(ValueError):
        with serve_triggers(triggers=triggers).test_client() as client:
            client.post(
                "/unknown_function",
                data=json.dumps({"data": "bar"}),
                headers={"Authorization": "bar"},
                content_type="application/json",
            )
