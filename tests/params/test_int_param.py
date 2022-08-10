"""IntParam unit tests."""
import os
from firebase_functions import params


def test_int_param_value():
    """Testing if int param correctly returns a value."""
    os.environ["int_value_test"] = "123"
    assert params.IntParam("int_value_test").value() == 123, "Failure, prams value != 123"


def test_int_param_empty_default():
    """Testing if int param defaults to empty int if no value and no default."""
    assert params.IntParam("int_default_test").value() == int(), "Failure, prams value is not int"


def test_int_param_default():
    """Testing if int param defaults to provided default value."""
    # TODO this isn't showing type issues when not an int
    assert params.IntParam("int_default_test", default=456).value() == 456,\
        "Failure, prams defult value != 456"
