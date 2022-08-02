import asyncio
import time
import yaml
import pytest

from urllib import request
from firebase_functions import codegen
from subprocess import Popen, run

import logging

LOGGER = logging.getLogger(__name__)

TEST_PORT = 8080

generated: dict = {}


def read_functions_yaml():

  _generated = request.urlopen(
      f"http://localhost:{TEST_PORT}/__/functions.yaml").read()

  global generated
  generated = yaml.safe_load(_generated)


@pytest.fixture(autouse=True, scope="module")
def codegen_fixture():
  # Generate the contract from the test functions. This will create a file named `autogenerated.py`
  # under the current directory's __pycache__.
  codegen.main('tests/functions/main.py')

  LOGGER.debug('fixure excuted')

  # Serve the admin from the generated code.
  Popen(
      [
          'gunicorn', '-b', f'localhost:{TEST_PORT}',
          '__pycache__.autogenerated:admin'
      ],
      cwd='tests/functions/',
  )

  # A little delay to ensure the localserver has started.
  time.sleep(5)

  # Parse and store the result in memory for tests.
  read_functions_yaml()

  # Cleanup by quitting the admin server.
  Popen(
      ['pkill', '-f', 'gunicorn'],
      cwd='tests/functions/',
  ).wait()

  yield


def test_manifest_spec_version():
  '''Test if the version in the manifest is v1alpha1'''
  generated["specVersion"] == "v1alpha1"


def test_memory_is_int():
  '''Test if the memory is an integer'''
  for function in generated["endpoints"].values():
    assert isinstance(function["availableMemoryMb"],
                      int) or function["availableMemoryMb"] is None


def test_entry_point_equals_function_name():
  '''Test if the entry point equals the function name as is, whatever case the user uses, camel, snake or kabab.'''
  for function in generated["endpoints"].values():
    assert function["entryPoint"] == 'http_callable_function'
    break


def test_endpoint_name_is_clean():
  '''Test if the name of the endpoint in the endpoints map is clean of underscores/hyphens and all small case.'''
  for function in generated["endpoints"].values():
    assert function["entryPoint"] == 'http_callable_function'
    break


def test_use_default_is_null():
  '''Test if USE_DEFAULT value will result in a null value.'''
  for function in generated["endpoints"].values():
    if (function["entryPoint"] == 'http_request_function'):
      # nulls in yaml are parsed to Nones in python.
      assert function["maxInstances"] is None
      break


def test_option_key_does_not_exist():
  '''Test if option key doesn't exists if the user didn't assign it.'''
  for function in generated["endpoints"].values():
    if (function["entryPoint"] == 'http_call_function'):
      with pytest.raises(KeyError):
        assert function["maxInstances"] is int
      break
