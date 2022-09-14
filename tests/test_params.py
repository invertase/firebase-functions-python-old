"""BoolParam unit tests."""
from os import environ

import pytest
from firebase_functions import params


class TestBoolParams:
    """BoolParam unit tests."""

    def test_bool_param_value_true_or_false(self):
        """Testing if bool params correctly returns a true or false value."""
        for value_true, value_false in zip(["true", "t", "1", "y", "yes"],
                                           ["false", "f", "0", "n", "no"]):
            environ["bool_value_test"] = value_true
            assert (params.BoolParam("bool_value_test").value() is
                    True), "Failure, params returned False"
            environ["bool_value_test"] = value_false
            assert (params.BoolParam("bool_value_test").value() is
                    False), "Failure, params returned True"

    def test_bool_param_value_error(self):
        """Testing if bool params throws a value error if invalid value."""
        with pytest.raises(ValueError):
            environ["bool_value_test"] = "bad_value"
            params.BoolParam("bool_value_test").value()

    def test_bool_param_empty_default(self):
        """Testing if bool params defaults to False if no value and no default."""
        assert (params.BoolParam("bool_default_test").value() is
                False), "Failure, params returned True"

    def test_bool_param_default(self):
        """Testing if bool params defaults to provided default value."""
        assert (params.BoolParam("bool_default_test", default=False).value() is
                False), "Failure, params returned True"
        assert (params.BoolParam("bool_default_test", default=True).value() is
                True), "Failure, params returned False"


class TesFloatParams:
    """FloatParam unit tests."""

    def test_float_param_value(self):
        """Testing if float params correctly returns a value."""
        environ["float_value_test"] = "123.456"
        assert params.FloatParam("float_value_test").value() == 123.456, \
            "Failure, params value != 123.456"

    def test_float_param_empty_default(self):
        """Testing if float params defaults to empty float if no value and no default."""
        assert params.FloatParam("float_default_test").value() == float(), \
            "Failure, params value is not float"

    def test_float_param_default(self):
        """Testing if float param defaults to provided default value."""
        assert params.FloatParam("float_default_test", default=float(456.789)).value() == 456.789, \
            "Failure, params default value != 456.789"


class TestIntParams:
    """IntParam unit tests."""

    def test_int_param_value(self):
        """Testing if int param correctly returns a value."""
        environ["int_value_test"] = "123"
        assert params.IntParam(
            "int_value_test").value() == 123, "Failure, params value != 123"

    def test_int_param_empty_default(self):
        """Testing if int param defaults to empty int if no value and no default."""
        assert params.IntParam("int_default_test").value() == int(
        ), "Failure, params value is not int"

    def test_int_param_default(self):
        """Testing if int param defaults to provided default value."""
        assert params.IntParam("int_default_test", default=456).value() == 456, \
            "Failure, params default value != 456"


class TestStringParams:
    """StringParam unit tests."""

    def test_string_param_value(self):
        """Testing if string param correctly returns a value."""
        environ["string_value_test"] = "string_test"
        assert params.StringParam("string_value_test").value() == "string_test", \
            'Failure, params value != "string_test"'

    def test_string_param_empty_default(self):
        """Testing if string param defaults to empty string if no value and no default."""
        assert params.StringParam("string_default_test").value() == str(), \
            "Failure, params value is not a string"

    def test_string_param_default(self):
        """Testing if string param defaults to provided default value."""
        assert (params.StringParam("string_default_test", default="string_override_default").value()
                == "string_override_default"), \
            'Failure, params default value != "string_override_default"'
