"""
Created on May 10, 2019

@author: kyleh
"""
import unittest
from pyate import ParameterSweep

import numpy as np


class TestParameterSweep(unittest.TestCase):
    def construct_sweep(self):
        pl = ParameterSweep()
        pl.set_parameter_range("PA", range(1, 4))
        pl.set_parameter_range("PB", range(1, 4))
        pl.set_parameter_range("PC", np.arange(1.1, 4.1))
        pl.set_order(["PA", "PB", "PC"])

        pl.compute()

        self.pl = pl

    def test_basic(self):
        self.construct_sweep()
        print(self.pl)  # pl.getList())

        while not self.pl.end():
            row = self.pl.get_current_row()
            print(row)

            if row == (2, 1, 2.1):
                print("Calling next_group()")
                self.pl.next_group()
            else:
                self.pl.next()

    def test_something(self):
        self.construct_sweep()
        print(self.pl["PC"])
        print(self.pl.get("PC"))
        print(self.pl.get_last("PC"))
        self.pl.next()
        print(self.pl["PC"])
        print(self.pl.get("PC"))
        print(self.pl.get_last("PC"))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
