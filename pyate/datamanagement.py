"""
Created on May 9, 2019

ToDo:
- Don't create new record dicts, but rather set values to None
- check if next_group is called without calling next_record first

@author: kyleh
"""

from collections import OrderedDict
from datetime import datetime
from itertools import product
import logging

from matplotlib.pyplot import plot
import numpy as np
from scipy.stats import linregress
import pandas as pd


class DataLogger(object):
    """
    classdocs
    """

    def __init__(self, logfile=None, logfile_format="csv", autosave=False, timestamp=True):
        """
        Constructor
        """

        self._logger = logging.getLogger(__name__)

        self._logfile = logfile
        self._logfile_started = False
        self._logfile_format = logfile_format
        self._autosave = autosave

        self._enable_timestamp = timestamp
        self._record_start_time = datetime.now()
        self._record_stop_time = None
        self._data = OrderedDict()
        self._record_current = OrderedDict()
        self._record_num = 0
        self._num_records = 0

        self._group_num = 0
        self._group_start = 0

        self._column_order = []

        # self._value_missing = float("nan")
        self._value_missing = None

    def __getitem__(self, key):
        return self._record_current[key]

    def __setitem__(self, key, val):
        if self._logfile_started and key not in self._data:
            raise (KeyError("Cannot add new keys once logfile has been started"))

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

        # Since keys in _record_current are never deleted, then _record_current should
        # always contain the keys already in _data

        for key, item in self._record_current.items():
            if key not in self._data:
                # Create missing record & fill with appropriate missing data value
                self._data[key] = [self._value_missing] * self._num_records

            self._data[key].append(self._record_current[key])

        if self._autosave:
            self.write_record()

        for key in self._record_current.keys():
            self._record_current[key] = None
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
        columns = self._column_order.copy()
        for key in self._data.keys():
            if key not in columns:
                columns.append(key)

        return pd.DataFrame(self._data, columns=columns).set_index("index")

    def to_csv(self, data):
        def add_quotes(text):
            if "," in text:
                text = f'"{text}"'
            return text

        line = ",".join([add_quotes(str(obj)) for obj in data])
        self._logger.debug(f"to_csv.line = {line}")
        return line

    def write_record(self):
        if self._logfile is None:
            raise ValueError("Logfile not specified")
        self._logger.debug("Writing record data")
        data_to_write = self._record_current
        if not self._logfile_started:
            with open(self._logfile, "wt") as fid:
                fid.write(self.to_csv(data_to_write.keys()))
                fid.write("\n")
            self._logfile_started = True

        with open(self._logfile, "at") as fid:
            fid.write(
                self.to_csv(data_to_write.values())
            )  # I think an odict should return the values in the same order as the keys....
            fid.write("\n")

    def write_data(self, filename=None, format="csv", name="data"):
        if filename is None:
            filename = self._logfile

        if filename is None:
            raise (FileNotFoundError("No output filename provided"))

        if format == "csv":
            self.to_frame().to_csv(filename)
        elif format == "hdf":
            self.to_frame().to_hdf(filename, name)

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
