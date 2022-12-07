import unittest
from pyate import instrument

class TestInstrument(unittest.TestCase):
    def setUp(self):
        print("setUp")
        self.IM = instrument.InstrumentManager()
        self.is_setup = True

    def test_something(self):
        available_instruments = self.IM.getAvailableInstruments()
