"""Specs for the served functions.yaml of the user's functions"""

# pylint: disable=invalid-name

from dataclasses import dataclass
from typing import TypedDict, Optional, Union

from firebase_functions.options import Memory, Sentinel, VpcOptions
from firebase_functions.params import IntParam, StringParam


class Secret(TypedDict):
  key: str
  secret: Union[str, None]


@dataclass(frozen=True)
class HttpsTrigger():
  invoker: Optional[list[str]] = None


@dataclass(frozen=True)
class CallableTrigger():
  pass


@dataclass(frozen=True)
class EventTrigger():
  eventFilters: Optional[dict] = None
  eventFilterPathPatterns: Optional[dict] = None
  channel: Optional[str] = None
  eventType: Optional[str] = None
  retry: Optional[bool] = None
  region: Optional[str] = None
  serviceAccountEmail: Optional[str] = None


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


@dataclass()
class ManifestEndpoint():
  """An definition of a function as appears in the Manifest."""

  entryPoint: str
  region: Optional[Union[StringParam, str]] = None
  platform: Optional[str] = None
  availableMemoryMb: Union[IntParam, Memory, Sentinel, None] = None
  maxInstances: Union[None, IntParam, int, Sentinel] = None
  minInstances: Union[None, IntParam, int, Sentinel] = None
  concurrency: Optional[int] = None
  serviceAccountEmail: Optional[str] = None
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


@dataclass(frozen=True)
class ManifestRequiredAPI():
  api: str
  reason: str


@dataclass(frozen=True)
class ManifestStack():
  specVersion: str = 'v1alpha1'
  endpoints: Optional[dict[str, ManifestEndpoint]] = None
  requiredAPIs: Union[Optional[list[ManifestRequiredAPI]], None] = None
