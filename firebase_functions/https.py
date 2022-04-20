"""HTTPS """
import functools
from flask import Response as FlaskResponse, Request as FlaskRequest
from dataclasses import dataclass
from typing import TypeVar, Callable, Union, Generic, Tuple, Any, Optional
from firebase_functions import options, params


Request = FlaskRequest

Response = FlaskResponse


@dataclass(frozen=True)
class OnRequestOptions(options.Options):
  """Options for https on_request functions.

  Attributes:
    allowed_origins: Origins allowed to invoke this function. Affects CORS
        options.
    allowed_methods: Methods allowed to invoke this function. Affects CORS
        options.

  To reset an attribute to factory default, use options.USE_DEFAULT
  """
  allowed_origins: str = None,
  allowed_methods: str = None,
  secrets: Union[None, Tuple[str],
                 params._ListExpression, options.Sentinel] = None

  # override metadata and merge with our own options
  def metadata(self):
    return {
        'allowedOrigins': self.allowed_origins,
        'allowedMethods': self.allowed_origins,
        'secrets': self.secrets,
        **super().metadata()
    }


def on_request(
    func: Callable[[Request], Response] = None,
    opts: Optional[OnRequestOptions] = None
) -> Callable[[Request], Response]:
  """Decorator for a function that handles raw HTTPS requests.

  Parameters:

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

  To reset an attribute to factory default, use options.USE_DEFAULT
  """

  metadata = {} if opts is None else opts.metadata()

  def https_with_options(func):
    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__
    wrapper_func.firebase_metadata = metadata
    return wrapper_func

  if func is None:
    return https_with_options

  return https_with_options(func)
