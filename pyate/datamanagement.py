'''
Created on May 9, 2019

@author: kyleh
'''

from datetime import datetime
import numpy as np
from scipy.stats import linregress
import pandas as pd
from itertools import product

class DataLogger(object):
    '''
    classdocs
    '''

    def __init__(self, logFile=None):
        '''
        Constructor
        '''
        
        self._logfile = logFile
        self._recordStartTime = datetime.now()
        self._recordStopTime = None
        self._data = {}
        self._recordCurrent = {}
        self._recordNum = 0
        self._numRecords = 0
        
        self._groupNum = 0
        self._groupStart = 0
        
        self._columnOrder = []
        
        self._valueMissing = float('nan')
        
    def __getitem__(self, key):
        return self._recordCurrent[key]
    
    def __setitem__(self, key, val):
        self._recordCurrent[key] = val

    def getData(self, key, s=None, includecurrent=False):
        if key not in self._data:
            v = []
        else:
            v = self._data[key][s]
        
        if includecurrent:
            v += [self._recordCurrent.get(key, None)]

        return v
        
    def trend(self, key, pts, includecurrent=False):
        # Get all the data in the current group
        v = self.getData(key, slice(self._groupStart,None), includecurrent=includecurrent)
        
        if len(v) < pts:
            pts = len(v)
        
        if (pts < 2):
            return float('nan')
        else:
            result = linregress(range(pts), v[-pts:])
        
        return result[0]
        
    def nextRecord(self):
        self._recordCurrent['tStart'] = str(self._recordStartTime)
        self._recordCurrent['tEnd'] = str(datetime.now())
        self._recordCurrent['index' ] = self._recordNum
        self._recordCurrent['group'] = self._groupNum
        
        keysAll = set(list(self._recordCurrent.keys()) + list(self._data.keys()))
                
        for key in keysAll:
            if key not in self._data:
                # Create missing records
                self._data[key] = [self._valueMissing]*self._numRecords
            if key not in self._recordCurrent:
                # The current results didn't have a previously assigned value.  Add nan
                self._data[key].append(self._valueMissing)
            else:
                self._data[key].append(self._recordCurrent[key])
        
        self._recordCurrent = {}
        self._recordNum += 1
        self._numRecords += 1
        self._recordStartTime = datetime.now()
        
    def nextGroup(self):
        """ Creates new grouping with current record as first entry in new group """
        self._groupNum += 1
        self._groupStart = self._recordNum
    
    def setOrder(self, order):
        self._columnOrder = ['index'] + order
        
    def numRecords(self):
        return self._recordNum
        
    def toFrame(self):
        # Create full column list by putting the columns specified in 
        # columnOrder  first and then any missing ones at the end
        columns = self._columnOrder + list(set(self._data.keys()) - set(self._columnOrder))
        return pd.DataFrame(self._data, columns=columns).set_index('index')
    
    def writeData(self, fname):
        self.toFrame().to_csv(fname)
        
class ParameterSweep(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        
        self._parameters = {}
        self._parameterOrder = []
        
        self._parameterList = None
        self._listComputed = False

        self._index = 0
        self._indexLast = None
        self._length = None

    def __getitem__(self, key):
        return self._parameterList[self._index][self._parameterOrder.index(key)]
    
    def __setitem__(self, key, val):
        raise Exception('Cannot assign parameter value')
    
    def __repr__(self):
        return self._parameterList.__repr__()

    def get(self, key):
        return self.__getitem__(key)
    
    def getAll(self):
        return dict(zip(self._parameterOrder, self.getCurrentRow()))
    
    def getLast(self, key):
        if self._indexLast is None:
            return None
        else:
            return self._parameterList[self._indexLast][self._parameterOrder.index(key)]
    
    def setParameterRange(self, key, val):
        # Create a copy if we can
        try:
            val = val.copy()
        except AttributeError:
            pass
        
        # If val is singular create a unitary list
        try:
            len(val)
        except TypeError:
            val = [val]
            

            
        self._parameters[key] = val
        self._listComputed = False
        
    def setOrder(self, order):
        # Check for complete list
        if (set(order) != set(self._parameters.keys())):
            raise Exception('Ordering list must contain all parameters')
        
        self._parameterOrder = order
        self._listComputed = False
    
    def compute(self):
        self.reset()
        self._parameterList = list(product(*[self._parameters[k] for k in self._parameterOrder]))
        self._length = len(self._parameterList)
        self._listComputed = True
        
    def reset(self):
        self._index = 0
        self._indexLast = None
        
    def checkValid(self):
        if not self._listComputed:
            raise Exception('compute() must be called before usage')        

    def getList(self):
        self.checkValid()
        return self._parameterList
    
    def next(self):
        self.checkValid()
        self._indexLast = self._index
        self._index += 1
        
    def nextGroup(self):
        # Slow but I'm tried of messing with this for now
        self._indexLast = self._index
        i0 = self._index
        v = self._parameterList[self._index][:-1]
        while (self._index < self._length) and (v == self._parameterList[self._index][:-1]):
            self.next()
        i1 = self._index
        print('Advanced from {:d} to {:d}'.format(i0, i1))
        
    def getCurrentRow(self):
        self.checkValid()
        return self._parameterList[self._index]
    
    def getIndex(self):
        return self._index
    
    def end(self):
        return self._index >= self._length
            
