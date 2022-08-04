"""
Test the functions that serve the admin and triggers.
"""

import dataclasses
import json
import logging
import os
import pytest
import yaml

from firebase_functions import options
from firebase_functions.https import Response, on_call, on_request
from firebase_functions.manifest import Manifest
from firebase_functions.serving import clean_nones_and_set_defult, serve_admin, serve_triggers

LOGGER = logging.getLogger(__name__)

# Environment variable used for pubsub topic name.
os.environ['GCLOUD_PROJECT'] = 'test-project'


@on_request(
    memory=options.Memory.MB_256,
    region='us-central-1',
    min_instances=1,
    max_instances=options.USE_DEFAULT,
    vpc=options.VpcOptions(
        connector='myConnector',
        egress_settings=options.VpcEgressSettings.ALL_TRAFFIC,
    ),
)
def http_request_function(req, res: Response):
    """
    Function gather HTTP request response
    """
    LOGGER.debug(req.data.decode('utf-8'))
    res.set_data('Hello World!')


@on_call(memory=options.Memory.MB_256)
def http_callable_function(req):
    """
    Function performs HTTP call
    """
    LOGGER.debug(req.data)
    return 'Hello World, again!'


triggers = {'http_request_function': http_request_function, 'http_callable_function': http_callable_function}


def test_admin_view_func():
    """
    Function tests admin view function response
    """
    with serve_admin(triggers=triggers).test_client() as client:
        res = client.get('/__/functions.yaml')
        assert res.status_code == 200, 'response failure, status_code != 200 '
        result = yaml.safe_load(res.get_data())
        assert result['endpoints']['httprequestfunction'][
                   'httpsTrigger'] is not None, 'Failure, httpsTrigger is none'
        assert result['endpoints']['httpcallablefunction'][
                   'callableTrigger'] is not None, 'Failure, callableTrigger is none'


def test_trigger_view_func():
    """
    Function tests for trigger view functions authentication, responses and requests
    """
    with serve_triggers(triggers=triggers).test_client() as client:
        res_request = client.post(
            '/http_request_function',
            data=json.dumps(dict(foo='bar')),
            content_type='application/json',
        )

        assert res_request.data.decode('utf-8') == 'Hello World!', 'Discrepancy found, response data != "Hello World!"'

        res_call = client.post(
            '/http_callable_function',
            data=json.dumps({'data': 'bar'}),
            content_type='application/json',
        )

        # Authenticated missing request
        assert json.loads(res_call.data.decode('utf-8')).get(
            'data') == 'Hello World, again!', 'Unauthenticated response or found request, response ' \
                                              'data != "Hello World!, again!"'

        res_call = client.post(
            '/http_callable_function',
            data=json.dumps({'data': 'bar'}),
            headers={'Authorization': 'bar'},
            content_type='application/json',
        )
        # Unauthenticated request
        assert json.loads(res_call.data.decode('utf-8')).get(
            'error')['message'] == 'Unauthenticated', 'Authenticated response, error message != "Unauthenticated"'


def test_quit_view_func():
    """
    Function tests for quit view function response
    """
    with serve_admin(triggers=triggers).test_client() as client:
        res = client.get('/__/quitquitquit')
        assert res.status_code == 200, 'response failure, status_code != 200'


def test_asdict_factory_cleanup():
    """
    Function tests fo factory cleanups as dictionaries
    """
    endpoints = {}

    for name, trigger in triggers.items():
        endpoints[name.replace('_', '').lower()] = trigger.__firebase_endpoint__

    manifest = dataclasses.asdict(
        Manifest(endpoints=endpoints),
        dict_factory=clean_nones_and_set_defult,
    )

    assert manifest['endpoints']['httprequestfunction']['maxInstances'] is None, 'Failure, maxInstances is none'
    with pytest.raises(KeyError):
        assert manifest['endpoints']['httpcallablefunction']['vpc'] is None, 'Failure, vpc is none'
