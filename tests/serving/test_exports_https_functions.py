"""Testing https functions are annotated with Firebase trigger metadata."""
import pytest
from firebase_functions import options
from firebase_functions import serving
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
    """Reset global options to default values before each test in case other tests have changed them."""
    options.set_global_options()


def test_https_on_call_function_endpoint():
    """Test https_on_call function has correct ManifestEndpoint configuration."""
    endpoint: ManifestEndpoint = https_on_call_function.__firebase_endpoint__
    assert isinstance(endpoint, ManifestEndpoint), 'Failure, endpoint is not an instance of ManifestEndpoint'
    assert endpoint.entryPoint == https_on_call_function.__name__, \
        'Failure, endpoint.entryPoint != https_on_call_function.__name__'
    assert endpoint.region == 'europe-west1', 'Failure, endpoint region does not mach  "europe-west1"'
    assert endpoint.availableMemoryMb == 256, 'Failure, endpoint available memory different from 256Mb'
    assert endpoint.timeoutSeconds == 15, 'Failure, endpoint timeout different from 15 seconds'
    assert endpoint.minInstances == 6, 'Failure, endpoint minimum instances different from 6'
    assert isinstance(endpoint.maxInstances, options.Sentinel), \
        'Failure, endpoint maximum instances is not an instance of Sentinel options'
    assert isinstance(endpoint.vpc, options.VpcOptions), 'Failure, endpoint vpc is not an instance of VpcOptions'
    assert endpoint.vpc.connector == 'id', 'Failure, endpoint vpc connector  different from "id"'
    assert endpoint.vpc.egress_settings == options.VpcEgressSettings.ALL_TRAFFIC
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
    """Test https_on_call functions are detected in exports."""
    exports = serving.get_exports(__file__)
    assert 'https_on_call_function' in exports
    assert exports['https_on_call_function']['memory'] == options.Memory.MB_256
    assert exports['https_on_call_function']['region'] == 'europe-west1'


def test_https_on_request_function_endpoint():
    """Test https_on_request function has correct ManifestEndpoint configuration."""
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
    """Test https_on_request functions are detected in exports."""
    exports = serving.get_exports(__file__)
    assert 'https_on_request_function' in exports
    assert exports['https_on_request_function']['memory'] == options.Memory.MB_512
    assert exports['https_on_request_function']['region'] == 'europe-west2'
