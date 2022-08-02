'''
Module used to serve Firebase functions locally and remotely.
'''

import asyncio
import dataclasses
import sys

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


def asdict_factory(data) -> dict:

  def convert_value(obj):
    if isinstance(obj, Enum):
      return obj.value
    elif isinstance(obj, Sentinel):
      return None

    return obj

  return dict((k, convert_value(v)) for k, v in data if v is not None)


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
    trig(data, {})
    return jsonify({})

  return wrapper


def clean_nones_and_set_default(value: dict) -> Any:
  '''Remove all `None` values from the generated manifest, and set Sentinels to None.'''

  result: dict = {}

  for k, v in value.items():
    if v is Sentinel:
      result[k] = None
    elif v is None:
      continue
    else:
      result[k] = value

  return result


def wrap_functions_yaml(triggers: dict) -> Any:
  '''Wrapper around each trigger in the user's codebase.'''

  def wrapper():
    endpoints = {}
    for name, trigger in triggers.items():
      # Lowercase the name of the function and replace '_' to support CF naming.
      endpoints[name.replace('_', '').lower()] = dataclasses.asdict(
          trigger.__firebase_endpoint__,
          dict_factory=asdict_factory,
      )

    manifest = Manifest(endpoints=endpoints)
    response = dump(dataclasses.asdict(
        manifest,
        dict_factory=asdict_factory,
    ))
    return Response(response, mimetype='text/yaml')

  return wrapper


def is_http_trigger(endpoint: ManifestEndpoint) -> bool:
  # If the function's trigger contains `httpsTrigger` attribute,
  # then it's a https function.
  return (endpoint.httpsTrigger is not None or
          endpoint.httpsTrigger is HttpsTrigger)


def is_callable_trigger(endpoint: ManifestEndpoint) -> bool:
  # If the function's trigger contains `httpsTrigger` attribute,
  # then it's a https function.
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
