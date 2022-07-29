"""Pub/sub trigger for the function to be triggered by Pub/Sub."""

import datetime as dt
import functools
import os
from typing import Any, Callable, Dict, Generic, List, TypeVar, Union
from dataclasses import dataclass

from firebase_functions import CloudEvent
from firebase_functions.options import PubSubOptions, Sentinel, VpcOptions, Memory, IngressSettings
from firebase_functions.manifest import EventTrigger, ManifestEndpoint
from firebase_functions.params import SecretParam, StringParam, IntParam, ListParam

T = TypeVar('T')


@dataclass(frozen=True)
class Message(Generic[T]):
  message_id: str
  publish_time: dt.datetime
  data: str
  attributes: dict[str, str]
  ordering_key: str

  @property
  def json(self) -> Dict[str, Any]:
    return {
        'message_id': self.message_id,
        'publish_time': self.publish_time,
        'data': self.data,
        'attributes': self.attributes,
        'ordering_key': self.ordering_key,
    }


CloudEventMessage = CloudEvent[Message[T]]


def on_message_published(
    *,
    topic: str,
    region: Union[None, StringParam, str] = None,
    memory: Union[None, IntParam, Memory, Sentinel] = None,
    timeout_sec: Union[None, IntParam, int, Sentinel] = None,
    min_instances: Union[None, IntParam, int, Sentinel] = None,
    max_instances: Union[None, IntParam, int, Sentinel] = None,
    vpc: Union[None, VpcOptions, Sentinel] = None,
    ingress: Union[None, IngressSettings, Sentinel] = None,
    service_account: Union[None, StringParam, str, Sentinel] = None,
    secrets: Union[None, List[StringParam], SecretParam, Sentinel] = None,
) -> Callable[[CloudEvent[Message[T]]], None]:
  """
      Decorator for functions that are triggered by Pub/Sub."""

  # Construct an Options object out from the args passed by the user, if any.
  pubsub_options = PubSubOptions(
      topic=topic,
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
  metadata = {}
  metadata = {} if pubsub_options is None else pubsub_options.metadata()

  def wrapper(func):

    @functools.wraps(func)
    def pubsub_view_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__
    project = os.environ.get('GCLOUD_PROJECT')

    manifest = ManifestEndpoint(
        platform='gcfv2',
        entryPoint=func.__name__,
        region=region,
        labels={},
        vpc=vpc,
        availableMemoryMb=memory,
        maxInstances=max_instances,
        minInstances=min_instances,
        eventTrigger=EventTrigger(
            eventType='google.cloud.pubsub.topic.v1.messagePublished',
            eventFilters={
                'topic': f'projects/{project}/topics/{topic}',
            },
        ),
    )

    pubsub_view_func.firebase_metadata = metadata
    pubsub_view_func.__endpoint__ = manifest

    return pubsub_view_func

  return wrapper
