'''
BoolParam unit tests.
'''
import os

import pytest
import firebase_functions.params as params


def test_bool_param_value_true():
  '''
  Testing if bool param correctly returns a truth value.
  '''
  valid_truthy_values = ['true', 't', '1', 'y', 'yes']
  for value in valid_truthy_values:
    os.environ['bool_value_test'] = value
    param = params.BoolParam('bool_value_test')
    assert param.value() == True


def test_bool_param_value_false():
  '''
  Testing if bool param correctly returns a false value.
  '''
  valid_falsey_values = ['false', 'f', '0', 'n', 'no']
  for value in valid_falsey_values:
    os.environ['bool_value_test'] = value
    param = params.BoolParam('bool_value_test')
    assert param.value() == False


def test_bool_param_value_error():
  '''
  Testing if bool param throws a value error if invalid value.
  '''
  with pytest.raises(ValueError):
    os.environ['bool_value_test'] = 'bad_value'
    param = params.BoolParam('bool_value_test')
    param.value()


def test_bool_param_empty_default():
  '''
  Testing if bool param defaults to False if no value and no default.
  '''
  param = params.BoolParam('bool_default_test')
  print(param.value())
  assert param.value() == False


def test_bool_param_default():
  '''
  Testing if bool param defaults to provided default value.
  '''
  param = params.BoolParam(
      'bool_default_test',
      # TODO accepts any value for default, but should only accept True or False
      default=False,
  )
  assert param.value() == False
  param = params.BoolParam(
      'bool_default_test',
      # TODO accepts any value for default, but should only accept True or False
      default=True,
  )
  assert param.value() == True
