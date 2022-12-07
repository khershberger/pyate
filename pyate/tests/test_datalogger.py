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
    def createTestIntance(self):
        inst = DataLogger()

        numGroups = 3
        numRecords = 5
        mult = 2

        for g in range(numGroups):
            for k in range(numRecords):
                inst["stra"] = "a{:d}".format(k * g)
                inst["strb"] = "b{:d}".format(k * g)
                inst["inta"] = k * g
                inst["floata"] = k * g + 0.1
                inst.nextRecord()
            inst.nextGroup()

        return inst

    def addRecords(self, datalog, n, m):
        for k in range(n):
            datalog["stra"] = "a{:d}".format(k * m)
            datalog["strb"] = "b{:d}".format(k * m)
            datalog["inta"] = k * m
            datalog["floata"] = k * m + 0.1
            datalog.nextRecord()

    def testName1(self):
        data = self.createTestIntance()
        self.assertIsInstance(data, DataLogger)

    def testPrintTrendInt(self):
        datalog = DataLogger()
        self.addRecords(datalog, 5, 1)
        print("Num Records: {:d}".format(datalog.numRecords()))
        print(datalog.trend("inta", 2))

        self.addRecords(datalog, 5, 2)
        print("Num Records: {:d}".format(datalog.numRecords()))
        print(datalog.trend("inta", 2))

        self.addRecords(datalog, 5, 3)
        print("Num Records: {:d}".format(datalog.numRecords()))
        print(datalog.trend("inta", 2))

    def testPrintTrendFloat(self):
        datalog = DataLogger()

        for g in range(1, 4):
            for k in range(5):
                datalog["f"] = k ** g
                datalog.nextRecord()
                print("Num Records: {:d}".format(datalog.numRecords()))
                print(datalog.getData("f", slice(None, None)))
                print("Slope: {:g}".format(datalog.trend("f", 3)))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
