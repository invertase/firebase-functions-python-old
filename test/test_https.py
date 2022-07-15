"""
Https unit tests.
"""
import unittest

from firebase_functions.https import OnRequestOptions
from firebase_functions.options import IngressSettings, Memory


class TestHttpsMethods(unittest.TestCase):
  """
  Tests for Https methods.
  """

  def test_on_request_defaults(self):
    """
    Testing the default values in OnRequestOptions.
    """
    opts = OnRequestOptions()
    self.assertEqual(opts.region[0], "us-central1",
                     "Default region is us-central1")
    self.assertEqual(opts.memory[0], Memory.MB_256, "Default memory is 256 MB")
    self.assertEqual(opts.ingress[0], IngressSettings.ALLOW_ALL)
    self.assertEqual(opts.max_instances[0], 1000)
    self.assertEqual(opts.min_instances[0], 0)
    self.assertEqual(opts.timeout_sec[0], 60)


if __name__ == "__main__":
  unittest.main()
