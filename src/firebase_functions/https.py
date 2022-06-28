import functools

from flask import Response as FlaskResponse, Request as FlaskRequest
from typing import Any, Callable, Generic, List, TypeVar, Union, Tuple, Optional
from dataclasses import dataclass

from firebase_functions import params
from firebase_functions import options
from firebase_functions.manifest import ManifestEndpoint

Request = FlaskRequest
Response = FlaskResponse

T = TypeVar('T')


@dataclass(frozen=True)
class DecodedAppCheckToken:
  '''Decoded AppCheck JWT token.

  TODO: replace with admin SDK type if/when available
  '''

  iss: str
  '''The issuer identifier for the issuer of the response.

  This value is a URL with the format
  `https://firebaseappcheck.googleapis.com/<PROJECT_NUMBER>`, where
  `<PROJECT_NUMBER>` is the same project number specified in the [`aud`](#aud)
  property.
  '''

  sub: str
  '''The audience for which this token is intended.

  This value is a JSON array of two strings, the first is the project number
  of your Firebase project, and the second is the project ID of the same
  project.
  '''

  aud: List[str]
  '''The audience for which this token is intended.

  This value is a JSON array of two strings, the first is the project number of
  your Firebase project, and the second is the project ID of the same project.
  '''

  exp: int
  '''The App Check token's expiration time, in seconds since the Unix epoch.

  This is the time at which this App Check token expires and should no longer be
  considered valid.
  '''

  iat: int
  '''The App Check token's issued-at time, in seconds since the Unix epoch.

  This is the time at which this App Check token was issued and should start to
  be considered valid.;
  '''

  app_id: str
  '''The App ID corresponding to the App the App Check token belonged to.

    This value is not actually one of the JWT token claims. It is added as a
    convenience, and is set as the value of the [`sub`](#sub) property.
    '''

  def get(self, prop: str) -> Any:
    ''' Get a property from the AppCheck token. '''
    pass

  def __getattribute__(self, name: str) -> Any:
    pass


@dataclass(frozen=True)
class AppCheckData:
  '''The interface for AppCheck tokens verified in Callable functions.'''
  app_id: str
  token: DecodedAppCheckToken


@dataclass(frozen=True)
class AuthData:
  '''The interface for Auth tokens verified in Callable functions.'''

  uid: str
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

  instance_id_token: str
  '''An unverified token for a Firebase Instance ID.'''

  raw_request: Request
  '''The raw request handled by the callable.'''


class HttpsFunction(Callable):
  '''Function type for https decorators.'''

  def __init__(self, req: Request, res: Optional[Response] = None) -> None:
    self.request = req
    self.response = res
    self.__trigger__ = None
    self.__endpoint__ = None

  @property
  def trigger(self):
    return self.__trigger__

  @trigger.setter
  def trigger(self, v):
    self.__trigger__ = v

  @property
  def endpoint(self):
    return self.__endpoint__

  @endpoint.setter
  def endpoint(self, v):
    self.__endpoint__ = v


class CallableFunction(HttpsFunction):

  def __init__(self, req: CallableRequest[T]) -> Any:
    super().__init__(req)


@dataclass(frozen=True)
class OnRequestOptions(options.HttpsOptions):
  """Options for https on_request functions.

  Attributes:
    allowed_origins: Origins allowed to invoke this function. Affects CORS
        options.
    allowed_methods: Methods allowed to invoke this function. Affects CORS
        options.

  To reset an attribute to factory default, use options.USE_DEFAULT
  """
  allowed_origins: str = None
  allowed_methods: str = None
  secrets: Union[None, Tuple[str], params.ListParam, options.Sentinel] = None

  # override metadata and merge with our own options
  def metadata(self):
    return {
        'allowedOrigins': self.allowed_origins,
        'allowedMethods': self.allowed_origins,
        'secrets': self.secrets,
        **super().metadata()
    }


def on_request(
    allowed_origins: str = None,
    allowed_methods: str = None,
    region: Optional[str] = None,
    memory: Union[None, int, options.Memory, options.Sentinel] = None,
    timeout_sec: Optional[int] = None,
    min_instances: Union[None, int, params.IntParam, options.Sentinel] = None,
    max_instances: Union[None, int, params.IntParam, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.StringParam,
                           options.Sentinel] = None,
    secrets: Union[None, List[str], params.ListParam, options.Sentinel] = None,
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

  # Construct an Options object out from the args passed by the user, if any.
  request_options = options.HttpsOptions(allowed_origins, allowed_methods,
                                         region, memory.value, timeout_sec,
                                         min_instances, max_instances, vpc,
                                         ingress, service_account, secrets)

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
    def wrapper_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__

    manifest = ManifestEndpoint(
        entryPoint=func.__name__,
        region=region,
        platform='gcfv2',
        labels={},
        httpsTrigger={},
        vpc=vpc,
        availableMemoryMb=memory.value,
        maxInstances=max_instances,
        minInstances=min_instances,
    )

    wrapper_func.firebase_metadata = metadata
    wrapper_func.trigger = trigger
    wrapper_func.__endpoint__ = manifest

    return wrapper_func

  return https_with_options


def on_call(
    allowed_origins: Optional[str] = None,
    region: Optional[str] = None,
    memory: Union[None, int, params.IntParam, options.Sentinel] = None,
    timeout_sec: Union[None, int, params.IntParam, options.Sentinel] = None,
    min_instances: Union[None, int, params.IntParam, options.Sentinel] = None,
    max_instances: Union[None, int, params.IntParam, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.StringParam,
                           options.Sentinel] = None,
    secrets: Union[None, List[str], params.ListParam, options.Sentinel] = None,
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

  # Construct an Options object out from the args passed by the user, if any.
  callable_options = options.HttpsOptions(allowed_origins, region, memory,
                                          timeout_sec, min_instances,
                                          max_instances, vpc, ingress,
                                          service_account, secrets)

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
    def wrapper_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__

    manifest = ManifestEndpoint(
        entryPoint=func.__name__,
        region=region,
        platform='gcfv2',
        labels={},
        httpsTrigger={},
        vpc=vpc,
        availableMemoryMb=memory.value,
        maxInstances=max_instances,
        minInstances=min_instances,
    )

    wrapper_func.firebase_metadata = metadata
    wrapper_func.trigger = trigger
    wrapper_func.__endpoint__ = manifest

    return wrapper_func

  return https_with_options
