"""Pub/sub trigger for the function to be triggered by Pub/Sub."""

import json
import os
import flask
import base64
import functools
import datetime as dt

import cloudevents.http as ce

from dataclasses import dataclass
from typing import Any, Callable, Generic, List, TypeVar, Union, Optional

from firebase_functions.options import (
    PubSubOptions,
    Sentinel,
    VpcEgressSettings,
    VpcOptions,
    Memory,
    IngressSettings,
)
from firebase_functions.manifest import EventTrigger, ManifestEndpoint
from firebase_functions.params import BoolParam, SecretParam, StringParam, IntParam
from firebase_functions.utils import CloudEvent

T = TypeVar("T")


@dataclass(frozen=True)
class Message(Generic[T]):
    """
    Wrapper around a Pub/Sub message.
    """

    message_id: str
    publish_time: dt.datetime
    data: Optional[str] = None
    attributes: Optional[dict[str, str]] = None
    ordering_key: Optional[str] = None

    @property
    def json(self) -> Optional[T]:
        try:
            if self.data is not None:
                return json.loads(base64.b64decode(self.data).decode("utf-8"))
            else:
                return None
        except Exception as e:
            raise Exception(
                f"Unable to parse Pub/Sub message data as JSON: {e}") from e

    def asdict(self) -> dict[str, Any]:
        dict_message: dict[str, Any] = {
            "message_id": self.message_id,
            "data": self.data,
            "publish_time": self.publish_time,
        }

        if self.attributes is not None:
            dict_message["attributes"] = self.attributes
        if self.ordering_key is not None:
            dict_message["ordering_key"] = self.ordering_key

        return dict_message


@dataclass(frozen=True)
class MessagePublishedData(Generic[T]):
    message: Message[T]
    subscription: str


def pubsub_wrap_handler(
    func: Callable[[CloudEvent[MessagePublishedData[T]]], None],
    raw: Union[ce.CloudEvent, dict],
) -> flask.Response:
    # If the call is coming from tests, the raw comes through as a dict,
    # therefore we need to convert it to a CloudEvent.
    if isinstance(raw, dict):
        raw = ce.from_json(json.dumps(raw))

    # pylint: disable=protected-access
    event_dict = {"data": raw.data, **raw._attributes}

    data = event_dict["data"]
    message_dict = data["message"]

    time = dt.datetime.strptime(
        event_dict["time"],
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )

    publish_time = dt.datetime.strptime(
        message_dict["publish_time"],
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )

    # Convert the UTC string into a datetime object
    event_dict["time"] = time
    message_dict["publish_time"] = publish_time

    # Pop unnecessary keys from the message data
    # (we get these keys from the snake case alternatives that are provided)
    message_dict.pop("messageId", None)
    message_dict.pop("publishTime", None)

    # `orderingKey` doesn't come with a snake case alternative,
    # there is no `ordering_key` in the raw request.
    ordering_key = message_dict.pop("orderingKey", None)

    message: MessagePublishedData = MessagePublishedData(
        message=Message(
            **message_dict,
            ordering_key=ordering_key,
        ),
        subscription=data["subscription"],
    )

    event_dict["data"] = message

    event: CloudEvent[MessagePublishedData] = CloudEvent(**event_dict)

    func(event)
    response = flask.jsonify(status=200)
    return response


def on_message_published(
    func: Callable[[CloudEvent[MessagePublishedData[T]]], None] = None,
    *,
    topic: str,
    region: Union[None, StringParam, str] = None,
    memory: Union[None, IntParam, Memory, Sentinel] = None,
    timeout_sec: Union[None, IntParam, int, Sentinel] = None,
    min_instances: Union[None, IntParam, int, Sentinel] = None,
    max_instances: Union[None, IntParam, int, Sentinel] = None,
    vpc: Union[None, VpcOptions, Sentinel] = None,
    vpc_connector_egress_settings: Union[None, VpcEgressSettings,
                                         Sentinel] = None,
    ingress: Union[None, IngressSettings, Sentinel] = None,
    service_account: Union[None, StringParam, str, Sentinel] = None,
    secrets: Union[None, List[StringParam], SecretParam, Sentinel] = None,
    retry: Union[None, bool, BoolParam] = None,
) -> Callable[[CloudEvent[MessagePublishedData[T]]], None]:
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
        vpc_connector_egress_settings=vpc_connector_egress_settings,
        ingress=ingress,
        service_account=service_account,
        secrets=secrets,
        retry=retry,
    )

    trigger = {} if pubsub_options is None else pubsub_options.metadata()

    def wrapper(func):

        @functools.wraps(func)
        def pubsub_view_func(data: ce.CloudEvent):
            return pubsub_wrap_handler(
                func=func,
                raw=data,
            )

        project = os.environ.get("GCLOUD_PROJECT")

        manifest = ManifestEndpoint(
            entryPoint=func.__name__,
            eventTrigger=EventTrigger(
                eventType="google.cloud.pubsub.topic.v1.messagePublished",
                eventFilters={
                    "topic": f"projects/{project}/topics/{topic}",
                },
                retry=pubsub_options.retry,
            ),
            region=pubsub_options.region,
            availableMemoryMb=pubsub_options.memory,
            timeoutSeconds=pubsub_options.timeout_sec,
            minInstances=pubsub_options.min_instances,
            maxInstances=pubsub_options.max_instances,
            vpc=pubsub_options.vpc,
            vpcConnectorEgressSettings=pubsub_options.
            vpc_connector_egress_settings,
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
