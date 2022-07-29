import asyncio
import dataclasses
from enum import Enum
import sys
from typing import Any, Callable, List
from yaml import load, dump

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response

from firebase_functions.manifest import CallableTrigger, HttpsTrigger, ManifestEndpoint, ManifestStack
from firebase_functions.utils import remove_undrscores

__ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE']


def asdict_factory(data) -> dict:

  def convert_value(obj):
    if isinstance(obj, Enum):
      return obj.value
    return obj

  return dict((k, convert_value(v)) for k, v in data)


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


def clean_nones(value) -> Any:
  if isinstance(value, list):
    return [clean_nones(x) for x in value if x is not None]
  elif isinstance(value, dict):
    return {
        key: clean_nones(val) for key, val in value.items() if val is not None
    }
  else:
    return value


def wrap_functions_yaml(triggers) -> Any:
  """Wrapper around each trigger in the user's codebase."""

  def wrapper():
    trigger_data = {}

    for name, trig in triggers.items():
      endpoint = add_entrypoint(
          name,
          clean_nones(
              dataclasses.asdict(trig.__firebase_endpoint__,
                                 dict_factory=asdict_factory)),
      )
      trigger_data.update(endpoint)

    result = ManifestStack(endpoints=trigger_data)
    response = dump(clean_nones(result.__dict__),
                    default_flow_style=False,
                    default_style=None)
    return Response(response, mimetype='text/yaml')

  return wrapper


def add_entrypoint(name, trigger) -> dict:
  """Add an entrypoint for a single function in the user's codebase."""
  endpoint = {}
  endpoint[remove_undrscores(name)] = trigger
  return endpoint


def is_http_trigger(endpoint: ManifestEndpoint) -> bool:
  # If the function's trigger contains `httpsTrigger` attribute,
  # then it's a https function.
  return endpoint.httpsTrigger is not None or isinstance(
      endpoint.httpsTrigger, HttpsTrigger)


def is_callable_trigger(endpoint: ManifestEndpoint) -> bool:
  # If the function's trigger contains `httpsTrigger` attribute,
  # then it's a https function.
  return endpoint.callableTrigger is not None or isinstance(
      endpoint.callableTrigger, CallableTrigger)


def is_pubsub_trigger(endpoint: ManifestEndpoint) -> bool:
  return endpoint.eventTrigger is not None and endpoint.eventTrigger.eventType == 'google.cloud.pubsub.topic.v1.messagePublished'


def serve_triggers(triggers: dict[str, Callable]) -> Flask:
  """
  Start serving all triggers provided by the user locally.
  Used by the generated `app` file upon deployment.
  """
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
  """Generate a specs `functions.yaml` file and serve it locally
  on the path `<host>:<port>/__/functions.yaml`."""

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
