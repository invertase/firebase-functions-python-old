"""SAMPLE APP"""

from firebase_functions.log import debug
from firebase_functions.options import Memory, VpcEgressSettings, VpcOptions

from firebase_functions.https import on_request, on_call, Request, CallableRequest
from firebase_functions.pubsub import CloudEventMessage, on_message_published


# Sample of a HTTPS request CF.
@on_request(
    memory=Memory.MB_256,
    region='us-central-1',
    max_instances=3,
    min_instances=1,
    vpc=VpcOptions(
        connector='myConnector',
        egress_settings=VpcEgressSettings.ALL_TRAFFIC,
    ),
)
def http_request_function(req: Request):

  debug('Debugging on_request')
  debug('Data: ' + str(req.data))

  return 'hi'


# Sample of a HTTPS callable CF.
@on_call(memory=Memory.MB_256, region='us-central-1')
def http_callable_function(req: CallableRequest):

  debug('Debugging on_call')
  debug(f'Data: {req.data}')

  return 'Hello world!'


# Sample of a Pub/Sub event CF.
# FIXME region should a list in yaml
@on_message_published(topic='uid', memory=Memory.MB_256, region='europe-west-3')
def pubsub_function(message: CloudEventMessage):

  debug('Debugging pubsub_function')
  debug(f'Data: {message}')

  return ''
