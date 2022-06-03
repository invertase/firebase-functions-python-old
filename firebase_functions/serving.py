import json
from typing import Callable
import yaml

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response

from firebase_functions.manifest import ManifestEndpoint, ManifestStack

_ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]


def wrap_http_trigger(trig: Callable):

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
    return jsonify(dict())

  return wrapper


def clean_nones(value):
  if isinstance(value, list):
    return [clean_nones(x) for x in value if x is not None]
  elif isinstance(value, dict):
    return {
        key: clean_nones(val) for key, val in value.items() if val is not None
    }
  else:
    return value


def wrap_functions_yaml(triggers):

  def wrapper():
    trigger_data = [
        add_entrypoint(
            name,
            clean_nones(trig.__endpoint__.__dict__),
        ) for name, trig in triggers.items()
    ]
    result = ManifestStack(endpoints=trigger_data)
    response = yaml.dump(clean_nones(result.__dict__))
    return Response(response, mimetype='text/yaml')

  return wrapper


def to_camel_case(snake_str):
  components = snake_str.split('_')
  # We capitalize the first letter of each component except the first one
  # with the 'title' method and join them together.
  return components[0] + ''.join(x.title() for x in components[1:])


def add_entrypoint(name, trigger):
  endpoint = {}
  endpoint[name] = trigger
  return endpoint


def is_http_trigger(trigger):
  # If the function's trigger contains `httpsTrigger` attribute,
  # then it's a https function.
  return trigger.get('httpsTrigger') is not None


def is_pubsub_trigger(metadata):
  trigger = metadata['trigger']
  return trigger.get('eventType') == 'google.pubsub.topic.publish'


def serve_triggers(triggers: list[Callable]):
  """Start serving all triggers provided by the user locally.
  Used by the generated `app` file upon deployment."""
  app = Flask(__name__)

  for name, trig in triggers.items():

    trigger = getattr(trig, 'trigger')

    if is_http_trigger(trigger):
      app.add_url_rule(
          f'/{name}',
          endpoint=name,
          view_func=wrap_http_trigger(trig),
          methods=_ALLOWED_METHODS,
      )
    # elif is_pubsub_trigger(metadata):
    #   app.add_url_rule(f'/{name}',
    #                    endpoint=name,
    #                    view_func=wrap_pubsub_trigger(trig),
    #                    methods=['POST'])
    else:
      raise ValueError('Unknown trigger type!')

  return app


def serve_admin(triggers):
  """Generate a specs `functions.yaml` file and serve it locally
  on the path `<host>:<port>/__/functions.yaml`."""

  app = Flask(__name__)
  app.add_url_rule(
      '/__/functions.yaml',
      endpoint='functions.yaml',
      view_func=wrap_functions_yaml(triggers),
  )
  return app
