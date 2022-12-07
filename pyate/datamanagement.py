"""
Created on May 9, 2019

@author: kyleh
"""

from datetime import datetime
from matplotlib.pyplot import plot
import numpy as np
from scipy.stats import linregress
import pandas as pd
from itertools import product


class DataLogger(object):
    """
    classdocs
    """

    def __init__(self, logfile=None, timestamp=True):
        """
        Constructor
        """

        self._enableTimestamp = timestamp
        self._recordStartTime = datetime.now()
        self._recordStopTime = None
        self._logfile = logfile
        self._enable_timestamp = timestamp
        self._record_start_time = datetime.now()
        self._record_stop_time = None
        self._data = {}
        self._record_current = {}
        self._record_num = 0
        self._num_records = 0

        self._group_num = 0
        self._group_start = 0

        self._column_order = []

        self._value_missing = float("nan")

    def __getitem__(self, key):
        return self._record_current[key]

    def __setitem__(self, key, val):
        self._record_current[key] = val

    def last(self, key):
        return self._data[key][-1]

    def get_data(self, key, s=None, includecurrent=False):
        if key not in self._data:
            v = []
        else:
            v = self._data[key][s]

        if includecurrent:
            v += [self._record_current.get(key, None)]

        return v

    def trend(self, key, pts, includecurrent=False):
        # Get all the data in the current group
        v = self.get_data(key, slice(self._group_start, None), includecurrent=includecurrent)

        if len(v) < pts:
            pts = len(v)

        if pts < 2:
            return float("nan")
        else:
            result = linregress(range(pts), v[-pts:])

        return result[0]

    def next_record(self):
        if self._enable_timestamp:
            self._record_current["tStart"] = str(self._record_start_time)
            self._record_current["tEnd"] = str(datetime.now())
        self._record_current["index"] = self._record_num
        self._record_current["group"] = self._group_num

        keysAll = set(list(self._record_current.keys()) + list(self._data.keys()))

        for key in keysAll:
            if key not in self._data:
                # Create missing records
                self._data[key] = [self._value_missing] * self._num_records
            if key not in self._record_current:
                # The current results didn't have a previously assigned value.  Add nan
                self._data[key].append(self._value_missing)
            else:
                self._data[key].append(self._record_current[key])
    
        # if self._autosave:
        #     self.write_record()

        self._record_current = {}
        self._record_num += 1
        self._num_records += 1
        self._record_start_time = datetime.now()

    def next_group(self):
        """ Creates new grouping with current record as first entry in new group """
        self._group_num += 1
        self._group_start = self._record_num

    def set_order(self, order):
        self._column_order = ["index"] + order

    def num_records(self):
        return self._record_num

    def to_frame(self):
        # Create full column list by putting the columns specified in
        # columnOrder  first and then any missing ones at the end
        columns = self._column_order + list(set(self._data.keys()) - set(self._column_order))
        return pd.DataFrame(self._data, columns=columns).set_index("index")

    def write_record(self):
        if not self._logfile_started:
            pass


    def write_data(self, fname, name="data", fformat="csv"):
        if fformat == "csv":
            self.to_frame().to_csv(fname)
        elif fformat == "hdf":
            self.to_frame().to_hdf(fname, name)

    def plot(self, x=None, y=None, **kwargs):
        if x is None:
            return plot(self._data[y], **kwargs)
        else:
            return plot(self._data[x], self._data[y], **kwargs)


class ParameterSweep(object):
    """
    classdocs
    """

    def __init__(self):
        """
        Constructor
        """

        self._parameters = {}
        self._parameter_order = []

        self._parameter_list = None
        self._list_computed = False

        self._index = 0
        self._index_last = None
        self._length = None

    def __getitem__(self, key):
        return self._parameter_list[self._index][self._parameter_order.index(key)]

    def __setitem__(self, key, val):
        raise Exception("Cannot assign parameter value")

    def __repr__(self):
        return self._parameter_list.__repr__()

    def get(self, key):
        return self.__getitem__(key)

    def get_last(self, key):
        if self._index_last is None:
            return None
        else:
            self.get_last_tuple()[self._parameter_order.index(key)]

    def get_last_tuple(self):
        if self._index_last is None:
            raise ValueError("Last not available due to being on first row")
        else:
            return self._parameter_list[self._index_last]

    def get_current_dict(self):
        return dict(zip(self._parameter_order, self.get_current_tuple()))

    def get_current_tuple(self):
        self.check_valid()
        return self._parameter_list[self._index]

    def get_index(self):
        return self._index

    def get_changes(self):
        if self._index_last is None:
            result = self.get_current_dict()
        else:
            cur = self.get_current_tuple()
            last = self.get_last_tuple()

            result = {}
            for i in range(len(cur)):
                if cur[i] != last[i]:
                    result[self._parameter_order[i]] = cur[i]
        return result

    def set_parameter_range(self, key, val):
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
        self._list_computed = False

    def set_order(self, order):
        # Check for complete list
        if set(order) != set(self._parameters.keys()):
            raise Exception("Ordering list must contain all parameters")

        self._parameter_order = order
        self._list_computed = False

    def compute(self):
        self.reset()
        self._parameter_list = list(product(*[self._parameters[k] for k in self._parameter_order]))
        self._length = len(self._parameter_list)
        self._list_computed = True

    def reset(self):
        self._index = 0
        self._index_last = None

    def check_valid(self):
        if not self._list_computed:
            raise Exception("compute() must be called before usage")

    def get_list(self):
        self.check_valid()
        return self._parameter_list

    def next(self):
        self.check_valid()
        self._index_last = self._index
        self._index += 1

    def next_group(self):
        # Slow but I'm tried of messing with this for now
        self._index_last = self._index
        i0 = self._index
        v = self._parameter_list[self._index][:-1]
        while (self._index < self._length) and (v == self._parameter_list[self._index][:-1]):
            self.next()
        i1 = self._index
        print("Advanced from {:d} to {:d}".format(i0, i1))

    def end(self):
        return self._index >= self._length
