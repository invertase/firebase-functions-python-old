# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https, log


@https.on_call()
def testfunctiondefaultregion(request: https.CallableRequest):
  log.error(f"Hello from a function on call! {type(request.data).__name__}")
  return type(request.data).__name__


# @https.on_request()
# def hello_function_on_request(request: https.Request, response: https.Response):
#     response.status_code = 200
#     response.set_data('Hello World!')
