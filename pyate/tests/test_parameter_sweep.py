'''
Created on May 10, 2019

@author: kyleh
'''
import unittest
from pyate import ParameterSweep

import numpy as np

class TestParameterSweep(unittest.TestCase):
    def constructSweep(self):
        pl = ParameterSweep()
        pl.setParameterRange('PA', range(1,4))
        pl.setParameterRange('PB', range(1,4))
        pl.setParameterRange('PC', np.arange(1.1,4.1))
        pl.setOrder(['PA', 'PB', 'PC'])
        
        pl.compute()
        
        self.pl = pl
    
    def testBasic(self):
        self.constructSweep()
        print(self.pl)  # pl.getList())
        
        while(not self.pl.end()):
            row = self.pl.getCurrentRow()
            print(row)

            if row == (2, 1, 2.1):
                print('Calling nextGroup()')
                self.pl.nextGroup()
            else:
                self.pl.next()
    
    def testSomething(self):
        self.constructSweep()
        print(self.pl['PC'])
        print(self.pl.get('PC'))
        print(self.pl.getLast('PC'))
        self.pl.next()
        print(self.pl['PC'])
        print(self.pl.get('PC'))
        print(self.pl.getLast('PC'))

        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()