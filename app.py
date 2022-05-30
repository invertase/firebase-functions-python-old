"""APP SERVER"""

# This is a generated file, do not edit.

from firebase_functions import serving

import sample as _alias

triggers = {}
triggers["http_callable_function"] = _alias.http_callable_function
triggers["http_request_function"] = _alias.http_request_function

app = serving.serve_triggers(triggers)

admin = serving.serve_admin(triggers)

