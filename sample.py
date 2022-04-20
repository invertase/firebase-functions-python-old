from firebase_functions import pubsub

@pubsub.https(memory_mb=256)
def http_function(request):
  return 'Hello world'

@pubsub.pubsub(
  topic='news',
  min_instances=1,
)
def pubsub_function(event, context):
  print('pubsub:', event, context)
