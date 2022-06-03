"""SAMPLE APP"""

from firebase_functions.log import debug
from firebase_functions.options import Memory, VpcEgressSettings, VpcOptions

from firebase_functions.https import Response, on_request, on_call, Request, CallableRequest


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
def http_request_function(req: Request, res: Response):

  debug('Debugging on_request')
  debug('Data: ' + str(req.data))

  res.status_code = 200

  return res


# # Sample of a HTTPS callable CF.
# @on_call(memory=Memory.MB_256, region='us-central-1')
# def http_callable_function(req: CallableRequest):

#   debug('Debugging on_call')
#   debug('Data: ' + str(req.data))

#   return 'Hello World'
