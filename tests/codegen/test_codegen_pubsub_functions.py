"""Testing pub/sub functions are annotated with Firebase trigger metadata."""

import os
from sys import stdout
import pytest
from firebase_functions import options
from firebase_functions import codegen
from firebase_functions.pubsub import on_message_published
from firebase_functions.manifest import ManifestEndpoint

os.environ['GCLOUD_PROJECT'] = "test-project"


@on_message_published(
    topic='my-awesome-topic',
    memory=options.Memory.MB_512,
    region='europe-west2',
    ingress=options.USE_DEFAULT,
)
def on_message_published_function():
  pass


@pytest.fixture(autouse=True, scope='module')
def reset_global_options():
  # Reset global options to default values before each test
  # in case other tests have changed them.
  options.set_global_options()


def test_on_message_published_function_endpoint():
  """Test on_message_published function has
  correct ManifestEndpoint configuration."""

  endpoint: ManifestEndpoint = on_message_published_function.__firebase_endpoint__
  filters = endpoint.eventTrigger['eventFilters']
  assert isinstance(endpoint, ManifestEndpoint)
  assert filters['topic'] == 'projects/test-project/topics/my-awesome-topic'
  assert endpoint.entryPoint == on_message_published_function.__name__
  assert endpoint.region == 'europe-west2'
  assert endpoint.availableMemoryMb == 512
  assert isinstance(endpoint.ingressSettings, options.Sentinel)
  assert endpoint.eventTrigger is not None
  assert endpoint.callableTrigger is None
  assert endpoint.httpsTrigger is None


def test_on_message_published_function_trigger_metadata():
  """Test on_message_published function trigger metadata is correctly attached."""
  trigger = on_message_published_function.__firebase_trigger__
  assert isinstance(trigger, dict)
  assert trigger['memory'] == options.Memory.MB_512
  assert trigger['region'] == 'europe-west2'


def test_on_message_published_function_trigger_exports():
  """Test on_message_published functions are detected in codegen exports."""
  exports = codegen.get_exports(__file__)
  assert 'on_message_published_function' in exports
  export = exports['on_message_published_function']
  assert export['memory'] == options.Memory.MB_512
  assert export['region'] == 'europe-west2'
