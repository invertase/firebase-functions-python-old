from enum import Enum
from dataclasses import dataclass
import os
from typing import List, Optional, Union

from firebase_functions.params import IntParam, StringParam, ListParam


class Sentinel:
  ''' Class for USE_DEFAULT. '''

  def __init__(self, description):
    self.description = description


USE_DEFAULT = Sentinel('Value used to reset an option to factory defaults')
''' Used to reset a function option to factory default. '''


class VpcEgressSettings(str, Enum):
  ''' Valid settings for VPC egress. '''
  PRIVATE_RANGES_ONLY = 'PRIVATE_RANGES_ONLY'
  ALL_TRAFFIC = 'ALL_TRAFFIC'


@dataclass(frozen=True)
class VpcOptions:
  '''Configuration for a virtual private cloud (VPC).

  Attributes:
    connector: The ID of the connector to use. For maximal portability,
        prefer just an <id> instead of
        'projects/<project>/locations/<region>/connectors/<id>'.
    egress_setting: What kinds of outgoing connections can be established.
  '''
  connector: str
  egress_settings: VpcEgressSettings


class IngressSettings(str, Enum):
  '''What kind of traffic can access this Cloud Function.'''
  ALLOW_ALL = 'ALLOW_ALL'
  ALLOW_INTERNAL_ONLY = 'ALLOW_INTERNAL_ONLY'
  ALLOW_INTERNAL_AND_GCLB = 'ALLOW_INTERNAL_AND_GCLB'


class Memory(Enum):
  '''Valid memory settings.'''
  MB_256 = 256
  MB_512 = 512
  GB_1 = 1 << 10
  GB_2 = 2 << 10
  GB_4 = 4 << 10
  GB_8 = 8 << 10


@dataclass(frozen=True)
class GlobalOptions:
  '''Options available for all function types in a codebase.

  Attributes:
      region: (str) Region to deploy functions. Defaults to us-central1.
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
  '''
  allowed_origins: str = None
  allowed_methods: str = None
  region: Optional[str] = None
  memory: Union[None, int, Sentinel] = None
  timeout_sec: Union[None, int, Sentinel] = None
  min_instances: Union[None, int, Sentinel] = None
  max_instances: Union[None, int, Sentinel] = None
  vpc: Union[None, VpcOptions, Sentinel] = None
  ingress: Union[None, IngressSettings, Sentinel] = None
  service_account: Union[None, str, Sentinel] = None
  secrets: Union[None, List[str], ListParam, Sentinel] = None

  def metadata(self):
    return {
        'allowed_origins': self.allowed_methods,
        'allowed_methods': self.allowed_methods,
        'region': self.region,
        'memory': self.memory,
        'timeout_sec': self.timeout_sec,
        'min_instances': self.min_instances,
        'max_instances': self.max_instances,
        'vpc': self.vpc,
        'ingress': self.ingress,
        'service_account': self.service_account
    }

  def __eq__(self, other):
    """Overrides the default implementation"""
    if isinstance(other, GlobalOptions):
      return (self.allowed_origins == other.allowed_origins and
              self.allowed_methods == other.allowed_methods and
              self.region == other.region and self.memory == other.memory and
              self.memory == other.memory and
              self.timeout_sec == other.timeout_sec and
              self.min_instances == other.min_instances and
              self.max_instances == other.max_instances and
              self.vpc == other.vpc and self.ingress == other.ingress and
              self.ingress == other.ingress and
              self.service_account == other.service_account)
    return NotImplemented


@dataclass(frozen=True)
class HttpsOptions(GlobalOptions):
  '''Options available for all function types in a codebase.

  Attributes:
      region: (str) Region to deploy functions. Defaults to us-central1.
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
  '''

  def __init__(self):
    super().__init__()
    self.set_from_global_options()

  def set_from_global_options(self):
    '''Set options from global options. '''
    self.allowed_origins = _global_options.allowed_origins
    self.allowed_methods = _global_options.allowed_methods
    self.region = _global_options.region
    self.memory = _global_options.memory
    self.timeout_sec = _global_options.timeout_sec
    self.min_instances = _global_options.min_instances
    self.max_instances = _global_options.max_instances
    self.vpc = _global_options.vpc
    self.ingress = _global_options.ingress
    self.service_account = _global_options.service_account


@dataclass(frozen=True)
class PubSubOptions(GlobalOptions):
  '''Options available for all Pub/Sub function types in a codebase.

  Attributes:
      region: (str) Region to deploy functions. Defaults to us-central1.
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
  '''
  topic: str = None

  def metadata(self):
    project = os.environ.get('GCLOUD_PROJECT')
    return {
        'topic': self.topic,
        'trigger': {
            'eventType': 'google.cloud.pubsub.topic.v1.messagePublished',
            'eventFilters': {
                'resource': f'projects/{project}/topics/{self.topic}',
            }
        },
        **super().metadata()
    }


# TODO move to private module and store state there


class _GlobalOptionsState:
  '''State for GlobalOptions.'''

  options: GlobalOptions = None

  def __init__(self):
    self.options = GlobalOptions()

  def set_options(self, options: GlobalOptions) -> None:
    self.options = options


_global_options = _GlobalOptionsState()


def set_global_options(*,
                       region: Optional[str] = None,
                       memory: Union[None, int, Sentinel] = None,
                       timeout_sec: Union[None, int, Sentinel] = None,
                       min_instances: Union[None, int, Sentinel] = None,
                       max_instances: Union[None, int, Sentinel] = None,
                       vpc: Union[None, VpcOptions, Sentinel] = None,
                       ingress: Union[None, IngressSettings, Sentinel] = None,
                       service_account: Union[None, str, Sentinel] = None):
  _global_options.set_options(
      GlobalOptions(
          region=region,
          memory=memory,
          timeout_sec=timeout_sec,
          min_instances=min_instances,
          max_instances=max_instances,
          vpc=vpc,
          ingress=ingress,
          service_account=service_account,
      ))
