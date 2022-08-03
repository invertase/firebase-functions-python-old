'''
Test the functions that serve the admin and triggers.
'''

import json
import logging
import yaml
from firebase_functions import options
from firebase_functions.https import Response, on_call, on_request
from firebase_functions.serving import serve_admin, serve_triggers

LOGGER = logging.getLogger(__name__)


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
  LOGGER.debug(req.data.decode('utf-8'))
  res.set_data('Hello World!')


@on_call(memory=options.Memory.MB_256)
def http_callable_function(req):
  LOGGER.debug(req.data)
  return 'Hello World, again!'


triggers = {}

triggers['http_request_function'] = http_request_function
triggers['http_callable_function'] = http_callable_function


def test_admin_view_func():
  with serve_admin(triggers=triggers).test_client() as client:
    res = client.get('/__/functions.yaml')
    assert res.status_code == 200
    result = yaml.safe_load(res.get_data())
    assert result['endpoints']['httprequestfunction']['httpsTrigger'] == {}
    assert result['endpoints']['httpcallablefunction']['callableTrigger'] == {}


def test_trigger_view_func():
  with serve_triggers(triggers=triggers).test_client() as client:
    res_request = client.post(
        '/http_request_function',
        data=json.dumps(dict(foo='bar')),
        content_type='application/json',
    )

    res_call = client.post(
        '/http_callable_function',
        data=json.dumps({'data': 'bar'}),
        headers={'Authorization': 'bar'},
        content_type='application/json',
    )

    assert res_request.data.decode('utf-8') == 'Hello World!'
    assert json.loads(res_call.data.decode('utf-8')).get(
        'error')['message'] == 'Unauthenticated'
