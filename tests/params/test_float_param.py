"""FloatParam unit tests."""
import os
from firebase_functions import params


def test_float_param_value():
    """Testing if float params correctly returns a value."""
    os.environ["float_value_test"] = "123.456"
    assert params.FloatParam("float_value_test").value() == 123.456,\
        "Failure, prams value != 123.456"


def test_float_param_empty_default():
    """Testing if float params defaults to empty float if no value and no default."""
    assert params.FloatParam("float_default_test").value() == float(),\
        "Failure, prams value is not float"


def test_float_param_default():
    """Testing if float param defaults to provided default value."""
    assert params.FloatParam("float_default_test", default=float(456.789)).value() == 456.789,\
        "Failure, prams default value != 456.789"
