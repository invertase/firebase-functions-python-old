'''Specs for the served functions.yaml of the user's functions'''

# pylint: disable=invalid-name

from dataclasses import dataclass
from typing import TypedDict, Optional, Union
from typing_extensions import NotRequired

from firebase_functions.options import Memory, Sentinel, VpcOptions
from firebase_functions.params import IntParam, StringParam


class Secret(TypedDict):
  key: str
  secret: Union[str, None]


class HttpsTrigger(TypedDict):
  invoker: NotRequired[list[str]]


class CallableTrigger(TypedDict):
  pass


class EventTrigger(TypedDict):
  eventFilters: NotRequired[dict]
  eventFilterPathPatterns: NotRequired[dict]
  channel: NotRequired[str]
  eventType: NotRequired[str]
  retry: NotRequired[bool]
  region: NotRequired[str]
  serviceAccountEmail: NotRequired[str]


class RetryConfig(TypedDict):
  retryCount: int
  maxRetryDuration: str
  minBackoffDuration: str
  maxBackoffDuration: str
  maxDoublings: int


class ScheduleTrigger(TypedDict):
  schedule: dict
  timezone: str
  retryConfig: RetryConfig


class BlockingTrigger(TypedDict):
  eventType: str
  options: dict


ServiceAccount = str


@dataclass(frozen=True)
class ManifestEndpoint():
  '''An definition of a function as appears in the Manifest.'''

  entryPoint: str
  region: Optional[Union[StringParam, str]] = None
  availableMemoryMb: Union[IntParam, Memory, Sentinel, None] = None
  maxInstances: Union[None, IntParam, int, Sentinel] = None
  minInstances: Union[None, IntParam, int, Sentinel] = None
  concurrency: Optional[int] = None
  serviceAccount: Optional[ServiceAccount] = None
  timeoutSeconds: Optional[int] = None
  cpu: Union[int, str] = 'gcf_gen1'
  vpc: Union[None, VpcOptions, Sentinel] = None
  labels: Optional[dict[str, str]] = None
  ingressSettings: Optional[str] = None
  environmentVariables: Optional[dict] = None
  secretEnvironmentVariables: Optional[list[Secret]] = None
  httpsTrigger: Optional[HttpsTrigger] = None
  callableTrigger: Optional[dict] = None
  eventTrigger: Optional[EventTrigger] = None
  scheduleTrigger: Optional[ScheduleTrigger] = None
  blockingTrigger: Optional[BlockingTrigger] = None
  platform: str = 'gcfv2'


class RequiredAPi(TypedDict):
  apiName: str
  reason: NotRequired[str]


@dataclass(frozen=True)
class Manifest():
  specVersion: str = 'v1alpha1'
  requiredApis: Optional[list[RequiredAPi]] = None
  params: Optional[list[str]] = None
  endpoints: Optional[dict[str, ManifestEndpoint]] = None
