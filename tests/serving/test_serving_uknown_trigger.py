import functools
import json

import pytest
import yaml
from firebase_functions.manifest import ManifestEndpoint
from firebase_functions.serving import serve_admin, serve_triggers


def uknown_trigger(func):

  @functools.wraps(func)
  def view_func():
    return 'Hello World!'

  view_func.__firebase_endpoint__ = ManifestEndpoint(
      entryPoint=view_func.__name__)
  view_func.__firebase_trigger__ = {}

  return view_func


@uknown_trigger
def uknown_function():
  pass


triggers = {}

triggers['uknown_function'] = uknown_function


def test_spec_unkown():
  with serve_admin(triggers=triggers).test_client() as client:
    res = client.get('/__/functions.yaml')
    res = yaml.safe_load(res.get_data())
    assert 'uknownfunction' not in res['endpoints']


def test_unkown_trigger_type():
  with pytest.raises(ValueError):
    with serve_triggers(triggers=triggers).test_client() as client:
      client.post(
          '/unknown_function',
          data=json.dumps({'data': 'bar'}),
          headers={'Authorization': 'bar'},
          content_type='application/json',
      )
