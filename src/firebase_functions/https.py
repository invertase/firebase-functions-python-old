from copy import deepcopy
import dataclasses
from enum import Enum
import functools
import json
import re
import flask
from typing import (Any, Generic, List, TypeVar, Union, Optional)
from dataclasses import dataclass
from collections.abc import Callable
from firebase_admin import auth

from firebase_functions import apps
from firebase_functions.log import (error, info, warn, debug)
from firebase_functions.errors import FunctionsErrorCode, HttpsError
from firebase_functions.manifest import HttpsTrigger, ManifestEndpoint
from firebase_functions.params import (SecretParam, StringParam, IntParam,
                                       ListParam)
from firebase_functions.options import (HttpsOptions, Memory, VpcOptions,
                                        IngressSettings, Sentinel)

FlaskRequest = flask.Request
FlaskResponse = flask.Response

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

  This value is a JSON array of two StringParamings, the first is
  the project number of your Firebase project, and the second is the
  project ID of the same project.
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


@dataclass(frozen=True)
class AppCheckData:
  '''The IntParamerface for AppCheck tokens verified in Callable functions.'''
  app_id: StringParam
  token: DecodedAppCheckToken


@dataclass(frozen=True)
class AuthData:
  '''The IntParamerface for Auth tokens verified in Callable functions.'''

  uid: str
  '''User ID of the auth token.'''

  token: dict
  '''TODO: replace with auth token definition'''


@dataclass(frozen=True)
class CallableRequest(Generic[T]):
  '''The request sent to a callable function.'''

  raw_request: FlaskRequest
  '''The raw request handled by the callable.'''

  data: Optional[T] = None
  '''The arguments passed in the call.'''

  app: Optional[AppCheckData] = None
  '''The application which made the call.'''

  auth: Optional[AuthData] = None
  '''The user who made the call.'''

  instance_id_token: Optional[StringParam] = None
  '''An unverified token for a Firebase Instance ID.'''


def on_request(
    func: Callable[[FlaskRequest], FlaskResponse],
    *,
    allowed_origins: Optional[StringParam] = None,
    allowed_methods: Optional[StringParam] = None,
    region: Optional[StringParam] = None,
    memory: Union[IntParam, Memory, Sentinel, None] = None,
    timeout_sec: Optional[IntParam] = None,
    min_instances: Union[None, IntParam, IntParam, Sentinel] = None,
    max_instances: Union[None, IntParam, IntParam, Sentinel] = None,
    vpc: Union[None, VpcOptions, Sentinel] = None,
    ingress: Union[None, IngressSettings, Sentinel] = None,
    service_account: Union[None, StringParam, StringParam, Sentinel] = None,
    secrets: Union[List[StringParam], SecretParam, Sentinel, None] = None,
) -> Callable[[FlaskRequest], FlaskResponse]:
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

  # Construct an Options object out from the args passed
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

  @functools.wraps(func)
  def request_view_func(request: FlaskRequest) -> FlaskResponse:

    return func(request)

  manifest = ManifestEndpoint(
      entryPoint=func.__name__,
      region=region,
      platform='gcfv2',
      labels={},
      httpsTrigger={},
      vpc=vpc,
      availableMemoryMb=memory,
      maxInstances=max_instances,
      minInstances=min_instances,
  )

  functools.partial(
      request_view_func,
      firebase_metadata=metadata,
      trigger=trigger,
      __endpoint__=manifest,
  )

  return request_view_func


class TokenStatus(Enum):
  '''The status of a token.'''

  MISSING = 'MISSING'
  '''The token is missing.'''

  VALID = 'VALID'
  '''The token is valid.'''

  INVALID = 'INVALID'
  '''The token is invalid.'''


class CallableTokenStatus():
  app: Optional[TokenStatus] = None
  auth: Optional[TokenStatus] = None

  def __init__(self) -> None:
    self.app = TokenStatus.INVALID
    self.auth = TokenStatus.INVALID

  def to_dict(self) -> dict:
    return {
        'app': self.app.value if self.app is not None else None,
        'auth': self.auth.value if self.auth is not None else None,
    }


def check_auth_token(req: FlaskRequest, ctx: CallableRequest) -> TokenStatus:
  ''' Validate the auth token in the callable request. '''
  authorization = req.headers.get('Authorization')
  if authorization is None:
    return TokenStatus.MISSING
  match = re.search(r'Bearer (.*)', authorization)
  if match is not None:
    try:
      id_token = match.string
      auth_token: dict[str, str] = {}
      auth.verify_id_token(id_token, app=apps())

      ctx = dataclasses.replace(
          ctx,
          auth=AuthData(uid=auth_token['uid'], token=auth_token),
      )

      return TokenStatus.VALID
    except auth.InvalidIdTokenError as e:
      error(f'Error validating token: {e}')
      return TokenStatus.INVALID
  return TokenStatus.INVALID


def check_app_token(req: FlaskRequest, ctx: CallableRequest) -> TokenStatus:
  ''' Validate the app token in the callable request. '''
  app_check = req.headers.get('X-Firebase-AppCheck')
  if app_check is None:
    return TokenStatus.MISSING

  # TODO validate the token using the Admin SDK once app check is supported.
  # For now, just assume it's valid.
  warn(f'App check is not supported in the Admin SDK.')
  ctx = dataclasses.replace(ctx, app=None)
  return TokenStatus.VALID


def check_tokens(
    req: FlaskRequest,
    ctx: CallableRequest,
) -> CallableTokenStatus:
  verifications = CallableTokenStatus()

  verifications.auth = check_auth_token(req, ctx)
  verifications.app = check_app_token(req, ctx)

  log_payload = {
      **verifications.to_dict(),
      'logging.googleapis.com/labels': {
          'firebase-log-type': 'callable-request-verification',
      },
  }

  errs = []
  if verifications.app == TokenStatus.INVALID:
    errs.append(('AppCheck token was rejected.', log_payload))

  if verifications.auth == TokenStatus.INVALID:
    errs.append(('Auth token was rejected.', log_payload))

  if len(errs) == 0:
    info('Callable request verification passed', log_payload)
  else:
    warn(f'Callable request verification failed: ${errs}', log_payload)

  # Clears out the content in the logPayload
  # or it will be persisted in the next call.
  log_payload.clear()

  return verifications


def valid_request(request: FlaskRequest) -> bool:
  # The body must not be empty.
  if request.json is None:
    warn('Request is missing body.')
    return False

  # Make sure it's a POST.
  if request.method != 'POST':
    warn('Request has invalid method.', request.method)
    return False

  # Check that the Content-Type is JSON.
  content_type: Optional[str] = request.headers.get('Content-Type') if getattr(
      request.headers, 'Content-Type') is not None else ''

  if content_type is None:
    warn('Request is missing Content-Type.', content_type)
    return False

  # If it has a charset, just ignore it for now.
  semi_colon = 0

  try:
    semi_colon = content_type.index(';')
    if semi_colon >= 0:
      content_type = content_type[0:semi_colon].strip()
  except ValueError:
    pass

  if content_type != 'application/json':

    warn('Request has incorrect Content-Type.', content_type)
    return False

  # The body must have data.
  if request.json == 'undefined':
    warn('Request body is missing data.', request.json)
    return False

  extra_keys = {}

  # Verify that the body does not have any extra fields.
  for key in request.json.keys():
    if key != 'data':
      extra_keys.update({key: request.json[key]})

  if len(extra_keys) != 0:
    warn(
        'Request body has extra fields: ',
        ''.join(f'{key}: {value},' for (key, value) in extra_keys.items()),
    )

  return True


class HttpResponseBody:
  '''The body of an HTTP response from a callable function.'''
  result: Optional[Any] = None
  error: Optional[HttpsError] = None


def wrap_on_call_handler(
    func: Callable[[CallableRequest], Any],
    request: FlaskRequest,
    response: FlaskResponse,
    options: HttpsOptions,
) -> FlaskResponse:
  if not valid_request(request):
    # TODO use the Cloud Logger to log an error entry.
    raise HttpsError(FunctionsErrorCode.INVALID_ARGUMENT, 'Bad Request')

  context: CallableRequest = CallableRequest(raw_request=request)
  token_status = check_tokens(request, context)

  if token_status.auth == TokenStatus.INVALID:
    raise HttpsError(FunctionsErrorCode.UNAUTHENTICATED, 'Unauthenticated')

  if token_status.app == TokenStatus.INVALID and not options.allow_invalid_app_check_token:
    raise HttpsError(FunctionsErrorCode.UNAUTHENTICATED, 'Unauthenticated')

  instance_id = request.headers.get('Firebase-Instance-ID-Token')
  if instance_id is not None:
    # Validating the token requires an http request, so we don't do it.
    # If the user wants to use it for something, it will be validated then.
    # Currently, the only real use case for this token is for sending
    # pushes with FCM. In that case, the FCM APIs will validate the token.
    context = dataclasses.replace(
        context,
        instance_id_token=request.headers.get('Firebase-Instance-ID-Token'),
    )

  data = json.loads(request.data)
  result: FlaskResponse

  arg: CallableRequest = CallableRequest(
      raw_request=context.raw_request,
      data=data,
      auth=context.auth,
      app=context.app,
      instance_id_token=context.instance_id_token,
  )

  try:
    result = func(arg)

    response_body = flask.jsonify(data=result, status=200)

    response = response_body
  except Exception as err:
    if not isinstance(err, HttpsError):
      error('Unhandled error', err)
      err = HttpsError(FunctionsErrorCode.INTERNAL, 'INTERNAL')

    status = err.http_error_code.status

    response_body = flask.jsonify(error=err.to_dict(), status=status)

    response = response_body

  return response


def on_call(
    func: Callable[[CallableRequest], Any],
    *,
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
    secrets: Union[List[StringParam], SecretParam, Sentinel, None],
) -> Callable[[CallableRequest], Any]:
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

  metadata['id'] = func.__name__

  def wrapper(func):

    @functools.wraps(func)
    def call_view_func(request: FlaskRequest, response: FlaskResponse):
      wrap_on_call_handler(
          func,
          request,
          response,
          callable_options,
      )

      return func

    manifest = ManifestEndpoint(
        entryPoint=metadata['id'],
        region=region,
        platform='gcfv2',
        labels={},
        httpsTrigger={},
        vpc=vpc,
        availableMemoryMb=memory,
        maxInstances=max_instances,
        minInstances=min_instances,
    )

    call_view_func.firebase_metadata = metadata
    call_view_func.trigger = trigger
    call_view_func.__endpoint__ = manifest

    return call_view_func

  return wrapper