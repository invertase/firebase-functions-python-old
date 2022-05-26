from firebase_functions import https
from firebase_functions.options import Memory


@https.on_request(memory=Memory.MB_256, region='us-central-1')
def http_function():
  return 'Hello world'


# @pubsub.https()
# def pubsub_function(event, context):
#   print('pubsub:', event, context)
