'''
IntParam unit tests.
'''
import os
import src.firebase_functions.params as params


def test_int_param_value():
  '''
  Testing if int param correctly returns a value.
  '''
  os.environ['int_value_test'] = '123'
  param = params.IntParam('int_value_test')
  assert param.value() == 123


def test_int_param_empty_default():
  '''
  Testing if int param defaults to empty int if no value and no default.
  '''
  param = params.IntParam('int_default_test')
  assert param.value() == int()


def test_int_param_default():
  '''
  Testing if int param defaults to provided default value.
  '''
  param = params.IntParam(
      'int_default_test',
      # TODO this isn't showing type issues when not an int
      default=456,
  )
  assert param.value() == 456
