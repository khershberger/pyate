"""
Created on May 9, 2019

@author: kyleh
"""

import logging
import os

from numpy import genfromtxt, savetxt, stack, all
import pandas as pd
from scipy.interpolate import interp1d


class Calibration(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tables = {}
        self.indep_var = None

    def set_indep_var(self, name):
        self.indep_var = name

    def set_table(self, name, x, y):
        self.tables[name] = interp1d(x, y)

    def get(self, name, x):
        val = self.tables[name](x)
        self.logger.debug("cal(%s,%g) = %g", name, x, val)
        return val

    def read(self, filename, delimiter=",", indep=None):
        cal_data = pd.read_csv(filename, delimiter=delimiter)

        # Determine independent values
        if indep is None:
            indep = cal_data.columns[0]

        # Check for compatability if an indep_var already set
        if self.indep_var is not None:
            if self.indep_var != indep:
                raise ValueError("Incompatible independant variables")
        else:
            self.indep_var = indep

        x = cal_data[self.indep_var]

        for name in cal_data.columns:
            if name == self.indep_var:
                continue
            y = cal_data[name]
            self.set_table(name, x, y)

    def write(self, filename, format="csv", fields=None):
        if fields is None:
            fields = list(self.tables.keys())

        cal_data = pd.DataFrame()

        # Check for compatible dimensions
        x = self.tables[fields[0]].x  # Get x of first field
        cal_data[self.indep_var] = x

        for field in fields:
            if not all(self.tables[field].x == x):
                raise ValueError("X data must be same for all saved fields")

            cal_data[field] = self.tables[field].y

        cal_data.to_csv(filename, header=True, index=False)
