"""BoolParam unit tests."""
from os import environ

import pytest
from firebase_functions import params


def test_bool_param_value_true_or_false():
    """Testing if bool params correctly returns a truth or false value."""
    for value_true, value_false in zip(
        ["true", "t", "1", "y", "yes"], ["false", "f", "0", "n", "no"]
    ):
        environ["bool_value_test"] = value_true
        assert (
            params.BoolParam("bool_value_test").value() is True
        ), "Failure, prams returned False"
        environ["bool_value_test"] = value_false
        assert (
            params.BoolParam("bool_value_test").value() is False
        ), "Failure, prams returned True"


def test_bool_param_value_error():
    """Testing if bool params throws a value error if invalid value."""
    with pytest.raises(ValueError):
        environ["bool_value_test"] = "bad_value"
        params.BoolParam("bool_value_test").value()


def test_bool_param_empty_default():
    """Testing if bool params defaults to False if no value and no default."""
    assert (
        params.BoolParam("bool_default_test").value() is False
    ), "Failure, prams returned True"


def test_bool_param_default():
    """Testing if bool params defaults to provided default value."""
    assert (
        # TODO accepts any value for default, but should only accept True or False
        params.BoolParam("bool_default_test", default=False).value() is False
    ), "Failure, prams returned True"
    assert (
        # TODO accepts any value for default, but should only accept True or False
        params.BoolParam("bool_default_test", default=True).value() is True
    ), "Failure, prams returned False"
