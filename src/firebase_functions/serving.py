import dataclasses
from enum import Enum
from typing import Callable
import yaml

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response

from firebase_functions.manifest import ManifestEndpoint, ManifestStack

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


def clean_nones(value) -> any:
  if isinstance(value, list):
    return [clean_nones(x) for x in value if x is not None]
  elif isinstance(value, dict):
    return {
        key: clean_nones(val) for key, val in value.items() if val is not None
    }
  else:
    return value


def wrap_functions_yaml(triggers) -> any:
  """Wrapper around each trigger in the user's codebase."""

  def wrapper():
    trigger_data = [
        add_entrypoint(
            name,
            clean_nones(
                dataclasses.asdict(trig.__endpoint__,
                                   dict_factory=asdict_factory)),
        ) for name, trig in triggers.items()
    ]
    result = ManifestStack(endpoints=trigger_data)
    response = yaml.dump(clean_nones(result.__dict__))
    return Response(response, mimetype='text/yaml')

  return wrapper


def add_entrypoint(name, trigger) -> dict:
  """Add an entrypoint for a single function in the user's codebase."""
  endpoint = {}
  endpoint[name] = trigger
  return endpoint


def is_http_trigger(trigger: ManifestEndpoint) -> bool:
  # If the function's trigger contains `httpsTrigger` attribute,
  # then it's a https function.
  return trigger.httpsTrigger is not None or trigger.httpsTrigger != {}


def is_pubsub_trigger(trigger: ManifestEndpoint) -> bool:
  return trigger.eventTrigger['eventType'] == 'google.pubsub.topic.publish'


def serve_triggers(triggers: list[Callable]) -> Flask:
  """Start serving all triggers provided by the user locally.
  Used by the generated `app` file upon deployment."""
  app = Flask(__name__)

  for name, trig in triggers.items():

    trigger = getattr(trig, '__endpoint__')

    if is_http_trigger(trigger):
      app.add_url_rule(
          f'/{name}',
          endpoint=name,
          view_func=wrap_http_trigger(trig),
          methods=__ALLOWED_METHODS,
      )
    elif is_pubsub_trigger(trigger):
      app.add_url_rule(f'/{name}',
                       endpoint=name,
                       view_func=wrap_pubsub_trigger(trig),
                       methods=['POST'])
    else:
      raise ValueError('Unknown trigger type!')

  return app


def serve_admin(triggers) -> Flask:
  """Generate a specs `functions.yaml` file and serve it locally
  on the path `<host>:<port>/__/functions.yaml`."""

  app = Flask(__name__)
  app.add_url_rule(
      '/__/functions.yaml',
      endpoint='functions.yaml',
      view_func=wrap_functions_yaml(triggers),
  )
  return app
