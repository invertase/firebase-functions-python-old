"""HTTPS request modeul"""

import functools
from urllib import response

from flask import Response as FlaskResponse, Request as FlaskRequest
from dataclasses import dataclass

from typing import Any, Callable, List, Union, Tuple, Optional

from requests import request

from firebase_functions import params
from firebase_functions import options

from firebase_functions.params import IntParam, StringParam, ListParam

Request = FlaskRequest
Response = FlaskResponse

# HttpsFunction = Callable[[Request], Response]


class HttpsFunction(Callable):
  '''Function type for https decorators.'''

  def __init__(self, req: Request, res: Response):
    self.request = req
    self.response = res
    self.__trigger__ = [None, Any]
    self.__endpoint__ = None

  @property
  def __trigger__(self):
    return self.__trigger__

  @property
  def __endpoint__(self):
    return self.__endpoint__


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
    memory: Union[None, int, IntParam, options.Sentinel] = None,
    timeout_sec: Optional[int] = None,
    min_instances: Union[None, int, IntParam, options.Sentinel] = None,
    max_instances: Union[None, int, IntParam, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, StringParam, options.Sentinel] = None,
    secrets: Union[None, List[str], ListParam, options.Sentinel] = None,
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
  request_options = options.Options(allowed_origins, allowed_methods, region,
                                    memory, timeout_sec, min_instances,
                                    max_instances, vpc, ingress,
                                    service_account, secrets)

  metadata = {} if request_options is None else request_options.metadata()

  metadata['apiVersion'] = 1
  metadata['trigger'] = {}

  def https_with_options(func: HttpsFunction):

    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__
    wrapper_func.firebase_metadata = metadata
    return wrapper_func

  return https_with_options
