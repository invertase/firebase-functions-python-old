# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for Cloud Functions that are triggered by the Firebase Realtime Database."""
import functools
import os
import json
import datetime as dt
import base64

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    TypeVar,
    Union,
    Optional,
    Dict,
    Iterable,
    Sequence,
)

import flask
import cloudevents.http as ce

from firebase_functions import options
from firebase_functions import params
from firebase_functions.manifest import ManifestEndpoint, EventTrigger
from firebase_functions.utils import CloudEvent

# pylint: disable=unused-argument

T = TypeVar("T")


@dataclass(frozen=True)
class Change:
    """Perform change"""

    before: object
    after: object


@dataclass(frozen=True)
class DbEvent(CloudEvent[T]):
    """Make event"""

    firebase_database_host: str
    instance: str
    reference: str
    location: str
    params: Dict[str, str]


@dataclass(frozen=True)
class DbData(Generic[T]):
    """
    Wrapper around db data.
    """

    publish_time: dt.datetime
    data: Optional[str] = None
    ordering_key: Optional[str] = None
    attributes: Optional[dict[str, str]] = None

    @property
    def json(self) -> Optional[T]:
        """Verify json content"""
        try:
            if self.data is not None:
                return json.loads(base64.b64decode(self.data).decode("utf-8"))
            return None
        except Exception:
            raise Exception(f"Unable to parse data as JSON: {Exception}") from Exception

    def as_dict(self) -> dict[str, Any]:
        """Make dict"""
        dict_data: dict[str, Any] = {
            "data": self.data,
        }

        return dict_data


@dataclass(frozen=True)
class PublishedDbData(Generic[T]):
    """Publish Db Data"""

    data: DbData[T]
    subscription: str


def db_wrap_handler(
    func: Callable[[DbEvent[PublishedDbData[T]]], None],
    raw: Union[ce.CloudEvent, dict],
) -> flask.Response:
    """Database warp handler"""
    # If the call is coming from tests, the raw comes through as a dict,
    # therefore we need to convert it to a CloudEvent.
    if isinstance(raw, dict):
        raw = ce.from_json(json.dumps(raw))

    # pylint: disable=protected-access
    event_dict = {"data": raw.data, **raw._attributes}

    data = event_dict["data"]
    message_dict = data["data"]

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

    ordering_key = message_dict.pop("orderingKey", None)

    data2: PublishedDbData = PublishedDbData(
        data=DbData(
            **message_dict,
            ordering_key=ordering_key,
        ),
        subscription=message_dict["subscription"],
    )

    event_dict["data"] = data2

    event: DbEvent[PublishedDbData] = DbEvent(**event_dict)

    func(event)
    response = flask.jsonify(status=200)
    return response


def on_value_written(
    func: Callable[[DbEvent[PublishedDbData[T]]], None] = None,
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    concurrency: Union[None, int, options.Sentinel] = None,
    cpu: Union[None, int, str, options.Sentinel] = "gcf_gen1",
    vpc_connector_egress_settings: Union[None, options.VpcEgressSettings, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel] = None,
    retry: Union[None, bool, params.BoolParam] = None,
    labels: Union[str, params.Expression[str]] = None,
) -> Callable[[DbEvent[object]], None]:
    """Decorator for a function that can handle write to the Realtime Database.

    Parameters:
        func: function for the decorator
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture an "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the region
          of the Cloud Function.
        region: Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
          Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
          time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
          Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
          Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
          the default compute service account.
        secrets: The list of secrets which should be available to this function.

    To reset an attribute to factory default, use RESET_ATTRIBUTE
    """

    reference_options = options.ReferenceOptions(
        reference=reference,
        instance=instance,
        region=region,
        memory=memory,
        timeout_sec=timeout_sec,
        min_instances=min_instances,
        max_instances=max_instances,
        vpc=vpc,
        ingress=ingress,
        service_account=service_account,
        secrets=secrets,
        concurrency=concurrency,
        cpu=cpu,
        vpc_connector_egress_settings=vpc_connector_egress_settings,
        retry=retry,
        labels=labels,
    )

    trigger = {} if reference_options is None else reference_options.metadata()

    def wrapper(func):

        @functools.wraps(func)
        def db_view_func(data: ce.CloudEvent):
            return db_wrap_handler(
                func=func,
                raw=data,
            )

        project = os.environ.get("GCLOUD_PROJECT")

        manifest = ManifestEndpoint(
            entryPoint=func.__name__,
            eventTrigger=EventTrigger(
                eventType="google.firebase.database.ref.v1.written",
                # TODO path patterns should be handled
                # https://github.com/firebase/firebase-functions/blob/d592847517c93b9240fbd2598bdf3dfefdb85948/src/utilities/path-pattern.ts#L100
                # https://github.com/firebase/firebase-functions/blob/d592847517c93b9240fbd2598bdf3dfefdb85948/src/v2/providers/database.ts#L425-L432
                eventFilters={},
                eventFilterPathPatterns={
                    "ref": f"projects/{project}/reference/{reference}",
                },
                # TODO this seems to be false in all cases, see https://github.com/firebase/firebase-functions/blob/d592847517c93b9240fbd2598bdf3dfefdb85948/src/v2/providers/database.ts#L446
                retry=reference_options.retry,
            ),
            region=reference_options.region,
            availableMemoryMb=reference_options.memory,
            timeoutSeconds=reference_options.timeout_sec,
            minInstances=reference_options.min_instances,
            maxInstances=reference_options.max_instances,
            vpc=reference_options.vpc,
            vpcConnectorEgressSettings=reference_options.vpc_connector_egress_settings,
            ingressSettings=reference_options.ingress,
            serviceAccount=reference_options.service_account,
            secretEnvironmentVariables=reference_options.secrets,
        )

        db_view_func.__firebase_trigger__ = trigger
        db_view_func.__firebase_endpoint__ = manifest

        return db_view_func

    if func is None:
        return wrapper

    return wrapper(func)


def on_value_updated(
    func: Callable[[DbEvent[PublishedDbData[T]]], None] = None,
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    concurrency: Union[None, int, options.Sentinel] = None,
    cpu: Union[None, int, str, options.Sentinel] = "gcf_gen1",
    vpc_connector_egress_settings: Union[None, options.VpcEgressSettings, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel] = None,
    retry: Union[None, bool, params.BoolParam] = None,
    labels: Union[str, params.Expression[str]] = None,
) -> Callable[[DbEvent[object]], None]:
    """Decorator for a function that can handle an existing value changing in the Realtime Database.

    Parameters:
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture an "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the region
          of the Cloud Function.
        region: Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
          Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
          time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
          Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
          Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
          the default compute service account.
        secrets: The list of secrets which should be available to this function.

    To reset an attribute to factory default, use RESET_ATTRIBUTE
    """

    # test for empty parameters

    # reference_options = options.ReferenceOptions(
    #     reference=reference,
    #     instance=instance,
    #     region=region,
    #     memory=memory,
    #     timeout_sec=timeout_sec,
    #     min_instances=min_instances,
    #     max_instances=max_instances,
    #     vpc=vpc,
    #     ingress=ingress,
    #     service_account=service_account,
    #     secrets=secrets,
    #     concurrency=concurrency,
    #     cpu=cpu,
    #     vpc_connector_egress_settings=vpc_connector_egress_settings,
    #     retry=retry,
    #     labels=labels,
    # )

    # trigger = {} if reference_options is None else reference_options.metadata()

    def todo(event: DbEvent[Change]):
        pass

    return todo


def on_value_created(
    func: Callable[[DbEvent[PublishedDbData[T]]], None] = None,
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    concurrency: Union[None, int, options.Sentinel] = None,
    cpu: Union[None, int, str, options.Sentinel] = "gcf_gen1",
    vpc_connector_egress_settings: Union[None, options.VpcEgressSettings, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel] = None,
    retry: Union[None, bool, params.BoolParam] = None,
    labels: Union[str, params.Expression[str]] = None,
) -> Callable[[DbEvent[object]], None]:
    """Decorator for a function that can handle new values being added to the Realtime Database.

    Parameters:
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture an "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the region
          of the Cloud Function.
        region: Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
          Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
          time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
          Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
          Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
          the default compute service account.
        secrets: The list of secrets which should be available to this function.

    To reset an attribute to factory default, use RESET_ATTRIBUTE
    """

    reference_options = options.ReferenceOptions(
        reference=reference,
        instance=instance,
        region=region,
        memory=memory,
        timeout_sec=timeout_sec,
        min_instances=min_instances,
        max_instances=max_instances,
        vpc=vpc,
        ingress=ingress,
        service_account=service_account,
        secrets=secrets,
        concurrency=concurrency,
        cpu=cpu,
        vpc_connector_egress_settings=vpc_connector_egress_settings,
        retry=retry,
        labels=labels,
    )

    trigger = {} if reference_options is None else reference_options.metadata()

    def wrapper(func):

        @functools.wraps(func)
        def db_view_func(data: ce.CloudEvent):
            return db_wrap_handler(
                func=func,
                raw=data,
            )

        project = os.environ.get("GCLOUD_PROJECT")

        manifest = ManifestEndpoint(
            entryPoint=func.__name__,
            eventTrigger=EventTrigger(
                eventType="google.firebase.database.ref.v1.created",
                eventFilters={
                    "reference": f"projects/{project}/reference/{reference}",
                },
                retry=reference_options.retry,
            ),
            region=reference_options.region,
            availableMemoryMb=reference_options.memory,
            timeoutSeconds=reference_options.timeout_sec,
            minInstances=reference_options.min_instances,
            maxInstances=reference_options.max_instances,
            vpc=reference_options.vpc,
            vpcConnectorEgressSettings=reference_options.vpc_connector_egress_settings,
            ingressSettings=reference_options.ingress,
            serviceAccount=reference_options.service_account,
            secretEnvironmentVariables=reference_options.secrets,
        )

        db_view_func.__firebase_trigger__ = trigger
        db_view_func.__firebase_endpoint__ = manifest

        return db_view_func

    if func is None:
        return wrapper

    return wrapper(func)


def on_value_deleted(
    func: Callable[[DbEvent[PublishedDbData[T]]], None] = None,
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    concurrency: Union[None, int, options.Sentinel] = None,
    cpu: Union[None, int, str, options.Sentinel] = "gcf_gen1",
    vpc_connector_egress_settings: Union[None, options.VpcEgressSettings, options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel] = None,
    retry: Union[None, bool, params.BoolParam] = None,
    labels: Union[str, params.Expression[str]] = None,
) -> Callable[[DbEvent[object]], None]:
    """Decorator for a function that can handle values being deleted from the Realtime Database.

    Parameters:
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture an "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the region
          of the Cloud Function.
        region: Region to deploy functions. Defaults to us-central1.
        memory: MB to allocate to function. Defaults to Memory.MB_256
        timeout_sec: Seconds before a function fails with a timeout error.
          Defaults to 60s.
        min_instances: Count of function instances that should be reserved at all
          time. Instances will be billed while idle. Defaults to 0.
        max_instances: Maximum count of function instances that can be created.
          Defaults to 1000.
        vpc: Configuration for a virtual private cloud. Defaults to no VPC.
        ingress: Configuration for what IP addresses can invoke a function.
          Defaults to all traffic.
        service_account: The service account a function should run as. Defaults to
          the default compute service account.
        secrets: The list of secrets which should be available to this function.

    To reset an attribute to factory default, use RESET_ATTRIBUTE
    """

    # test for empty parameters

    # reference_options = options.ReferenceOptions(
    #     reference=reference,
    #     instance=instance,
    #     region=region,
    #     memory=memory,
    #     timeout_sec=timeout_sec,
    #     min_instances=min_instances,
    #     max_instances=max_instances,
    #     vpc=vpc,
    #     ingress=ingress,
    #     service_account=service_account,
    #     secrets=secrets,
    #     concurrency=concurrency,
    #     cpu=cpu,
    #     vpc_connector_egress_settings=vpc_connector_egress_settings,
    #     retry=retry,
    #     labels=labels,
    # )

    # trigger = {} if reference_options is None else reference_options.metadata()

    def todo(event: DbEvent[Change]):
        pass

    return todo
