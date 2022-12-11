# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 13:51:46 2017

@author: kyleh
"""

import logging
import time
import pyvisa.errors

from pyate import visawrapper
from pyate.instrument import manager


def pyvisaExceptionHandler(fcn):
    """ This is a decorator to handle the excessive number of exceptions
    that pyvisa raises for problems it really should hanldle on it's own """

    def wrapper(self, *args, **kwargs):
        retries = kwargs.get("retries", 3)
        for n in range(retries):
            try:
                return fcn(self, *args, **kwargs)
            except pyvisa.VisaIOError as e:
                if e.error_code == pyvisa.errors.VI_ERROR_TMO:
                    self.logger.warning("NI Timeout occured during Instrument.write() operation")
                elif e.error_code == pyvisa.errors.VI_ERROR_CONN_LOST:
                    self.res.open()
                else:
                    raise e
            except pyvisa.errors.InvalidSession:
                self.logger.warning("InvalidSession error occured attempting to reopen")
                self.res.open()
            except ConnectionResetError as e:
                self.logger.warning("ConnectionResetError during Instrument.write().  Closing & Reopening")
                self.res.reset()
            except visawrapper.prologix.PrologixTimeout as e:
                self.logger.warning("Prologix Timeout occured during Instrument.write() operation")
        raise InstrumentIOError("Instrument.write() Max retries exceeded")

    return wrapper


class Instrument:
    @classmethod
    def register_models(cls, models):
        def _internal(pyclass):
            manager.InstrumentManager.register_instrument(models, pyclass)
            return pyclass

        return _internal

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.driver_name = "Instrument"

        if "resource" in kwargs:
            if "addr" in kwargs:
                self.logger.warning("Called with res and addr.  res will take precidence")
            self.res = kwargs["resource"]
        elif "addr" in kwargs:
            self.res = visawrapper.ResourceManager.open_resource(kwargs["addr"])
        else:
            self.logger.error("Attempt to create instrument without address")
            raise manager.InstrumentDriverException("Attempt to create instrument without address")

        self.res.open()
        self.res.read_termination = "\n"
        self.refreshIDN()

    def __del__(self):
        self.res.close()

    @property
    def res(self):
        return self._res

    @res.setter
    def res(self, resource):
        self._res = resource

    @property
    def resource(self):
        return self._res

    @resource.setter
    def resource(self, resource):
        self._res = resource

    def refreshIDN(self):
        self.identity = manager.InstrumentManager.parse_ident_string(self.res.query("*IDN?"))

    def open(self):
        self.res.open()

    def close(self):
        try:
            self.res.close()
        except pyvisa.errors.VisaIOError as e:
            if e.error_code == pyvisa.errors.VI_ERROR_INV_OBJECT:
                # We'll consider this a sucess
                self.logger.warning("Error when closing device: VI_ERROR_INV_OBJECT")
                pass
            if e.error_code == pyvisa.errors.VI_ERROR_CLOSING_FAILED:
                # We'll consider this a sucess
                self.logger.warning("Error when closing device: VI_ERROR_CLOSING_FAILED")
                pass
            else:
                raise e

    def reset(self):
        self.logger.debug("Resetting resource")
        try:
            self.res.close()
        except pyvisa.errors.VisaIOError as e:
            self.logger.error("VisaIOError: {:s}".format(str(e.error_code)))
        self.res.open()
        self.res.clear()

    @pyvisaExceptionHandler
    def write(self, command, delay=0.0, retries=3):
        res = self.res.write(command)
        time.sleep(delay)
        return res

    @pyvisaExceptionHandler
    def read(self, retries=3):
        return self.res.read()

    def query(self, command, delay=0, retries=3):
        self.write(command, retries=retries)
        time.sleep(delay)
        return self.read(retries=retries)

    def write_binary_values(self, *args, **kwargs):
        return self.res.write_binary_values(*args, **kwargs)

    def read_binary_values(self, *args, **kwargs):
        return self.res.read_binary_values(*args, **kwargs)

    def query_binary_values(self, *args, **kwargs):
        return self.res.query_binary_values(*args, **kwargs)

    def test_connection(self, attempt_reset=False, tries_left=1):
        try:
            self.refreshIDN()
            return True
        except visawrapper.pyvisa.errors.VisaIOError as e:
            if attempt_reset and (tries_left > 0):
                self.res.close()
                self.res.open()
                return self.test_connection(attempt_reset=attempt_reset, tries_left=tries_left - 1)
            else:
                return False

    def check_parameter(self, par_name, par_value, dtype, drange):
        if dtype is not None:
            if not isinstance(par_value, dtype):
                raise TypeError("{:s} must be of type {:s}".format(par_name, str(dtype)))

        if drange is not None:
            if isinstance(drange, list):
                if par_value not in drange:
                    raise ValueError("{:s} must be in range {:s}".format(par_name, str(drange)))
            if isinstance(drange, tuple):
                if (par_value < drange[0]) or (par_value > drange[1]):
                    raise ValueError("{:s} must be between {:g} and {:g}".format(par_name, drange[0], drange[1]))
