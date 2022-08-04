'''
StringParam unit tests.
'''
import os
import firebase_functions.params as params


def test_string_param_value():
  '''
  Testing if string param correctly returns a value.
  '''
  os.environ['string_value_test'] = 'string_test'
  param = params.StringParam('string_value_test')
  assert param.value() == 'string_test'


def test_string_param_empty_default():
  '''
  Testing if string param defaults to empty string if no value and no default.
  '''
  param = params.StringParam('string_default_test')
  assert param.value() == ''


def test_string_param_default():
  '''
  Testing if string param defaults to provided default value.
  '''
  param = params.StringParam('string_default_test',
                             default='string_overriden_default')
  assert param.value() == 'string_overriden_default'
