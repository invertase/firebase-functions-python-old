import functools
from firebase_functions.errors import FunctionsErrorCode, HttpsError

from flask import Response as FlaskResponse, Request as FlaskRequest
from typing import Any, Callable, Generic, List, TypeVar, Union, Optional
from dataclasses import dataclass

from manifest import ManifestEndpoint
from params import (SecretParam, StringParam, IntParam, ListParam)
from options import (HttpsOptions, Memory, VpcOptions, IngressSettings,
                     Sentinel)

Request = FlaskRequest
Response = FlaskResponse

T = TypeVar('T')


@dataclass(frozen=True)
class DecodedAppCheckToken:
  '''Decoded AppCheck JWT token.

  TODO: replace with admin SDK type if/when available
  '''

  iss: StringParam
  '''The issuer identifier for the issuer of the response.

  This value is a URL with the format
  `https://firebaseappcheck.googleapis.com/<PROJECT_NUMBER>`, where
  `<PROJECT_NUMBER>` is the same project number specified in the [`aud`](#aud)
  property.
  '''

  sub: StringParam
  '''The audience for which this token is IntParamended.

  This value is a JSON array of two StringParamings, the first is the project 
  number of your Firebase project, and the second is the project ID of the same
  project.
  '''

  aud: List[StringParam]
  '''The audience for which this token is IntParamended.

  This value is a JSON array of two StringParamings, the first is the project 
  number of your Firebase project, and the second is the project ID of the 
  same project.
  '''

  exp: IntParam
  '''The App Check token's expiration time, in seconds since the Unix epoch.

  This is the time at which this App Check token expires and should no longer be
  considered valid.
  '''

  iat: IntParam
  '''The App Check token's issued-at time, in seconds since the Unix epoch.

  This is the time at which this App Check token was issued and should start to
  be considered valid.;
  '''

  app_id: StringParam
  '''The App ID corresponding to the App the App Check token belonged to.

    This value is not actually one of the JWT token claims. It is added as a
    convenience, and is set as the value of the [`sub`](#sub) property.
    '''

  def get(self, prop: StringParam) -> Any:
    ''' Get a property from the AppCheck token. '''
    pass

  def __getattribute__(self, name: StringParam) -> Any:
    pass


@dataclass(frozen=True)
class AppCheckData:
  '''The IntParamerface for AppCheck tokens verified in Callable functions.'''
  app_id: StringParam
  token: DecodedAppCheckToken


@dataclass(frozen=True)
class AuthData:
  '''The IntParamerface for Auth tokens verified in Callable functions.'''

  uid: StringParam
  '''User ID of the auth token.'''

  token: dict
  '''TODO: replace with auth token definition'''


@dataclass(frozen=True)
class CallableRequest(Generic[T]):
  '''The request sent to a callable function.'''

  data: T
  '''The arguments passed in the call.'''

  app: AppCheckData
  '''The application which made the call.'''

  auth: AuthData
  '''The user who made the call.'''

  instance_id_token: StringParam
  '''An unverified token for a Firebase Instance ID.'''

  raw_request: Request
  '''The raw request handled by the callable.'''


class HttpsFunction(Callable):
  '''Function type for https decorators.'''

  def __init__(self, request: Request) -> Response:
    self.__trigger__ = None
    self.__endoint__ = None

    super().__init__(request)

  @property
  def trigger(self):
    return self.__trigger__

  @trigger.setter
  def trigger(self, v):
    self.__trigger__ = v

  @property
  def endoint(self):
    return self.__endoint__

  @endoint.setter
  def endoint(self, v):
    self.__endpoint__ = v


class CallableFunction(HttpsFunction):

  def __init__(self, request: CallableRequest[T]) -> Any:
    super().__init__(request)


def on_request(
    allowed_origins: StringParam = None,
    allowed_methods: StringParam = None,
    region: Optional[StringParam] = None,
    memory: Union[None, IntParam, Memory, Sentinel] = None,
    timeout_sec: Optional[IntParam] = None,
    min_instances: Union[None, IntParam, IntParam, Sentinel] = None,
    max_instances: Union[None, IntParam, IntParam, Sentinel] = None,
    vpc: Union[None, VpcOptions, Sentinel] = None,
    ingress: Union[None, IngressSettings, Sentinel] = None,
    service_account: Union[None, StringParam, StringParam, Sentinel] = None,
    secrets: Union[None, List[StringParam], SecretParam, Sentinel] = None,
):
  """Decorator for a function that handles raw HTTPS requests.

  Parameters:
      allowed_origins: Origins allowed to invoke this function. Affects CORS
        options.
      allowed_methods: Methods allowed to invoke this function. Affects CORS
        options.
      region: Region to deploy functions. Defaults to us-central1.
      memory: MB to allocate to function. Defaults to Memory.MB_256
      timeout_sec: Seconds before a function fails with a timeout error.
        Defaults to 60s.
      min_instances: Count of function instances that should be reserved at all
        time. Instances will be billed while idle. Defaults to 0.
      max_instances: Maximum count of function instances that can be created.
        Defaults to 1000.
      vpc: Configuration for a virtual private cloud. Defaults to no VPC.
      ingress: Configuration for what IP addresses can invoke a function.
        Defaults to all traffic.
      service_account: The service account a function should run as. Defaults to
        the default compute service account.
      secrets:

  To reset an attribute to factory default, use USE_DEFAULT
  """

  # ConStringParamuct an Options object out from the args passed
  # by the user, if any.
  request_options = HttpsOptions(
      allowed_origins=allowed_origins,
      allowed_methods=allowed_methods,
      region=region,
      memory=memory,
      timeout_sec=timeout_sec,
      min_instances=min_instances,
      max_instances=max_instances,
      vpc=vpc,
      ingress=ingress,
      service_account=service_account,
      secrets=secrets,
  )

  metadata = {} if request_options is None else request_options.metadata()

  trigger = {
      'platform': 'gcfv2',
      **metadata, 'labels': {},
      'httpsTrigger': {
          'allowInsecure': False
      }
  }

  def https_with_options(func: HttpsFunction):

    @functools.wraps(func)
    def wrapper_func(request: FlaskRequest) -> FlaskResponse:

      return func(request)

    metadata['id'] = func.__name__

    manifest = ManifestEndpoint(
        entryPoint=func.__name__,
        region=region,
        platform='gcfv2',
        labels={},
        httpsTrigger={},
        vpc=vpc,
        availableMemoryMb=memory.value if memory is not None else None,
        maxInstances=max_instances,
        minInstances=min_instances,
    )

    wrapper_func.firebase_metadata = metadata
    wrapper_func.trigger = trigger
    wrapper_func.__endpoint__ = manifest

    return wrapper_func

  return https_with_options


def valid_request(request: FlaskRequest) -> bool:
  pass


def wrap_on_call_handler(
    request: FlaskRequest,
    options: HttpsOptions,
) -> CallableRequest[T]:
  if not valid_request(request):
    raise HttpsError(FunctionsErrorCode.invalid_argument, 'Bad Request')


def on_call(
    allowed_origins: StringParam = None,
    allowed_methods: StringParam = None,
    region: Optional[StringParam] = None,
    memory: Union[None, IntParam, Sentinel] = None,
    timeout_sec: Union[None, IntParam, Sentinel] = None,
    min_instances: Union[None, IntParam, Sentinel] = None,
    max_instances: Union[None, IntParam, Sentinel] = None,
    vpc: Union[None, VpcOptions, Sentinel] = None,
    ingress: Union[None, IngressSettings, Sentinel] = None,
    service_account: Union[None, StringParam, Sentinel] = None,
    secrets: Union[None, List[StringParam], ListParam, Sentinel] = None,
):
  '''Decorator for a function that can be called like an RPC service.

  Parameters:
      allowed_origins: Origins allowed to invoke this function. Affects CORS
        options.
      region: Region to deploy functions. Defaults to us-central1.
      memory: MB to allocate to function. Defaults to Memory.MB_256
      timeout_sec: Seconds before a function fails with a timeout error.
        Defaults to 60s.
      min_instances: Count of function instances that should be reserved at all
        time. Instances will be billed while idle. Defaults to 0.
      max_instances: Maximum count of function instances that can be created.
        Defaults to 1000.
      vpc: Configuration for a virtual private cloud. Defaults to no VPC.
      ingress: Configuration for what IP addresses can invoke a function.
        Defaults to all traffic.
      service_account: The service account a function should run as. Defaults to
        the default compute service account.
      secrets: The list of secrets which should be available to this function.

  To reset an attribute to factory default, use USE_DEFAULT.
  '''

  # Construct an HttpsOptions object out from the args passed
  # by the user, if any.
  callable_options = HttpsOptions(
      allowed_origins=allowed_origins,
      allowed_methods=allowed_methods,
      region=region,
      memory=memory,
      timeout_sec=timeout_sec,
      min_instances=min_instances,
      max_instances=max_instances,
      vpc=vpc,
      ingress=ingress,
      service_account=service_account,
      secrets=secrets,
  )

  metadata = {} if callable_options is None else callable_options.metadata()

  trigger = {
      'platform': 'gcfv2',
      **metadata, 'labels': {
          'deployment-callable': 'true',
      },
      'httpsTrigger': {
          'allowInsecure': False
      }
  }

  metadata['apiVersion'] = 1
  metadata['trigger'] = {}

  def https_with_options(func: CallableFunction):

    @functools.wraps(func)
    def call_view_func(request: FlaskRequest) -> any:

      return func(wrap_on_call_handler(request, callable_options))

    metadata['id'] = func.__name__

    manifest = ManifestEndpoint(
        entryPoint=func.__name__,
        region=region,
        platform='gcfv2',
        labels={},
        httpsTrigger={},
        vpc=vpc,
        availableMemoryMb=memory.value if memory is not None else None,
        maxInstances=max_instances,
        minInstances=min_instances,
    )

    call_view_func.firebase_metadata = metadata
    call_view_func.trigger = trigger
    call_view_func.__endpoint__ = manifest

    return call_view_func

  return https_with_options
