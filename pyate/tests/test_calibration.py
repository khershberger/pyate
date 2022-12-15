"""
Created on Dec 13, 2022

@author: kyleh
"""
import unittest

import numpy as np
import numpy.testing as nptest

from pyate.calibration import Calibration as Cal


class TestCalibration(unittest.TestCase):
    def create_calibration(self, functions=None):
        cal = Cal()

        cal.set_indep_var("x")

        if functions is None:
            functions = {"eq": lambda x: x, "lin": lambda x: 1 + 2 * x, "sq": lambda x: x ** 2}

        # Generate data
        x = np.arange(1.0, 10.0, 1.0)
        for name, fcn in functions.items():
            y = fcn(x)
            # Create cal table
            cal.set_table(name, x, y)

        return cal

    def test_create_calibration(self):
        cal = self.create_calibration()

    def test_get(self):
        cal = self.create_calibration()
        self.assertAlmostEqual(cal.get("eq", 3), 3)

    def test_interp(self):
        cal = self.create_calibration()
        self.assertAlmostEqual(cal.get("lin", 3.5), 1 + 2 * 3.5)

    def test_save_calibration(self):
        cal = self.create_calibration()
        cal.write("unittest_cal.csv")

    def test_read_calibration(self):
        cal1 = self.create_calibration()
        cal2 = Cal()
        cal2.read("unittest_cal.csv")

        self.assertEqual(list(cal1.tables.keys()), list(cal2.tables.keys()))
        for name in cal1.tables.keys():
            nptest.assert_array_almost_equal(cal1.tables[name].x, cal2.tables[name].x)
            nptest.assert_array_almost_equal(cal1.tables[name].y, cal2.tables[name].y)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
