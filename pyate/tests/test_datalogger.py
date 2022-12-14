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
        for group in range(num_groups):
            self.add_records(log, num_records, group)
            log.next_group()
        return log

    def add_records(self, datalog, num_records, group=1):
        for record_id in range(num_records):
            datalog["str1"] = f"g{group}r{record_id}a"
            datalog["str2"] = f"g{group}r{record_id}b"
            datalog["int1"] = group * 1000 + record_id
            datalog["float1"] = group + record_id / 1000.0
            datalog.next_record()

    def test_basic_usage(self):
        datalog = self.create_test_instance()
        self.assertIsInstance(datalog, DataLogger)

        self.assertEqual(datalog._data["str1"][0], "g0r0a")
        self.assertEqual(datalog._data["str2"][0], "g0r0b")
        self.assertEqual(datalog._data["int1"][2], 2)
        self.assertEqual(datalog._data["float1"][2], 0.002)

    def test_write(self):
        datalog = self.create_test_instance()
        self.assertRaises(FileNotFoundError, datalog.write_data, filename=None, format="csv")
        datalog.write_data(filename="unittest.csv", format="csv")
        # datalog.write_data(filename="unittest.hdf", format="hdf")
        datalog._logfile = "unittest.csv"
        datalog.write_data(format="csv")

    def test_autosave(self):
        datalog = self.create_test_instance(kwargs={"logfile": "unittest.log", "autosave": True})

    def test_autosave_then_write(self):
        datalog = self.create_test_instance(kwargs={"logfile": "unittest.log", "autosave": True})
        datalog.write_data()
        datalog.write_data(filename=None, format="csv")
        # datalog.write_data(filename="unittest.hdf", format="hdf")

    def test_addkey(self):
        datalog = self.create_test_instance()
        datalog["newkey"] = 42
        self.assertIsNone(datalog["str1"])
        self.assertIsNone(datalog["int1"])
        self.assertEqual(datalog["newkey"], 42)
        datalog.next_record()
        self.assertIsNone(datalog._data["str1"][-1])
        self.assertIsNone(datalog._data["int1"][-1])
        self.assertEqual(datalog._data["newkey"][-1], 42)

    def test_addkey_after_autosave(self):
        data = self.create_test_instance(kwargs={"logfile": "unittest.log", "autosave": True})
        self.assertRaises(KeyError, lambda: data.__setitem__("newkey", 42))

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
