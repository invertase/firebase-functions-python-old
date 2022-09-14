"""Utils for Firebase Functions"""

import re
from typing import Generic, Literal, TypeVar, Optional
from dataclasses import dataclass
import datetime as dt
from functions_framework import logging
from flask import Request

T = TypeVar("T")

WILDCARD_CAPTURE_REGEX = r"{[^/{}]+}"


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


SegmentName = Literal["segment", "single-capture", "multi-capture"]


def trim_param(param: str) -> str:
    """Trim params"""
    param_no_braces = param[1:-1]
    if "=" in param_no_braces:
        return param_no_braces[0:param_no_braces.index("=")]
    return param_no_braces


class PathSegment(Generic[T]):
    name: SegmentName
    value: str
    trimmed: str

    def is_single_segment_wildcard(self) -> bool:
        pass

    def is_multi_segment_wildcard(self) -> bool:
        pass


class Segment(PathSegment):
    """Segment of a path"""

    name: SegmentName = "segment"

    def __init__(self, value: str) -> None:
        super().__init__()
        self.trimmed = value

    def is_single_segment_wildcard(self) -> bool:
        return "*" in self.trimmed and not self.is_multi_segment_wildcard()

    def is_multi_segment_wildcard(self) -> bool:
        return "**" in self.trimmed


class SingleCaptureSegment(PathSegment):
    """Segment of a path with a single capture. e.g. {*}"""
    name: SegmentName = "single-capture"

    def __init__(self, value: str) -> None:
        super().__init__()
        self.trimmed = trim_param(value)

    def is_single_segment_wildcard(self) -> bool:
        return True

    def is_multi_segment_wildcard(self) -> bool:
        return False


class MultiCaptureSegment(PathSegment):
    """Segment of a path with a multi capture. e.g. {**}"""
    name: SegmentName = "multi-capture"

    def __init__(self, value: str) -> None:
        super().__init__()
        self.trimmed = trim_param(value)

    def is_single_segment_wildcard(self) -> bool:
        return False

    def is_multi_segment_wildcard(self) -> bool:
        return True


class PathPattern:
    """Path pattern"""

    raw: str
    segments: list[PathSegment]

    def __init__(self, raw: str):
        self.raw = raw
        self.segments = []
        self.init_path_segments(raw)

    def get_value(self) -> str:
        return self.raw

    def has_wildcards(self) -> bool:
        return any(segment.is_multi_segment_wildcard() or segment.is_multi_segment_wildcard()
                   for segment in self.segments)

    def has_captures(self) -> bool:
        return any(segment.name in ("single-capture", "multi-capture") for segment in self.segments)

    def init_path_segments(self, raw: str) -> None:
        parts = path_parts(raw)
        for part in parts:
            segment: PathSegment
            capture = re.findall(WILDCARD_CAPTURE_REGEX, part)
            if capture and len(capture) == 1:
                segment = MultiCaptureSegment(part) if "**" in part else SingleCaptureSegment(part)
            else:
                segment = Segment(part)
            self.segments.append(segment)

    def extract_matches(self, path: str) -> dict[str, str]:
        """Extract matches"""
        matches: dict[str, str] = {}
        if not self.has_captures():
            return matches
        path_segments = path_parts(path)
        for i, part in enumerate(path_segments):
            segment = self.segments[i]
            if segment.is_single_segment_wildcard():
                matches[segment.trimmed] = part
            elif segment.is_multi_segment_wildcard():
                matches[segment.trimmed] = "/".join(path_segments[i:i + 1])
        return matches


def path_parts(path: str) -> list[str]:
    """Path parts"""
    if path is None or path == "" or path == "/":
        return []
    return normalize_path(path).split("/")


def normalize_path(path: str) -> str:
    """Normalize path"""

    if path is None:
        return ""
    return re.sub(r"^/|/$", "", path)


def join_path(path: str) -> str:
    """Join path"""
    return "/".join(path_parts(path))


def valid_request(request: Request) -> bool:
    """Validate request"""
    if (valid_content(request) and valid_keys(request) and valid_type(request) and
            valid_body(request)):
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
    extra_keys = {key: request.json[key] for key in request.json.keys() if key != "data"}
    if len(extra_keys) != 0:
        logging.warning(
            "Request body has extra fields: ",
            "".join(f"{key}: {value}," for (key, value) in extra_keys.items()),
        )
        return False
    return True
