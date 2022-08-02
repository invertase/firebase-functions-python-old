"""Testing https functions are annotated with Firebase trigger metadata."""
import pytest
from firebase_functions import options
from firebase_functions import codegen
from firebase_functions.https import on_call, on_request
from firebase_functions.manifest import ManifestEndpoint


@on_call(
    memory=options.Memory.MB_256,
    region='europe-west1',
    timeout_sec=15,
    min_instances=6,
    max_instances=options.USE_DEFAULT,
    vpc=options.VpcOptions(
        connector='id',
        egress_settings=options.VpcEgressSettings.ALL_TRAFFIC,
    ),
    ingress=options.IngressSettings.ALLOW_INTERNAL_AND_GCLB,
    service_account='some-service-account',
    secrets=['secret-1', 'secret-2'],
)
def https_on_call_function():
  pass


@on_request(
    memory=options.Memory.MB_512,
    region='europe-west2',
    timeout_sec=123,
    min_instances=6,
    max_instances=12,
    vpc=options.VpcOptions(
        connector='id2',
        egress_settings=options.VpcEgressSettings.PRIVATE_RANGES_ONLY),
    ingress=options.IngressSettings.ALLOW_INTERNAL_ONLY,
    service_account='some-service-account',
    secrets=['secret-1', 'secret-2'],
)
def https_on_request_function():
  pass


@pytest.fixture(autouse=True, scope='module')
def reset_global_options():
  # Reset global options to default values before each test
  # in case other tests have changed them.
  options.set_global_options()


def test_https_on_call_function_endpoint():
  """Test https_on_call function has correct ManifestEndpoint configuration."""
  endpoint: ManifestEndpoint = https_on_call_function.__firebase_endpoint__
  fn = https_on_call_function
  assert isinstance(endpoint, ManifestEndpoint)
  assert endpoint.entryPoint == fn.__name__
  assert endpoint.region == 'europe-west1'
  assert endpoint.availableMemoryMb == 256
  assert endpoint.timeoutSeconds == 15
  assert endpoint.minInstances == 6
  assert isinstance(endpoint.maxInstances, options.Sentinel)
  vpc = endpoint.vpc
  assert isinstance(vpc, options.VpcOptions)
  assert vpc.connector == 'id'
  assert vpc.egress_settings == options.VpcEgressSettings.ALL_TRAFFIC
  assert endpoint.ingressSettings == options.IngressSettings.ALLOW_INTERNAL_AND_GCLB
  assert endpoint.serviceAccount == 'some-service-account'
  assert endpoint.secretEnvironmentVariables == ['secret-1', 'secret-2']
  assert endpoint.callableTrigger is not None
  assert endpoint.eventTrigger is None
  assert endpoint.httpsTrigger is None


def test_https_on_call_function_trigger_metadata():
  """Test https_on_call function trigger metadata is correctly attached."""
  trigger = https_on_call_function.__firebase_trigger__
  assert isinstance(trigger, dict)
  assert trigger['memory'] == options.Memory.MB_256
  assert trigger['region'] == 'europe-west1'


def test_https_on_call_function_trigger_exports():
  """Test https_on_call functions are detected in codegen exports."""
  exports = codegen.get_exports(__file__)
  assert 'https_on_call_function' in exports
  export = exports['https_on_call_function']
  assert export['memory'] == options.Memory.MB_256
  assert export['region'] == 'europe-west1'


def test_https_on_request_function_endpoint():
  """Test https_on_request function has
  correct ManifestEndpoint configuration."""
  endpoint: ManifestEndpoint = https_on_request_function.__firebase_endpoint__
  assert isinstance(endpoint, ManifestEndpoint)
  assert endpoint.entryPoint == https_on_request_function.__name__
  assert endpoint.region == 'europe-west2'
  assert endpoint.availableMemoryMb == 512
  assert endpoint.callableTrigger is None
  assert endpoint.httpsTrigger is not None


def test_https_on_request_function_trigger_metadata():
  """Test https_on_request function trigger metadata is correctly attached."""
  trigger = https_on_request_function.__firebase_trigger__
  assert isinstance(trigger, dict)
  assert trigger['memory'] == options.Memory.MB_512
  assert trigger['region'] == 'europe-west2'


def test_https_on_request_function_trigger_exports():
  """Test https_on_request functions are detected in codegen exports."""
  exports = codegen.get_exports(__file__)
  assert 'https_on_request_function' in exports
  export = exports['https_on_request_function']
  assert export['memory'] == options.Memory.MB_512
  assert export['region'] == 'europe-west2'
