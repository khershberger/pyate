import unittest
from pyate import instrument


class TestInstrument(unittest.TestCase):
    def setUp(self):
        print("setUp")
        self.IM = instrument.InstrumentManager()
        self.is_setup = True

    def test_something(self):
        available_instruments = self.IM.get_available_instruments()

    def test_register_instrument(self):
        self.IM.register_instrument(['model1'], instrument.Instrument)
        self.assertIn('model1', self.IM._models)
        self.assertNotIn('model2', self.IM._models)