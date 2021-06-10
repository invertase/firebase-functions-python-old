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

* `functions.py` contains the experimental Functions SDK for Python.

* `sample.py` contains some sample user code written using the Functions SDK.

* Run the codegen tool to generate an entrypoint. Save the output to a new
  `app.py` file.

 ```
 python codegen.py sample > app.py
 ```

 * Start the Flask server to serve the generated entrypoint.

  ```
  flask run
  ```

* To trigger the HTTP function:

 ```
 curl localhost:5000/http_function
 ```

* To trigger the PubSub function:

 ```
 curl -X POST -d '{"uid": "alice"}' localhost:5000/pubsub_function
 ```

* To get the discovery yaml (currently served on the same port):

 ```
 curl localhost:5000/backend.yaml
 ```
