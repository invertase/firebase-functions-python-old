"""Testing pub/sub functions are annotated with Firebase trigger metadata."""

import os
import pytest
from firebase_functions import options
from firebase_functions import codegen
from firebase_functions.pubsub import on_message_published
from firebase_functions.manifest import ManifestEndpoint

# Environment variable used for pubsub topic name.
os.environ['GCLOUD_PROJECT'] = 'test-project'


@on_message_published(
    topic='my-awesome-topic',
    memory=options.Memory.MB_512,
    region='europe-west2',
    ingress=options.USE_DEFAULT,
)
def on_message_published_function():
  pass


@on_message_published(
    topic='my-awesome-topic',
    memory=options.Memory.MB_512,
    region='europe-west2',
    timeout_sec=123,
    min_instances=6,
    max_instances=12,
    vpc=options.VpcOptions(
        connector='id',
        egress_settings=options.VpcEgressSettings.PRIVATE_RANGES_ONLY),
    ingress=options.IngressSettings.ALLOW_INTERNAL_ONLY,
    service_account='some-service-account',
    secrets=['secret-1', 'secret-2'],
)
def on_message_published_function_all_options():
  pass


@pytest.fixture(autouse=True, scope='module')
def reset_global_options():
  # Reset global options to default values before each test
  # in case other tests have changed them.
  options.set_global_options()


def test_on_message_published_function_endpoint_has_all_options():
  """Test on_message_published function has
  all options passed through to ManifestEndpoint configuration."""
  fn = on_message_published_function_all_options
  endpoint: ManifestEndpoint = fn.__firebase_endpoint__
  filters = endpoint.eventTrigger['eventFilters']
  assert isinstance(endpoint, ManifestEndpoint)
  assert filters['topic'] == 'projects/test-project/topics/my-awesome-topic'
  assert endpoint.entryPoint == fn.__name__
  assert endpoint.region == 'europe-west2'
  assert endpoint.availableMemoryMb == 512
  assert endpoint.timeoutSeconds == 123
  assert endpoint.minInstances == 6
  assert endpoint.maxInstances == 12
  vpc = endpoint.vpc
  assert isinstance(vpc, options.VpcOptions)
  assert vpc.connector == 'id'
  assert vpc.egress_settings == options.VpcEgressSettings.PRIVATE_RANGES_ONLY
  assert endpoint.ingressSettings == options.IngressSettings.ALLOW_INTERNAL_ONLY
  assert endpoint.serviceAccount == 'some-service-account'
  assert endpoint.secretEnvironmentVariables == ['secret-1', 'secret-2']
  assert endpoint.eventTrigger is not None
  assert endpoint.callableTrigger is None
  assert endpoint.httpsTrigger is None


def test_on_message_published_function_endpoint():
  """Test on_message_published function has
  correct ManifestEndpoint configuration."""
  fn = on_message_published_function
  endpoint: ManifestEndpoint = fn.__firebase_endpoint__
  filters = endpoint.eventTrigger['eventFilters']
  assert isinstance(endpoint, ManifestEndpoint)
  assert filters['topic'] == 'projects/test-project/topics/my-awesome-topic'
  assert endpoint.entryPoint == fn.__name__
  assert endpoint.region == 'europe-west2'
  assert endpoint.availableMemoryMb == 512
  assert isinstance(endpoint.ingressSettings, options.Sentinel)
  assert endpoint.eventTrigger is not None
  assert endpoint.callableTrigger is None
  assert endpoint.httpsTrigger is None


def test_on_message_published_function_trigger_metadata():
  """Test on_message_published function trigger metadata
  is correctly attached."""
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
