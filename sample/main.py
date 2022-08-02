'''SAMPLE APP'''

from firebase_functions.log import debug
from firebase_functions import options
from firebase_functions.https import on_request, on_call, Response, Request, CallableRequest
from firebase_functions.pubsub import on_message_published, CloudEventMessage

options.set_global_options(max_instances=3)


# Sample of a HTTPS request CF.
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
def http_request_function(req: Request, res: Response):

  debug('Debugging on_request')
  debug('Data: ' + str(req.data))

  res.set_data('hi')


# Sample of a HTTPS callable CF.
@on_call(
    memory=options.Memory.MB_256,
    region='us-central-1',
)
def httpcallablefunction(req: CallableRequest):

  debug('Debugging on_call')
  debug(f'Data: {req.data}')

  return 'Hello world!'


# Sample of a Pub/Sub event CF.
# FIXME region should a list in yaml
@on_message_published(
    topic='uid',
    memory=options.Memory.MB_256,
    region='europe-west-3',
)
def pubsub_function(message: CloudEventMessage):

  debug('Debugging pubsub_function')
  debug(f'Data: {message}')

  return ''
