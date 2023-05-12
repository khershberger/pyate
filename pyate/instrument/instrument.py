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
from pyate.instrument.error import InstrumentIOError


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
                    self.logger.warning(
                        "NI Timeout occured during Instrument.write() operation"
                    )
                elif e.error_code == pyvisa.errors.VI_ERROR_CONN_LOST:
                    self.resource.open()
                else:
                    raise e
            except pyvisa.errors.InvalidSession:
                self.logger.warning("InvalidSession error occured attempting to reopen")
                self.resource.open()
            except ConnectionResetError as e:
                self.logger.warning(
                    "ConnectionResetError during Instrument.write().  Closing & Reopening"
                )
                self.resource.reset()
            except visawrapper.prologix.PrologixTimeout as e:
                self.logger.warning(
                    "Prologix Timeout occured during Instrument.write() operation"
                )
        raise InstrumentIOError("Instrument.write() Max retries exceeded")

    return wrapper


class Instrument:
    @classmethod
    def register_models(cls, models):
        logging.getLogger(__name__).debug(".register_models(%s)", str(models))

        def _internal(pyclass):
            manager.InstrumentManager.register_instrument(models, pyclass)
            return pyclass

        return _internal

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.driver_name = "Instrument"

        self._channel_default = None

        if "resource" in kwargs:
            if "addr" in kwargs:
                self.logger.warning(
                    "Called with resource and addr.  resource will take precidence"
                )
            self.resource = kwargs["resource"]
        elif "addr" in kwargs:
            self.resource = visawrapper.ResourceManager.open_resource(kwargs["addr"])
        else:
            self.logger.error("Attempt to create instrument without address")
            raise manager.InstrumentDriverException(
                "Attempt to create instrument without address"
            )

        self.resource.open()
        self.resource.read_termination = "\n"
        self.refreshIDN()

    def __del__(self):
        self.resource.close()

    @property
    def res(self):
        return self._resource

    @res.setter
    def res(self, resource):
        self._resource = resource

    @property
    def resource(self):
        return self._resource

    @resource.setter
    def resource(self, resource):
        self._resource = resource

    def refreshIDN(self):
        self.identity = manager.InstrumentManager.parse_ident_string(
            self.resource.query("*IDN?")
        )

    def open(self):
        self.resource.open()

    def close(self):
        try:
            self.resource.close()
        except pyvisa.errors.VisaIOError as e:
            if e.error_code == pyvisa.errors.VI_ERROR_INV_OBJECT:
                # We'll consider this a sucess
                self.logger.warning("Error when closing device: VI_ERROR_INV_OBJECT")
                pass
            if e.error_code == pyvisa.errors.VI_ERROR_CLOSING_FAILED:
                # We'll consider this a sucess
                self.logger.warning(
                    "Error when closing device: VI_ERROR_CLOSING_FAILED"
                )
                pass
            else:
                raise e

    def reset(self):
        self.logger.debug("Resetting resource")
        try:
            self.resource.close()
        except pyvisa.errors.VisaIOError as e:
            self.logger.error("VisaIOError: {:s}".format(str(e.error_code)))
        self.resource.open()
        self.resource.clear()

    @pyvisaExceptionHandler
    def write(self, command, delay=0.0, retries=3):
        result = self.resource.write(command)
        time.sleep(delay)
        return result

    @pyvisaExceptionHandler
    def read(self, retries=3):
        return self.resource.read()

    def query(self, command, delay=0, retries=3):
        self.write(command, retries=retries)
        time.sleep(delay)
        return self.read(retries=retries)

    def write_binary_values(self, *args, **kwargs):
        return self.resource.write_binary_values(*args, **kwargs)

    def read_binary_values(self, *args, **kwargs):
        return self.resource.read_binary_values(*args, **kwargs)

    def query_binary_values(self, *args, **kwargs):
        return self.resource.query_binary_values(*args, **kwargs)

    def test_connection(self, attempt_reset=False, tries_left=1):
        try:
            self.refreshIDN()
            return True
        except visawrapper.pyvisa.errors.VisaIOError as e:
            if attempt_reset and (tries_left > 0):
                self.resource.close()
                self.resource.open()
                return self.test_connection(
                    attempt_reset=attempt_reset, tries_left=tries_left - 1
                )
            else:
                return False

    def check_parameter(self, par_name, par_value, dtype, drange):
        if dtype is not None:
            if not isinstance(par_value, dtype):
                raise TypeError(
                    "{:s} must be of type {:s}".format(par_name, str(dtype))
                )

        if drange is not None:
            if isinstance(drange, list):
                if par_value not in drange:
                    raise ValueError(
                        "{:s} must be in range {:s}".format(par_name, str(drange))
                    )
            if isinstance(drange, tuple):
                if (par_value < drange[0]) or (par_value > drange[1]):
                    raise ValueError(
                        "{:s} must be between {:g} and {:g}".format(
                            par_name, drange[0], drange[1]
                        )
                    )

    def get_default_channel(self, default=None) -> int:
        """
        Returns instruments devault channel setting

        Parameters
        ----------
        default : int, optional
            Value to return if instrument does not have a default channel set

        Raises
        ------
        TypeError

        Returns
        -------
        int
            Instruments devault channel setting

        """
        if default is None:
            if self._channel_default is None:
                raise Exception(
                    "Ambiguous channel: Channel number must be set before operation"
                )
            return self._channel_default
        elif isinstance(default, int):
            return default
        raise TypeError("Channel must either be an int or None")

    def set_default_channel(self, channel: int = None):
        """
        Sets default channel for this instrument

        Parameters
        ----------
        channel : int, optional
            Default channel to use for instrument

        Raises
        ------
        TypeError

        Returns
        -------
        None.

        """
        if channel is not None and not isinstance(channel, int):
            raise TypeError("channel must be an int or None")
        self._channel_default = channel

    def get_basic_parameter(
        self, scpi_command: str, channel: int = None, dtype=float, retries=3
    ):
        """
        Reads back value from basic SCPI command

        Parameters
        ----------
        scpi_command : string
            SCPI command

        dtype: type
            Python type to return value as

        Raises
        ------
        None

        Returns
        -------
        Value read from instrument

        """

        raw = self.query(scpi_command + "?", retries=retries)

        if dtype == bool:
            lookup = {
                "0": False,
                "false": False,
                "f": False,
                "1": True,
                "true": True,
                "t": True,
            }
            result = lookup[raw]
        else:
            result = dtype(raw)

        return result

    def set_basic_parameter(
        self,
        scpi_command: str,
        value,
        channel: int = None,
        dtype=float,
        raise_exception=True,
        retries=3,
    ):
        """
        Sets value for basic SCPI command

        Parameters
        ----------
        scpi_command : string
            SCPI command
        value : 
            Value to send to instrument
        channel : int (optional)
            Channel to use (if applicable)
        dtype : type
            Python type to return value as
        raise_exception : bool
            Should an exception be raised if value read back from instrument
            does not match set value
        retrues : int
            Number of times to try setting value if readback does not match

        Raises
        ------
        Exception

        Returns
        -------
        bool : Whether readback value matches set value

        """

        if isinstance(value, bool):
            value = int(value)

        while retries >= 0:
            self.write(f"{scpi_command} {value}")
            readback = self.get_basic_parameter(
                scpi_command, channel=channel, dtype=dtype
            )

            if readback == value:
                return True
            else:
                self.logger.warning(
                    "Readback value does not match set value. Retrying..."
                )

            retries -= 1

        self.logger.warning("Readback value does not match set value. Giving up.")
        if raise_exception:
            raise Exception("Readback value does not match set value")
        return False

    def map_value(self, input, direction, mapping):
        """
        Performes value lookups from mapping tables

        Parameters
        ----------
        input : string
            Value to lookup
        
        direction : string
            Which direction to map:
            "from": input is from instrument, output is to Python
            "to": input is from Python, output is to instrument

        mapping table is a tuple of tuples.
            (
                ("text_from_instrument", "python_driver_text", "text_to_instrument"),
                ("text_from_instrument", "python_driver_text", "text_to_instrument"),
            )

        Raises
        ------
        ValueError

        Returns
        -------
        None.

        """
        if direction == "from":
            d = 0
        elif direction == "to":
            d = 1
        else:
            raise ValueError("Invalid direction")

        try:
            keys = [x[d] for x in mapping]
            idx = keys.index(input)
            return mapping[idx][d + 1]
        except ValueError:
            # raise ValueError(f"Error with map_value(): {input} not in mapping table")
            self.logger.warning(
                f"map_from_instrument() input of {input} not in mapping table"
            )
            return input
