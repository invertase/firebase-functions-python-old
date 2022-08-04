'''Module for params that can make Cloud Functions codebases generic.'''

import os
import abc
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence, Union, TypeVar, Generic, Optional

T = TypeVar('T', int, float, str, bool, Sequence[str])


class Input(Generic[T]):
  pass


@dataclass(frozen=True)
class SelectOption(Generic[T]):
  '''An option in a SelectInput or MultiSelectInput.

  Attributes:
      value: The value a parameter should have if this is selected.
  '''
  value: T
  label: Optional[str] = None


@dataclass(frozen=True)
class TextInput(Input[T]):
  example: Optional[T] = None
  validation_regex: Optional[str] = None
  validation_error_message: Optional[str] = None
  '''Input for this parameter should be with freeform text.

    Attributes:
        example: Sample which should be shown when prompting users for values.
        validation_regex: A regex which string input must match (str input only)
        validation_error_message: An error message which should be used when
          input fails to match validation_regex
    '''


@dataclass(frozen=True)
class SelectInput(Input[T]):
  options: Union[Sequence[T], Sequence[SelectOption[T]]]
  '''Input for this parameter should select from a predefined set of options.

    Attributes:
        options: Options from which a value can be chosen.
    '''


@dataclass(frozen=True)
class MultiselectInput(Input[Sequence[str]]):
  '''Input for this parameter should select from a predefined set of options.

  May only be used for ListParams


  Attributes:
      options: Options from which a value can be chosen.
  '''
  options: Union[Sequence[str], Sequence[SelectOption[str]]]


class CheckboxInput(Input[bool]):
  pass


class ResourceType(Enum):
  '''The type of resource that a picker should pick.'''
  STORAGE_BUCKET = 'storage.googleapis.com/Bucket'


@dataclass(frozen=True)
class ResourceInput(Input[str]):
  '''Input for this parameter should be with a resource picker UI.

  May only be used for StringParams.

  Attributes:
      resource_type: Kind of resource to pick
  '''
  resource_type: ResourceType


E = TypeVar('E', str, int, float, bool, Iterable[str])


class Expression(abc.ABC, Generic[E]):
  ''' An abstract base class for all expressions '''

  @abc.abstractmethod
  def expression(self) -> str:
    ''' Returns the CEL for this expression '''
    pass

  def __str__(self) -> str:
    ''' Returns the full expression in a {{ }} escape sequence '''
    return f'{{ {self.expression} }}'

  @abc.abstractmethod
  def value(self) -> E:
    pass


@dataclass(frozen=True)
class _IfThenExpression(Expression[E]):
  condition: Expression[bool]
  then_val: E
  else_val: E

  def value(self) -> E:
    if super().value():
      return self.then_val
    else:
      return self.else_val

  def expression(self) -> str:
    return f'{self.condition.expression} ? {self.then_val} : {self.else_val}'


@dataclass(frozen=True)
class BoolExpression(Expression[bool]):
  ''' A boolean expression supports boolean operators '''

  def expression(self) -> str:
    return 'bool'

  def value(self) -> bool:
    pass

  def then(self, then_val: E, else_val: E) -> Expression[E]:
    return _IfThenExpression(condition=self,
                             then_val=then_val,
                             else_val=else_val)


@dataclass(frozen=True)
class _EqualityExpression(BoolExpression):
  left: Expression[E]
  right: E

  def value(self) -> bool:
    return self.left.value() == self.right

  def expression(self) -> str:
    return f'{self.left.expression()} == {self.right}'


@dataclass(frozen=True)
class ComparableExpression(Expression[E]):
  ''' An expression which supports the equals method '''

  def __str__(self) -> str:
    ''' Returns the full expression in a {{ }} escape sequence '''
    return f'{{ {self.expression} }}'

  def expression(self) -> str:
    ''' Returns the CEL for this expression '''
    pass

  def value(self) -> E:
    pass

  def equals(self, val: E) -> BoolExpression:
    return _EqualityExpression(left=self, right=val)


@dataclass(frozen=True)
class _Param(Expression[E]):
  ''' A param is a declared dependency on an external value.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
      input_type: Method of prompting a user for this variable.
  '''
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Union[None, E, Expression[E]] = None
  input_type: Optional[Input[E]] = None

  def expression(self) -> str:
    return f'params.{self.name}'

  @abc.abstractmethod
  def value(self) -> E:
    pass


@dataclass(frozen=True)
class StringParam(_Param[str], ComparableExpression[str]):
  ''' A string parameter '''

  def value(self) -> str:
    if os.environ.get(self.name) is not None:
      return os.environ[self.name]
    elif isinstance(self.default, Expression):
      return self.default.value()
    elif self.default is not None:
      return self.default
    else:
      return str()


@dataclass(frozen=True)
class IntParam(_Param[int], ComparableExpression[int]):
  ''' An int parameter '''

  def value(self) -> int:
    if os.environ.get(self.name) is not None:
      return int(os.environ[self.name])
    elif isinstance(self.default, Expression):
      return self.default.value()
    elif self.default is not None:
      return self.default
    else:
      return int()


@dataclass(frozen=True)
class FloatParam(_Param[float], ComparableExpression[float]):
  ''' A float parameter '''

  def value(self) -> float:
    if os.environ.get(self.name) is not None:
      return float(os.environ[self.name])
    elif isinstance(self.default, Expression):
      return self.default.value()
    elif self.default is not None:
      return self.default
    else:
      return float()


@dataclass(frozen=True)
class ListParam(_Param[Iterable[str]]):
  ''' A list of strings parameter. '''

  def value(self) -> Iterable[str]:
    if os.environ.get(self.name) is not None:
      return os.environ[self.name].split(',')
    elif isinstance(self.default, Expression):
      return self.default.value()
    elif self.default is not None:
      return self.default
    else:
      return []


@dataclass(frozen=True)
class BoolParam(_Param[bool], BoolExpression):
  '''A boolean parameter '''

  def value(self) -> bool:
    env_value = os.environ.get(self.name)
    if env_value is not None:
      if (env_value.lower() in ['true', 't', '1', 'y', 'yes']):
        return True
      elif (env_value.lower() in ['false', 'f', '0', 'n', 'no']):
        return False
      else:
        raise ValueError(f'Invalid value for {self.name}: {env_value}')
    elif isinstance(self.default, Expression):
      return self.default.value()
    elif self.default is not None:
      return self.default
    else:
      return False


@dataclass(frozen=True)
class SecretParam:
  '''A string parameter bound to a cloud secret.

  A SecretParam is not an Expression; it cannot be used to configure the shape
  of a deployment.

  Attributes:
      name: The environment variable of this parameter. Must be upper case.
      label: A human readable name for this parameter.
      description: An optional description of this parameter.
      default: What value the parameter should have if not specified.
      immutable: Whether the value of this parameter can change between function
        deployments.
  '''
  name: str
  label: Optional[str] = None
  description: Optional[str] = None
  immutable: Optional[bool] = None
  default: Optional[str] = None

  def __str__(self):
    return f'{{{{ params.{self.name} }}}}'

  def value(self) -> str:
    '''Current value of this parameter.'''
    return str(os.environ.get(self.name) or self.default or '')


PROJECT_ID = StringParam('GCLOUD_PROJECT',
                         description='The active Firebase project')

STORAGE_BUCKET = StringParam(
    'STORAGE_BUCKET',
    description='The default Cloud Storage for Firebase bucket')

DATABASE_URL = StringParam(
    'DATABASE_URL',
    description='The Firebase project\'s default Realtime Database instance URL'
)

DATABASE_INSTANCE = StringParam(
    'DATABASE_INSTANCE',
    description='The Firebase projet\'s default Realtime Database instance name'
)

EXTENSION_ID = StringParam(
    'EXT_INSTANCE_ID',
    label='Extension instance ID',
    description='When a function is running as part of an extension, '
    'this is the unique identifier for the installed extension '
    'instance',
    default='')
