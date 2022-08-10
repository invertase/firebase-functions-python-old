"""StringParam unit tests."""
import os
from firebase_functions import params


def test_string_param_value():
    """Testing if string param correctly returns a value."""
    os.environ["string_value_test"] = "string_test"
    assert params.StringParam("string_value_test").value() == "string_test",\
        'Failure, prams value != "string_test"'


def test_string_param_empty_default():
    """Testing if string param defaults to empty string if no value and no default."""
    assert params.StringParam("string_default_test").value() == str(),\
        "Failure, prams value is not a string"


def test_string_param_default():
    """Testing if string param defaults to provided default value."""
    assert (params.StringParam("string_default_test", default="string_override_default").value()
            == "string_override_default"), \
        'Failure, prams default value != "string_override_default"'
