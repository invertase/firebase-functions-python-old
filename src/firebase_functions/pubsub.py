"""Pub/sub trigger for the function to be triggered by Pub/Sub."""

import datetime
import functools
import os
from typing import Callable, Generic, TypeVar, Union
from dataclasses import dataclass

from firebase_functions import CloudEvent, options
from firebase_functions.manifest import EventTrigger, ManifestEndpoint
from firebase_functions.params import StringParam, IntParam, ListParam

T = TypeVar('T')


@dataclass(frozen=True)
class Message(Generic[T]):
  message_id: str
  publish_time: datetime
  data: str
  attributes: dict[str, str]
  ordering_key: str

  @property
  def json(self) -> T:
    return {
        'message_id': self.message_id,
        'publish_time': self.publish_time,
        'data': self.data,
        'attributes': self.attributes,
        'ordering_key': self.ordering_key,
    }


CloudEventMessage = CloudEvent[Message[T]]


@dataclass(frozen=True)
class PubSubFunction(Callable[[CloudEventMessage], None]):
  '''Function type for https decorators.'''

  def __init__(self, message: CloudEventMessage):
    self.message = message
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


def on_message_published(
    *,
    topic: str,
    region: Union[None, str, StringParam, options.Sentinel] = None,
    memory: Union[None, int, options.Memory, options.Sentinel] = None,
    timeout_sec: Union[None, int, IntParam, options.Sentinel] = None,
    min_instances: Union[None, int, IntParam, options.Sentinel] = None,
    max_instances: Union[None, int, IntParam, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, StringParam, options.Sentinel] = None,
    secrets: Union[None, list[str], ListParam, options.Sentinel] = None,
):
  """
      Decorator for functions that are triggered by Pub/Sub."""

  # Construct an Options object out from the args passed by the user, if any.
  pubsub_options = options.PubSubOptions(topic, region, memory, timeout_sec,
                                         min_instances, max_instances, vpc,
                                         ingress, service_account, secrets)
  metadata = {}
  metadata = {} if pubsub_options is None else pubsub_options.metadata()

  def pubsub_with_topic(func: PubSubFunction):

    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
      return func(*args, **kwargs)

    metadata['id'] = func.__name__
    project = os.environ.get('GCLOUD_PROJECT')

    manifest = ManifestEndpoint(
        platform='gcfv2',
        entryPoint=func.__name__,
        region=region,
        labels={},
        vpc=vpc,
        availableMemoryMb=memory.value,
        maxInstances=max_instances,
        minInstances=min_instances,
        eventTrigger=EventTrigger(
            eventType='google.cloud.pubsub.topic.v1.messagePublished',
            eventFilters={
                'topic': f'projects/{project}/topics/{topic}',
            },
        ),
    )

    wrapper_func.firebase_metadata = metadata
    wrapper_func.__endpoint__ = manifest

    return wrapper_func

  return pubsub_with_topic
