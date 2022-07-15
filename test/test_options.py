"""
Https unit tests.
"""
import unittest

from firebase_functions.options import GlobalOptions, HttpsOptions, set_global_options, _global_options


class TestGlobalOptions(unittest.TestCase):
  """
  Tests for Global Options.
  """

  def test_set_global_options(self):
    """
    Testing if setting the global options actually change the values.
    """
    set_global_options()
    test_global_options = GlobalOptions()

    self.assertEqual(
        _global_options.options, test_global_options,
        "The global options should be the same as the test global options.")

    set_global_options(max_instances=1)

    self.assertNotEqual(
        _global_options.options, test_global_options,
        """ After setting the global options,
        the global options should not be the same as the test global options."""
    )

  def test_https_options(self):
    """
    Testing if setting the global options actually change the values.
    """
    set_global_options()
    https_options = HttpsOptions()

    self.assertEqual(_global_options.options, https_options,
                     """ HttpsOptions is an instance of GlobalOptions """)

    https_options = HttpsOptions(max_instances=1)

    self.assertNotEqual(
        _global_options.options, https_options,
        """ HttpsOptions is not equal to the global options """)

    set_global_options(max_instances=1)

    self.assertEqual(_global_options.options, https_options,
                     """ HttpsOptions is equal to the global options """)


if __name__ == "__main__":
  unittest.main()
