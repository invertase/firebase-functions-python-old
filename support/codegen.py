import importlib
import inspect
import sys

def get_exports(module_name):
  module = importlib.import_module(module_name)
  funcs = inspect.getmembers(module, inspect.isfunction)
  exports = {}
  for func in funcs:
    if hasattr(func[1], 'firebase_metadata'):
      exports[func[0]] = getattr(func[1], 'firebase_metadata')

  return exports


def generate_http_server(module_name, exports):
  print('import serving')
  print()
  print(f'import {module_name} as _alias')
  print()
  print('triggers = {}')
  for name in exports.keys():
    print(f'triggers["{name}"] = _alias.{name}')
  print()
  print('app = serving.serve_triggers(triggers)')
  print()


if __name__ == '__main__':
  args = sys.argv[1:]
  if len(args) != 1:
    print('Usage: python codegen.py <ModuleName>')
    sys.exit(1)

  exports = get_exports(args[0])
  if not exports:
    print('No exports in module')
    sys.exit(1)

  generate_http_server('sample', exports)
