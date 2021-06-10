import importlib
import importlib.util
import inspect
import os
import sys


def get_exports(file_path):
  basename = os.path.basename(file_path)
  modname = os.path.splitext(basename)[0]
  spec = importlib.util.spec_from_file_location(modname, file_path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)

  funcs = inspect.getmembers(module, inspect.isfunction)
  exports = {}
  for func in funcs:
    if hasattr(func[1], 'firebase_metadata'):
      exports[func[0]] = getattr(func[1], 'firebase_metadata')

  return exports


def generate_http_server(module_name, exports):
  print('from firebase_functions import serving')
  print()
  print(f'import {module_name} as _alias')
  print()
  print('triggers = {}')
  for name in exports.keys():
    print(f'triggers["{name}"] = _alias.{name}')
  print()
  print('app = serving.serve_triggers(triggers)')
  print()
  print('backend_yaml = serving.serve_backend_yaml(triggers)')
  print()


if __name__ == '__main__':
  args = sys.argv[1:]
  if len(args) != 1:
    print('Usage: python codegen.py <PathToModule>')
    sys.exit(1)

  exports = get_exports(args[0])
  if not exports:
    print('No exports in module')
    sys.exit(1)

  generate_http_server('sample', exports)
