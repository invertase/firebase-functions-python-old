import functools
import os


def https(_func=None, *, min_instances=None, max_instances=None, memory_mb=None):
  metadata = {
    'apiVersion': 1,
    'trigger': {},
    'minInstances': min_instances,
    'maxInstances': max_instances,
    'availableMemoryMb': memory_mb,
  }

  def https_with_options(func):
    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__
    wrapper_func.firebase_metadata = metadata
    return wrapper_func

  if _func is None:
    return https_with_options

  return https_with_options(_func)


def pubsub(*, topic, min_instances=None):
  project = os.environ.get('GCLOUD_PROJECT')
  metadata = {
    'apiVersion': 1,
    'minInstances': min_instances,
    'trigger': {
      'eventType': 'google.pubsub.topic.publish',
      'eventFilters': [
        {
          'attribute': 'resource',
          'value': f'projects/{project}/topics/{topic}',
        },
      ]
    },
  }

  def pubsub_with_topic(func):
    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__
    wrapper_func.firebase_metadata = metadata
    return wrapper_func

  return pubsub_with_topic
