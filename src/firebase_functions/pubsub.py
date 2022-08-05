'''Pub/sub trigger for the function to be triggered by Pub/Sub.'''
import logging
import os
import flask
import base64
import functools
import datetime as dt

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, TypeVar, Union, Optional

from firebase_functions.options import PubSubOptions, Sentinel, VpcOptions, Memory, IngressSettings
from firebase_functions.manifest import EventTrigger, ManifestEndpoint
from firebase_functions.params import BoolParam, SecretParam, StringParam, IntParam

T = TypeVar('T')


@dataclass()
class CloudEvent(Generic[T]):
  specversion: str
  source: str
  type: str
  time: dt.datetime
  data: T


@dataclass(frozen=True)
class Message(Generic[T]):
  message_id: str
  publish_time: dt.datetime
  data: T
  attributes: Optional[dict[str, str]] = None
  ordering_key: Optional[str] = None

  @property
  def json(self) -> Dict[str, Any]:
    return {
        'message_id': self.message_id,
        'publish_time': self.publish_time,
        'data': self.data,
        'attributes': self.attributes,
        'ordering_key': self.ordering_key,
    }


@dataclass(frozen=True)
class MessagePublishedData:
  message: Message[Union[dict, str, None]]
  subscription: str


def pubsub_wrap_handler(
    func: Callable[[CloudEvent[MessagePublishedData]], None],
    raw: CloudEvent[Any],
) -> flask.Response:
  logging.getLogger(__name__).debug(raw)

  data = raw.data

  # Decode the message data
  data['message']['data'] = base64.b64decode(
      data['message']['data']).decode('utf-8')

  time = dt.datetime.strptime(
      data['message']['publish_time'],
      '%Y-%m-%dT%H:%M:%S.%f%z',
  )

  # Convert the UTC string into a datetime object
  raw.time = time
  data['message']['publish_time'] = time

  # Pop unnecessary keys from the message data
  data['message'].pop('messageId', None)
  data['message'].pop('publishTime', None)

  # `orderingKey` doesn't come with a snake case alternative,
  # there is no ordering_key in the raw request.
  ordering_key = data['message'].pop('orderingKey', None)

  message: MessagePublishedData = MessagePublishedData(
      message=Message(
          **data['message'],
          ordering_key=ordering_key,
      ),
      subscription=data['subscription'],
  )

  event: CloudEvent[MessagePublishedData] = CloudEvent(
      source=raw.source,
      specversion=raw.specversion,
      type=raw.type,
      time=raw.time,
      data=message,
  )

  func(event)
  response = flask.jsonify(status=200)
  return response


def on_message_published(
    func: Callable[[MessagePublishedData], None] = None,
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
    retry: Union[None, bool, BoolParam] = None,
) -> Callable[[MessagePublishedData], None]:
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
      retry=retry,
  )

  trigger = {} if pubsub_options is None else pubsub_options.metadata()

  def wrapper(func):

    @functools.wraps(func)
    def pubsub_view_func(data: CloudEvent[Any]):
      return pubsub_wrap_handler(
          func=func,
          raw=data,
      )

    project = os.environ.get('GCLOUD_PROJECT')

    manifest = ManifestEndpoint(
        entryPoint=func.__name__,
        eventTrigger=EventTrigger(
            eventType='google.cloud.pubsub.topic.v1.messagePublished',
            eventFilters={
                'topic': f'projects/{project}/topics/{topic}',
            },
            retry=pubsub_options.retry,
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

  return wrapper(func)
