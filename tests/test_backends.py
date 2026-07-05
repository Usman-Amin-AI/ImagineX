import unittest

from modules import backends


class TestBackends(unittest.TestCase):
    def test_default_backend_is_sdxl(self):
        self.assertEqual(backends.get_backend_name(), 'sdxl')

    def test_backend_can_be_switched(self):
        backends.set_backend('flux')
        self.assertEqual(backends.get_backend_name(), 'flux')
        backends.set_backend('sdxl')
        self.assertEqual(backends.get_backend_name(), 'sdxl')

    def test_unknown_backend_falls_back_to_sdxl(self):
        backends.set_backend('unknown')
        self.assertEqual(backends.get_backend_name(), 'sdxl')
