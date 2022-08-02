'''
FloatParam unit tests.
'''
import os
import firebase_functions.params as params


def test_float_param_value():
  '''
  Testing if float param correctly returns a value.
  '''
  os.environ['float_value_test'] = '123.456'
  param = params.FloatParam('float_value_test')
  assert param.value() == 123.456


def test_float_param_empty_default():
  '''
  Testing if float param defaults to empty float if no value and no default.
  '''
  param = params.FloatParam('float_default_test')
  assert param.value() == float()


def test_float_param_default():
  '''
  Testing if float param defaults to provided default value.
  '''
  param = params.FloatParam(
      'float_default_test',
      default=float(456.789),
  )
  assert param.value() == 456.789
