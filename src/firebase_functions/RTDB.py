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

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Sequence, TypeVar, Union

from firebase_functions import options, params


T = TypeVar("T")


@dataclass(frozen=True)
class Change:
    before: object
    after: object


@dataclass(frozen=True)
class Event(event.CloudEvent[T]):
    firebase_database_host: str
    instance: str
    reference: str
    location: str
    params: Dict[str, str]


def on_value_written(
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[
        None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel
    ] = None,
) -> Callable[[Event[Change]], None]:
    """Decorator for a function that can handle a write to the Realtime Database.

    Parameters:
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture a "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the reigon
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

    def todo(event: Event[Change]):
        pass

    return todo


def on_value_updated(
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[
        None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel
    ] = None,
) -> Callable[[Event[Change]], None]:
    """Decorator for a function that can handle an existing value changing in the Realtime Database.

    Parameters:
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture a "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the reigon
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

    def todo(event: Event[Change]):
        pass

    return todo


def on_value_created(
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[
        None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel
    ] = None,
) -> Callable[[Event[object]], None]:
    """Decorator for a function that can handle new values being added to the Realtime Database.

    Parameters:
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture a "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the reigon
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

    def todo(event: Event[object]):
        pass

    return todo


def on_value_deleted(
    *,
    reference: Union[str, params.Expression[str]],
    instance: Union[None, str, params.Expression[str], options.Sentinel] = None,
    region: Union[None, str, params.Expression[str], options.Sentinel] = None,
    memory: Union[None, int, params.Expression[int], options.Sentinel] = None,
    timeout_sec: Union[None, int, params.Expression[int], options.Sentinel] = None,
    min_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    max_instances: Union[None, int, params.Expression[int], options.Sentinel] = None,
    vpc: Union[None, options.VpcOptions, options.Sentinel] = None,
    ingress: Union[None, options.IngressSettings, options.Sentinel] = None,
    service_account: Union[None, str, params.Expression[str], options.Sentinel] = None,
    secrets: Union[
        None, Sequence[str], params.Expression[Iterable[str]], options.Sentinel
    ] = None,
) -> Callable[[Event[object]], None]:
    """Decorator for a function that can handle values being deleted from the Realtime Database.

    Parameters:
        reference: The database path (ref) to listen on. Paths may include components
           with a wildcard (*) character to match a single component or (**) to
           match zero or more components. Wildcards can be captured by putting a
           capture statement in curly-brackets. For example, one can listen to and
           capture a "uid" variable with ref="users/{uid}" or ref="users/{uid=*}".
           To capture zero or more components, "=" syntax must be used. For, example,
           ref="notes/{path=**}".
        instance: The Realtime Database instance to listen to. The instance must
          be in the same region as the Cloud Function. Users may use "*" to match
          against a wildcard. Defaults to listening to all databases in the reigon
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

    def todo(event: Event[object]):
        pass

    return todo
