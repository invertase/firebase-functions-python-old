'''
Module used to serve Firebase functions locally and remotely.
'''

import asyncio
import dataclasses
import sys
import os
import inspect

from importlib import util

from enum import Enum
from typing import Any, Callable
from yaml import dump

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response

from firebase_functions.manifest import CallableTrigger, HttpsTrigger, ManifestEndpoint, Manifest
from firebase_functions.options import Sentinel

__ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE']


def get_module_name(file_path: str) -> str:
  '''Get the module name from the file path.'''
  basename = os.path.basename(file_path)
  return os.path.splitext(basename)[0]


def get_triggers():
  spec = util.spec_from_file_location('main', 'main.py')
  if spec is not None and spec.loader is not None:
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
  else:
    # TODO: raise friendly error
    raise Exception('Could not find main.py')
  funcs = inspect.getmembers(module, inspect.isfunction)
  triggers = {}
  for entry in funcs:
    if hasattr(entry[1], '__firebase_trigger__'):
      name = entry[1].__firebase_endpoint__.entryPoint
      triggers[name] = entry[1]
  return triggers


def get_exports(file_path: str):
  modname = get_module_name(file_path)
  spec = util.spec_from_file_location(modname, file_path)
  if spec is not None and spec.loader is not None:
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

  funcs = inspect.getmembers(module, inspect.isfunction)
  exports = {}
  for func in funcs:
    if hasattr(func[1], '__firebase_trigger__'):
      exports[func[0]] = getattr(func[1], '__firebase_trigger__')

  return exports


def wrap_http_trigger(trig: Callable) -> Callable:

  def wrapper():

    try:
      return trig(request)
    except TypeError:
      return trig(request, Response())

  return wrapper


def wrap_pubsub_trigger(trig):

  def wrapper():
    data = request.get_json(force=True)
    trig(data)
    return jsonify({})

  return wrapper


def clean_nones_and_set_defult(data) -> dict:

  def convert_value(obj):
    if isinstance(obj, Enum):
      return obj.value
    elif isinstance(obj, Sentinel):
      return None

    return obj

  return dict((k, convert_value(v)) for k, v in data if v is not None)


def is_valid_trigger(trigger: ManifestEndpoint) -> bool:
  return is_http_trigger(trigger) or is_callable_trigger(
      trigger) or is_pubsub_trigger(trigger)


def triggers_as_yaml(triggers: dict) -> str:
  '''Convert a list of triggers to a YAML string.'''

  endpoints: dict[str, ManifestEndpoint] = {}

  for name, trig in triggers.items():

    trigger = trig.__firebase_endpoint__

    if not is_valid_trigger(trigger):
      continue
    else:
      # Lowercase the name of the function and replace '_' to support CF naming.
      endpoints[name.replace('_', '').lower()] = trigger

  manifest_yaml = dump(
      dataclasses.asdict(
          Manifest(endpoints=endpoints),
          dict_factory=clean_nones_and_set_defult,
      ))

  return manifest_yaml


def wrap_functions_yaml(triggers: dict) -> Any:
  '''Wrapper around each trigger in the user's codebase.'''

  def wrapper() -> Response:
    triggers_yaml = triggers_as_yaml(triggers)
    return Response(triggers_yaml, mimetype='text/yaml')

  return wrapper


def is_http_trigger(endpoint: ManifestEndpoint) -> bool:
  ''' If the function's trigger contains `httpsTrigger` attribute,
  then it's a https function. '''
  return (endpoint.httpsTrigger is not None or
          endpoint.httpsTrigger is HttpsTrigger)


def is_callable_trigger(endpoint: ManifestEndpoint) -> bool:
  ''' If the function's trigger contains `httpsTrigger` attribute,
  then it's a https function. '''
  return (endpoint.callableTrigger is not None or
          endpoint.callableTrigger is CallableTrigger)


def is_pubsub_trigger(endpoint: ManifestEndpoint) -> bool:
  return endpoint.eventTrigger is not None and endpoint.eventTrigger[
      'eventType'] == 'google.cloud.pubsub.topic.v1.messagePublished'


def serve_triggers(triggers: dict[str, Callable]) -> Flask:
  '''
  Start serving all triggers provided by the user locally.
  Used by the generated `app` file upon deployment.
  '''
  app = Flask(__name__)

  for name, trigger in triggers.items():

    endpoint = getattr(trigger, '__firebase_endpoint__')

    if is_http_trigger(endpoint) or is_callable_trigger(endpoint):
      app.add_url_rule(
          f'/{name}',
          endpoint=name,
          view_func=wrap_http_trigger(trigger),
          methods=__ALLOWED_METHODS,
      )
    elif is_pubsub_trigger(endpoint):
      app.add_url_rule(
          f'/{name}',
          endpoint=name,
          view_func=wrap_pubsub_trigger(trigger),
          methods=['POST'],
      )
    else:
      raise ValueError('Unknown trigger type!')

  return app


def quitquitquit():
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  asyncio.get_event_loop().call_later(1, sys.exit)
  return Response(status=200)


def serve_admin(triggers) -> Flask:
  '''Generate a specs `functions.yaml` file and serve it locally
  on the path `<host>:<port>/__/functions.yaml`.'''

  app = Flask(__name__)
  app.add_url_rule(
      '/__/functions.yaml',
      endpoint='functions.yaml',
      view_func=wrap_functions_yaml(triggers),
  )

  app.add_url_rule(
      '/__/quitquitquit',
      endpoint='quitquitquit',
      view_func=quitquitquit,
  )

  return app


def main():
  triggers = get_triggers()
  if os.environ['ADMIN_PORT'] is not None:
    serve_admin(triggers).run(port=int(os.environ['ADMIN_PORT']))
  if os.environ['PORT'] is not None:
    serve_triggers(triggers).run(port=int(os.environ['PORT']))


if __name__ == '__main__':
  main()
