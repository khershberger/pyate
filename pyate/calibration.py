"""
Created on May 9, 2019

@author: kyleh
"""

import logging
import os
from numpy import genfromtxt
from scipy.interpolate import interp1d


class Calibration(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tables = {}

    def setTable(self, name, x, y):
        self.tables[name] = interp1d(x, y)

    def setTableFromFile(self, name, fname, path=None, delimiter=","):
        if path is not None:
            fname = os.path.join(path, fname)
        data = genfromtxt(fname, delimiter=delimiter)
        self.setTable(name, data.T[0], data.T[1])

    def get(self, name, x):
        val = self.tables[name](x)
        self.logger.debug("cal(%s,%g) = %g", name, x, val)
        return val
