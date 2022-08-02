'''Pub/sub trigger for the function to be triggered by Pub/Sub.'''

import datetime as dt
import functools
import os

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, TypeVar, Union

import flask

from firebase_functions import CloudEvent
from firebase_functions.options import PubSubOptions, Sentinel, VpcOptions, Memory, IngressSettings
from firebase_functions.manifest import EventTrigger, ManifestEndpoint
from firebase_functions.params import SecretParam, StringParam, IntParam

T = TypeVar('T')

Request = flask.Request
Response = flask.Response


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


def pubsub_wrap_handler(
    func: Callable[[CloudEvent], None],
    request: Request,
    options: PubSubOptions,
):
  pass


def on_message_published(
    func: Callable[[CloudEvent], None] = None,
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
  '''
      Decorator for functions that are triggered by Pub/Sub.'''

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

  trigger = {} if pubsub_options is None else pubsub_options.metadata()

  def wrapper(func):

    @functools.wraps(func)
    def pubsub_view_func(request: Request):

      return pubsub_wrap_handler(
          func=func,
          request=request,
          options=pubsub_options,
      )

    project = os.environ.get('GCLOUD_PROJECT')

    manifest = ManifestEndpoint(
        entryPoint=func.__name__,
        eventTrigger=EventTrigger(
            eventType='google.cloud.pubsub.topic.v1.messagePublished',
            eventFilters={
                'topic': f'projects/{project}/topics/{topic}',
            },
        ),
        region=pubsub_options.region,
        availableMemoryMb=pubsub_options.memory,
        timeoutSeconds=pubsub_options.timeout_sec,
        minInstances=pubsub_options.min_instances,
        maxInstances=pubsub_options.max_instances,
        vpc=pubsub_options.vpc,
        ingressSettings=pubsub_options.ingress,
        serviceAccount=pubsub_options.service_account,
        secretEnvironmentVariables=pubsub_options.secrets,
    )

    pubsub_view_func.__firebase_trigger__ = trigger
    pubsub_view_func.__firebase_endpoint__ = manifest

    return pubsub_view_func

  if func is None:
    return wrapper

  return wrapper
