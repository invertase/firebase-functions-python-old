"""Specs for the served functions.yaml of the user's functions"""

# pylint: disable=invalid-name

from dataclasses import dataclass
from typing import TypedDict, Optional, Union


class Vpc(TypedDict):
  connector: str
  egressSettings: str


class Secret(TypedDict):
  key: str
  secret: Union[str, None]


class HttpsTrigger(TypedDict):
  invoker: list[str]


class EventTrigger(TypedDict):
  eventFilters: dict
  eventFilter_path_patterns: dict
  channel: str
  eventType: str
  retry: bool
  region: str
  serviceAccountEmail: str


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


@dataclass(frozen=True)
class ManifestEndpoint():
  """An definition of a function as appears in the Manifest."""

  entryPoint: str
  region: list[str]
  platform: str = None
  availableMemoryMb: int = None
  maxInstances: int = None
  minInstances: int = None
  concurrency: int = None
  serviceAccountEmail: str = None
  timeoutSeconds: int = None
  cpu: Union[int, str] = 'gcf_gen1'
  vpc: Vpc = None
  labels: dict[str, str] = None
  ingressSettings: str = None
  environmentVariables: dict = None
  secretEnvironmentVariables: list[Secret] = None
  httpsTrigger: HttpsTrigger = None
  callableTrigger: dict = None
  eventTrigger: EventTrigger = None
  scheduleTrigger: ScheduleTrigger = None
  blockingTrigger: BlockingTrigger = None


@dataclass(frozen=True)
class ManifestRequiredAPI():
  api: str
  reason: str


@dataclass(frozen=True)
class ManifestStack():
  specVersion: str = 'v1alpha1'
  endpoints: dict[str, ManifestEndpoint] = None
  requiredAPIs: Union[Optional[list[ManifestRequiredAPI]], None] = None
