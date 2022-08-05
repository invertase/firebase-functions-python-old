'''Pub/sub trigger for the function to be triggered by Pub/Sub.'''

import datetime as dt
import functools
import os
import flask
import base64

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, TypeVar, Union, Optional

from firebase_functions.options import PubSubOptions, Sentinel, VpcOptions, Memory, IngressSettings
from firebase_functions.manifest import EventTrigger, ManifestEndpoint
from firebase_functions.params import BoolParam, SecretParam, StringParam, IntParam

T = TypeVar('T')

Request = flask.Request
Response = flask.Response


@dataclass(frozen=True)
class CloudEvent(Generic[T]):
  data: T
  specversion: Optional[str] = None
  source: Optional[str] = None
  subject: Optional[str] = None
  type: Optional[str] = None
  time: Optional[dt.datetime] = None


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


CloudEventMessage = CloudEvent[Message[str]]


@dataclass(frozen=True)
class CloudEventPublishedMessage:
  message: Message[Union[dict, str, None]]
  subscription: str


def pubsub_wrap_handler(
    func: Callable[[CloudEventPublishedMessage], None],
    raw: CloudEvent[dict],
) -> Response:

  # Decode the message data
  raw.data['message']['data'] = base64.b64decode(
      raw.data['message']['data']).decode('utf-8')

  # Convert the UTC string into a datetime object
  raw.data['message']['publish_time'] = dt.datetime.strptime(
      raw.data['message']['publish_time'],
      '%Y-%m-%dT%H:%M:%S.%f%z',
  )

  # Pop unnecessary keys from the message data
  raw.data['message'].pop('messageId', None)
  raw.data['message'].pop('publishTime', None)

  # `orderingKey` doesn't come with a snake case alternative,
  # there is no ordering_key in the raw request.
  ordering_key = raw.data['message'].pop('orderingKey', None)

  message: CloudEventPublishedMessage = CloudEventPublishedMessage(
      message=Message(
          **raw.data['message'],
          ordering_key=ordering_key,
      ),
      subscription=raw.data['subscription'],
  )

  func(message)
  response = flask.jsonify(status=200)
  return response


def on_message_published(
    func: Callable[[CloudEventPublishedMessage], None] = None,
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
) -> Callable[[CloudEventPublishedMessage], None]:
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
    def pubsub_view_func(data: CloudEvent[dict]):
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
