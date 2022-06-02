"""Specs for the served functions.yaml of the user's functions"""

from dataclasses import dataclass
from typing import TypedDict, Optional, Union


class Vpc(TypedDict):
  connector: str
  egress_settings: str


class Secret(TypedDict):
  key: str
  secret: Union[str, None]


class HttpsTrigger(TypedDict):
  invoker: list[str]


class EventTrigger(TypedDict):
  event_filters: dict
  event_filter_path_patterns: dict
  channel: str
  event_type: str
  retry: bool
  region: str
  service_account_email: str


class RetryConfig(TypedDict):
  retry_count: int
  max_retry_duration: str
  min_backoff_duration: str
  max_backoff_duration: str
  max_doublings: int


class ScheduleTrigger(TypedDict):
  schedule: dict
  timezone: str
  retry_config: RetryConfig


class BlockingTrigger(TypedDict):
  event_type: str
  options: dict


@dataclass(frozen=True)
class ManifestEndpoint():
  """An definition of a function as appears in the Manifest."""

  entry_point: str
  region: list[str]
  platform: str
  available_memory_mb: int
  max_instances: int
  min_instances: int
  concurrency: int
  service_account_email: str
  timeout_seconds: int
  vpc: Vpc
  labels: dict[str, str]
  ingress_settings: str
  environment_variables: dict
  secret_environment_variables: list[Secret]
  https_trigger: HttpsTrigger
  callable_trigger: dict
  event_trigger: EventTrigger
  schedule_trigger: ScheduleTrigger
  blocking_trigger: BlockingTrigger
  cpu: Union[int, str] = 'gcf_gen1'


@dataclass(frozen=True)
class ManifestRequiredAPI():
  api: str
  reason: str


class Endpoint(TypedDict):
  key: str
  endpoint: ManifestEndpoint


@dataclass(frozen=True)
class ManifestStack():
  endpoints: dict[str, ManifestEndpoint]
  required_apis: Union[Optional[list[ManifestRequiredAPI]], None] = None
  spec_version: str = 'v1alpha1'
