import unittest
from pyate import visawrapper


class TestVisawrapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("setUpClass")
        cls.rm = visawrapper.ResourceManager()
        cls.is_class_setup = True

    def test_add_resource(self):
        self.rm.addResource("resource_name_01", "VISA_ADDR")
        self.assertIn("resource_name_01", self.rm.resources)

    def test_get_resource(self):
        self.assertEqual(self.rm.getResource("resource_name_01"), "VISA_ADDR")

    def test_get_resource_missing(self):
        self.assertRaises(KeyError, self.rm.getResource, "non_existant")
