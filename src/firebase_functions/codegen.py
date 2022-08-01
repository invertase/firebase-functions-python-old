"""
Code generator.
"""
import os
import sys
import inspect

from importlib import util


def get_module_name(file_path: str):
  basename = os.path.basename(file_path)
  return os.path.splitext(basename)[0]


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


def generate_http_server(module_name: str, exports: dict, file_path: str):
  """Generate the HTTP server code."""

  triggers = ''
  for name in exports.keys():
    triggers += f'triggers["{name}"] = _alias.{name}\n'

  server = f'''
"""APP SERVER"""

# This is a generated file, do not edit.

from firebase_functions import serving

import {module_name} as _alias

triggers = {{}}

{triggers}
  
app = serving.serve_triggers(triggers)
admin = serving.serve_admin(triggers)

  '''
  os.makedirs(os.path.dirname(file_path) + '/__pycache__', exist_ok=True)
  with open(f'{os.path.dirname(file_path)}/__pycache__/autogenerated.py',
            'w+') as f:
    f.write(server)


def main(*args):
  _file_path = args[0]
  _exports = get_exports(_file_path)
  if not _exports:
    print('No exports in module')
    sys.exit(1)

  mod_name = get_module_name(_file_path)
  generate_http_server(mod_name, _exports, _file_path)


if __name__ == '__main__':
  args = sys.argv[1:]
  if len(args) != 1:
    print('Usage: python codegen.py <PathToModule>')
    sys.exit(1)

  main(args)
