"""
Created on May 10, 2019

@author: kyleh
"""
import unittest
import sys
import os

print(sys.path)
print(os.getcwd())
from pyate import DataLogger

# from pyate.datamanagement import DataLogger


class TestDataLogger(unittest.TestCase):
    def create_test_instance(self, num_groups=3, num_records=5, args=[], kwargs={}):
        log = DataLogger(*args, **kwargs)
        for g in range(num_groups):
            self.add_records(log, num_records)
            log.next_group()
        return log

    def add_records(self, datalog, num_records, multiplier=1):
        for counter in range(num_records):
            datalog["stra"] = "a{:d}".format(counter * multiplier)
            datalog["strb"] = "b{:d}".format(counter * multiplier)
            datalog["inta"] = counter * multiplier
            datalog["floata"] = counter * multiplier + 0.1
            datalog.next_record()

    def test_basic_usage(self):
        data = self.create_test_instance()
        self.assertIsInstance(data, DataLogger)

    def test_autosave(self):
        data = self.create_test_instance(kwargs={'logfile':'unittest.log', 'autosave':True})
        
    def test_autosave(self):
        data = self.create_test_instance(kwargs={'logfile':'unittest.log', 'autosave':True})
        data["newkey"] = 42

    def test_print_trend_int(self):
        datalog = DataLogger()
        self.add_records(datalog, 5, 1)
        print("Num Records: {:d}".format(datalog.num_records()))
        print(datalog.trend("inta", 2))

        self.add_records(datalog, 5, 2)
        print("Num Records: {:d}".format(datalog.num_records()))
        print(datalog.trend("inta", 2))

        self.add_records(datalog, 5, 3)
        print("Num Records: {:d}".format(datalog.num_records()))
        print(datalog.trend("inta", 2))

    def test_print_trend_float(self):
        datalog = DataLogger()

        for g in range(1, 4):
            for k in range(5):
                datalog["f"] = k ** g
                datalog.next_record()
                print("Num Records: {:d}".format(datalog.num_records()))
                print(datalog.get_data("f", slice(None, None)))
                print("Slope: {:g}".format(datalog.trend("f", 3)))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
