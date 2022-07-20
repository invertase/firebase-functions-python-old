""" Errors and exceptions in this package. """

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, TypedDict


class CanonicalErrorCodeName(Enum):
  """The canonical error code name for a given error code."""
  OK = 'OK'
  CANCELLED = 'CANCELLED'
  UNKNOWN = 'UNKNOWN'
  INVALID_ARGUMENT = 'INVALID_ARGUMENT'
  DEADLINE_EXCEEDED = 'DEADLINE_EXCEEDED'
  NOT_FOUND = 'NOT_FOUND'
  ALREADY_EXISTS = 'ALREADY_EXISTS'
  PERMISSION_DENIED = 'PERMISSION_DENIED'
  UNAUTHENTICATED = 'UNAUTHENTICATED'
  RESOURCE_EXHAUSTED = 'RESOURCE_EXHAUSTED'
  FAILED_PRECONDITION = 'FAILED_PRECONDITION'
  ABORTED = 'ABORTED'
  OUT_OF_RANGE = 'OUT_OF_RANGE'
  UNIMPLEMENTED = 'UNIMPLEMENTED'
  INTERNAL = 'INTERNAL'
  UNAVAILABLE = 'UNAVAILABLE'
  DATA_LOSS = 'DATA_LOSS'


@dataclass(frozen=True)
class FunctionsErrorCode():
  """The error code for a given error."""
  ok: str = 'ok'
  cancelled: str = 'cancelled'
  unknown: str = 'unknown'
  invalid_argument: str = 'invalid-argument'
  deadline_exceeded: str = 'deadline-exceeded'
  not_found: str = 'not-found'
  already_exists: str = 'already-exists'
  permission_denied: str = 'permission-denied'
  unauthenticated: str = 'unauthenticated'
  resource_exhausted: str = 'resource-exhausted'
  failed_precondition: str = 'failed-precondition'
  aborted: str = 'aborted'
  out_of_range: str = 'out-of-range'
  unimplemented: str = 'unimplemented'
  internal: str = 'internal'
  unavailable: str = 'unavailable'
  data_loss: str = 'data-loss'


class HttpErrorCode():
  canonical_name: CanonicalErrorCodeName
  status: int


error_code_map = {
    FunctionsErrorCode.ok:
        HttpErrorCode(CanonicalErrorCodeName.OK, 200),
    FunctionsErrorCode.cancelled:
        HttpErrorCode(CanonicalErrorCodeName.CANCELLED, 499),
    FunctionsErrorCode.unknown:
        HttpErrorCode(CanonicalErrorCodeName.UNKNOWN, 500),
    FunctionsErrorCode.invalid_argument:
        HttpErrorCode(CanonicalErrorCodeName.INVALID_ARGUMENT, 400),
    FunctionsErrorCode.deadline_exceeded:
        HttpErrorCode(CanonicalErrorCodeName.DEADLINE_EXCEEDED, 504),
    FunctionsErrorCode.not_found:
        HttpErrorCode(CanonicalErrorCodeName.NOT_FOUND, 404),
    FunctionsErrorCode.already_exists:
        HttpErrorCode(CanonicalErrorCodeName.ALREADY_EXISTS, 409),
    FunctionsErrorCode.permission_denied:
        HttpErrorCode(CanonicalErrorCodeName.PERMISSION_DENIED, 403),
    FunctionsErrorCode.unauthenticated:
        HttpErrorCode(CanonicalErrorCodeName.UNAUTHENTICATED, 401),
}


class HttpErrorWireFormat(TypedDict):
  details: Optional[Any]
  status: CanonicalErrorCodeName
  message: str


class HttpsError(Exception):
  """
  A standard error code that will be returned to the client. This also
  determines the HTTP status code of the response, as defined in code.proto.
  """

  def __init__(
      self,
      code: FunctionsErrorCode,
      message: str,
      details: Optional[Any] = None,
  ):
    self.code = code
    self.message = message
    self.details = details
    self.http_error_code = error_code_map[code]

    super().__init__()

  def __str__(self):
    return self.code.canonical_name.value

  def to_dict(self):
    return HttpErrorWireFormat(
        details={self.details} if self.details is not None else {},
        status=self.http_error_code.canonical_name,
        message=self.message,
    )
