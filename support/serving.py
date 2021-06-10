import yaml

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response


_ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]


def wrap_http_trigger(trig):
  def wrapper():
    return trig(request)
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
        key: clean_nones(val)
        for key, val in value.items()
        if val is not None
      }
    else:
      return value


def wrap_backend_yaml(triggers):
  def wrapper():
    trigger_data = [ trig.firebase_metadata for trig in triggers.values() ]
    result = {'cloudFunctions': trigger_data}
    response = yaml.dump(clean_nones(result))
    return Response(response, mimetype='text/yaml')
  return wrapper


def is_http_trigger(metadata):
  trigger = metadata['trigger']
  return trigger.get('eventType') is None


def is_pubsub_trigger(metadata):
  trigger = metadata['trigger']
  return trigger.get('eventType') == 'google.cloud.pubsub.topic.v1.messagePublished'


def serve_triggers(triggers):
  app = Flask(__name__)

  for name, trig in triggers.items():
    metadata = trig.firebase_metadata
    if is_http_trigger(metadata):
      app.add_url_rule(
        f'/{name}', endpoint=name, view_func=wrap_http_trigger(trig), methods=_ALLOWED_METHODS)
      print(f'Serving http trigger {name} at /{name}')
    elif is_pubsub_trigger(metadata):
      app.add_url_rule(
        f'/{name}', endpoint=name, view_func=wrap_pubsub_trigger(trig), methods=['POST'])
      print(f'Serving pubsub trigger {name} at /{name}')
    else:
      raise ValueError('Unknown trigger type')

  app.add_url_rule('/backend.yaml', endpoint='backend.json', view_func=wrap_backend_yaml(triggers))
  return app
