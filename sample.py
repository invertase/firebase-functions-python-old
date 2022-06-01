"""SAMPLE APP"""

from firebase_functions.log import debug
from firebase_functions.request import Response, Request, on_request
from firebase_functions.call import on_call
from firebase_functions.options import Memory
from firebase_functions.call import CallableRequest


# Sample of a HTTPS request CF.
@on_request(memory=Memory.MB_256, region='us-central-1')
def http_request_function(req: Request) -> None:

  debug('Debugging on_request')
  debug('Data: ' + str(req.data))

  return 'Hello World'


# Sample of a HTTPS callable CF.
@on_call(memory=Memory.MB_256, region='us-central-1')
def http_callable_function(req: CallableRequest):

  debug('Debugging on_call')
  debug('Data: ' + str(req.data))

  return 'Hello World'
