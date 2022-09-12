"""Utils for Firebase Functions"""

from typing import Generic, TypeVar, Optional
from dataclasses import dataclass
import datetime as dt
from functions_framework import logging
from flask import Request

T = TypeVar("T")


@dataclass(frozen=True)
class CloudEvent(Generic[T]):
    """Create CloudEvent"""

    id: str
    datacontenttype: str
    specversion: str
    source: str
    type: str
    time: dt.datetime
    data: T


def valid_request(request: Request) -> bool:
    """Validate request"""
    if (valid_content(request) and valid_keys(request) and
            valid_type(request) and valid_body(request)):
        return True
    return False


def valid_body(request: Request) -> bool:
    """The body must not be empty."""
    if request.json is None:
        logging.warning("Request is missing body.")
        return False
    return True


def valid_type(request: Request) -> bool:
    """Make sure it's a POST."""
    if request.method != "POST":
        logging.warning("Request has invalid method.", request.method)
        return False
    return True


def valid_content(request: Request) -> bool:
    """Validate content"""
    content_type: Optional[str] = request.headers.get("Content-Type")

    if content_type is None:
        logging.warning("Request is missing Content-Type.", content_type)
        return False

    # If it has a charset, just ignore it for now.
    try:
        semi_colon = content_type.index(";")
        if semi_colon >= 0:
            content_type = content_type[0:semi_colon].strip()
    except ValueError:
        pass

    # Check that the Content-Type is JSON.
    if content_type != "application/json":
        logging.warning("Request has incorrect Content-Type.", content_type)
        return False

    # The body must have data.
    if request.json is None or request.json["data"] is None:
        # TODO should we check if data exists or not?
        logging.warning("Request body is missing data.", request.json)
        return False
    return True


def valid_keys(request: Request) -> bool:
    """Verify that the body does not have any extra fields."""
    assert request.json is not None
    extra_keys = {
        key: request.json[key] for key in request.json.keys() if key != "data"
    }
    if len(extra_keys) != 0:
        logging.warning(
            "Request body has extra fields: ",
            "".join(f"{key}: {value}," for (key, value) in extra_keys.items()),
        )
        return False
    return True
