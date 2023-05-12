"""
Created on May 19, 2023

@author: kyle.hershberger@gmail.com
"""

import unittest

from pyate.instrument import InstrumentManager


class TestPowerSupply2400(unittest.TestCase):
    def setUpClass(cls):
        print("setUpClass")
        cls.instr = InstrumentManager.create_instrument("GPIB::24::INSTR")

    def test_ident(self):
        print(self.instr.identity)

    def test_voltage(self):
        self.instr.set_voltage(1.23)
        self.assertAlmostEqual(self.instr.get_voltage(), 1.23)
        self.instr.set_output_state(True)
        self.assertTrue(self.instr.get_output_state())
        self.assertAlmostEqual(self.instr.meas_voltage(), 1.23)
        self.instr.set_output_state(False)
        self.assertFalse(self.instr.get_output_state())

    def test_current(self):
        self.instr.set_current(0.0123)
        self.assertAlmostEqual(self.instr.get_current(), 0.012)
        self.instr.set_output_state(True)
        self.assertTrue(self.instr.get_output_state())
        self.assertAlmostEqual(self.instr.meas_current(), 0.012)
        self.instr.set_output_state(False)
        self.assertFalse(self.instr.get_output_state())
