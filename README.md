# Requirements

* Python 3.6 or higher
* Pip (usually installed alongside Python)

# Setup

* Install `virtualenv` if you already haven't. Makes it a lot easier to keep
  Python dependencies and modules isolated from the rest of your environment.

  ```
  pip install --user virtualenv

  # After this you might have to add the virtualenv binary
  # to your $PATH.
  ```

* Create and activate a new virtual environment.

 ```
 virtualenv -p python3 py3
 source py3/bin/activate
 ```

* Install dependencies.

 ```
 pip install -r requirements.txt
 ```

# Running the example

* `firebase_functions` contains the experimental Functions SDK for Python.

* `sample.py` contains some sample user code written using the Functions SDK.

* Run the codegen tool to generate an entrypoint. Save the output to a new
  `app.py` file.

 ```
 python ./firebase_functions/codegen.py ./sample.py > app.py
 ```

 * Start the Flask server to serve the generated entrypoint.

  ```
  gunicorn -b :8080 app:app
  ```

* Start a separate server to serve the `backend.yaml`.

  ```
  gunicorn -b :8081 app:backend_yaml
  ```

* To trigger the HTTP function:

 ```
 curl localhost:8080/http_function
 ```

* To trigger the PubSub function:

 ```
 curl -X POST -d '{"uid": "alice"}' localhost:8080/pubsub_function
 ```

* To get the discovery yaml (currently served on the same port):

 ```
 curl localhost:8081/backend.yaml
 ```
