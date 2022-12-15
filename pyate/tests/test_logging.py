"""
Created on May 10, 2019

@author: kyleh
"""

import logging
import unittest

from pyate import logging_tools

class TestLogger(unittest.TestCase):
    def test_basicConfig(self):
        logging_tools.basicConfig(level_file=logging.DEBUG, level_console=logging.WARNING)
        logging.getLogger(__name__).warning("Test WARNING")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
