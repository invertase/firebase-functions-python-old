"""Module for params that can make Cloud Functions codebases generic."""
import os

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Union, TypeVar, Generic, Optional

T = TypeVar("T", int, float, str, Tuple[str])


class Input(Generic[T]):
  pass


@dataclass(frozen=True)
class SelectOption(Generic[T]):
  """An option in a SelectInput or MultiSelectInput.

  Attributes:
      value: The value a parameter should have if this is selected.
  """
  value: T
  label: Optional[str] = None


@dataclass(frozen=True)
class TextInput(Input[T]):
  example: Optional[T] = None
  validation_regex: Optional[str] = None
  validation_error_message: Optional[str] = None
  """Input for this parameter should be with freeform text.

    Attributes:
        example: Sample which should be shown when prompting users for values.
        validation_regex: A regex which string input must match (str input only)
        validation_error_message: An error message which should be used when
          input fails to match validation_regex
    """


@dataclass(frozen=True)
class SelectInput(Input[T]):
  options: Union[List[T], List[SelectOption[T]]]
  """Input for this parameter should select from a predefined set of options.

    Attributes:
        options: Options from which a value can be chosen.
    """


@dataclass(frozen=True)
class MultiselectInput(Input[List[str]]):
  """Input for this parameter should select from a predefined set of options.

  May only be used for ListParams


  Attributes:
      options: Options from which a value can be chosen.
  """
  options: Union[List[str], List[SelectOption[str]]]


class CheckboxInput(Input[bool]):
  pass


class ResourceType(Enum):
  """The type of resource that a picker should pick."""
  STORAGE_BUCKET = "storage.googleapis.com/Bucket"


@dataclass(frozen=True)
class ResourceInput(Input[str]):
  """Input for this parameter should be with a resource picker UI.

  May only be used for StringParams.

  Attributes:
      resource_type: Kind of resource to pick
  """
  resource_type: ResourceType


class _StringExpression:
  pass


@dataclass(frozen=True)
class StringParam(_StringExpression):
  """A string parameter.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
      input_type: Method of prompting a user for this variable. Defaults to
        TextInput[str]
  """
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Union[None, str, _StringExpression] = None
  input_type: Optional[Input[str]] = None

  def __str__(self):
    return f"{{{{ params.{self.name} }}}}"

  @property
  def value(self) -> str:
    """Current value of this parameter."""
    return os.environ.get(self.name) or self.default or ""


class _IntExpression:
  pass


@dataclass(frozen=True)
class IntParam(_IntExpression):
  """An int parameter.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
      input_type: Method of prompting a user for this variable. Defaults to
        TextInput[int]
  """
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Optional[Union[None, int, _IntExpression]] = None
  input_type: Optional[Input[int]] = None

  def __str__(self):
    return f"{{{{ params.{self.name} }}}}"

  @property
  def value(self) -> int:
    """Current value of this parameter."""
    return int(os.environ.get(self.name) or self.default or 0)


class _FloatExpression:
  pass


@dataclass(frozen=True)
class FloatParam(_FloatExpression):
  """A float parameter.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
      input_type: Method of prompting a user for this variable. Defaults to
        TextInput[float]
  """
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Union[None, int, _FloatExpression] = None
  input_type: Optional[Input[float]] = None

  def __str__(self):
    return f"{{{{ params.{self.name} }}}}"

  @property
  def value(self) -> float:
    """Current value of this parameter."""
    pass


class _ListExpression:
  pass


@dataclass(frozen=True)
class ListParam(_ListExpression):
  """A list of string parameters.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
      input_type: Method of prompting a user for this variable.
  """
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Optional[Union[None, List[str], _ListExpression]] = None
  input_type: Union[None, Input[List[str]], List[str]] = None

  def __str__(self):
    return f"{{{{ params.{self.name} }}}}"

  @property
  def value(self) -> List[str]:
    """Current value of this parameter."""
    # TODO is split by coma right?
    return os.environ.get(self.name).split(",") or self.default or []


class _BoolExpression:
  pass


@dataclass(frozen=True)
class BoolParam(_BoolExpression):
  """A boolean parameter.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
      input_type: Method of prompting a user for this variable. Defaults to
        TextInput[float]
  """
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Optional[Union[None, bool, _BoolExpression]] = None
  input_type: Optional[Input[bool]] = None

  def __str__(self):
    return f"{{{{ params.{self.name} }}}}"

  @property
  def value(self) -> bool:
    """Current value of this parameter."""
    return bool(os.environ.get(self.name) or self.default)


@dataclass(frozen=True)
class SecretParam:
  """A string parameter bound to a cloud secret.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
  """
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Optional[str] = None

  def __str__(self):
    return f"{{{{ params.{self.name} }}}}"

  @property
  def value(self) -> str:
    """Current value of this parameter."""
    return str(os.environ.get(self.name) or self.default or "")


PROJECT_ID = StringParam("GCLOUD_PROJECT",
                         description="The active Firebase project")

STORAGE_BUCKET = StringParam(
    "STORAGE_BUCKET",
    description="The default Cloud Storage for Firebase bucket")

DATABASE_URL = StringParam(
    "DATABASE_URL",
    description="The Firebase project's default Realtime Database instance URL")

DATABASE_INSTANCE = StringParam(
    "DATABASE_INSTANCE",
    description="The Firebase projet's default Realtime Database instance name")

EXTENSION_ID = StringParam(
    "EXT_INSTANCE_ID",
    label="Extension instance ID",
    description="When a function is running as part of an extension, "
    "this is the unique identifier for the installed extension "
    "instance",
    default="")
