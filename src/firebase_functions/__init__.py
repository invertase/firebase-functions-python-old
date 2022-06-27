from dataclasses import dataclass
import datetime
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class CloudEvent(Generic[T]):
  specversion: str
  source: str
  subject: str
  type: str
  time: datetime
  data: T