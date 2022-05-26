# def pubsub(*, topic, min_instances=None):
#   project = os.environ.get('GCLOUD_PROJECT')
#   metadata = {
#     'apiVersion': 1,
#     'minInstances': min_instances,
#     'trigger': {
#       'eventType': 'google.pubsub.topic.publish',
#       'eventFilters': {
#         'resource': f'projects/{project}/topics/{topic}',
#       }
#     },
#   }

#   def pubsub_with_topic(func):
#     @functools.wraps(func)
#     def wrapper_func(*args, **kwargs):
#       return func(*args, **kwargs)

#     metadata['id'] = func.__name__
#     wrapper_func.firebase_metadata = metadata
#     return wrapper_func

#   return pubsub_with_topic
