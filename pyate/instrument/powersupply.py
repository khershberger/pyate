"""
Created on Jul 4, 2017

@author: kyleh
"""

from pyate.instrument import Instrument


class PowerSupply(Instrument):
    """
    Superclass for all Power Supply instruments

    Outliens required functionality for all Power Supply drivers and provies
    helper methods.
    """

    def __init__(self, *args, channel=None, **kwargs):
        """
        Constructor for all Power Supply instruments

        Parameters
        ----------
        channel : int, optional
            Default channel to use for instrument

        Returns
        -------
        None.

        """
        super().__init__(*args, **kwargs)
        self.driver_name = "PowerSupply"
        self.set_default_channel(channel)

    def set_output_state(self, state: bool, channel: int = None):
        raise NotImplementedError()

    def get_output_state(self, channel: int = None):
        raise NotImplementedError()


@Instrument.register_models(["DP832"])
class PowerSupplyDP832(PowerSupply):
    """
    Instrument driver for Rigol DP832 power supply
    """

    def __init__(self, *args, channel=None, **kwargs):
        """
        Constructor for Rigol DP832 Power Supply

        Parameters
        ----------
        channel : int, optional
            Default channel to use for instrument

        Returns
        -------
        None.

        """
        super().__init__(*args, channel=channel, **kwargs)
        self.driver_name = "PowerSupplyDP832"

    def get_output_state(self, channel: int = None):
        channel = self.get_default_channel(default=channel)

        chanstr = {1: "CH1", 2: "CH2", 3: "CH3"}[channel]
        result = self.query(f":OUTP? {chanstr}")
        self.logger.debug("get_output_sttate = %s", str(result))
        return result

    def set_output_state(self, state: bool, channel: int = None):
        channel = self.get_default_channel(default=channel)
        if not isinstance(state, bool):
            raise TypeError("state must be boolean")

        # Get proper string representatiosn of arguments
        statestr = "ON" if state else "OFF"
        chanstr = {1: "CH1", 2: "CH2", 3: "CH3"}[channel]

        result = self.write(f":OUTP {chanstr},{statestr}")
        return result

    def get_voltage(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        return float(self.query(f":SOUR{channel}:VOLT?"))

    def set_voltage(self, value: float, channel: int = None, readback=False):
        channel = self.get_default_channel(default=channel)
        self.write(f":SOUR{channel}:VOLT {value}")
        if readback:
            result = self.get_voltage(channel)
            self.logger.debug("Readback = %g", result)
            return result

    def get_current(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        return float(self.query(f":SOUR{channel}:CURR?"))

    def set_current(self, value: float, channel: int = None, readback: bool = False):
        channel = self.get_default_channel(default=channel)
        self.write(f":SOUR{channel}:CURR {value}")
        if readback:
            result = self.get_current(channel)
            self.logger.debug("Readback = %g", result)
            return result

    def measure_voltage(self, channel: int = None):
        result = float(self.query(f":MEAS:VOLT? CH{channel}"))
        self.logger.debug("Measured Voltage = %g", result)
        return result

    def measure_current(self, channel: int = None):
        result = float(self.query(f":MEAS:CURR? CH{channel}"))
        self.logger.debug("Measured Current = %g", result)
        return result


@Instrument.register_models(["E3646A"])
class PowerSupplyKeysight(PowerSupply):
    """
    Instrument driver for Keysight E3646A & similar supplies
    """

    def __init__(self, *args, channel=None, **kwargs):
        """
        Constructor for Rigol DP832 Power Supply

        Parameters
        ----------
        channel : int, optional
            Default channel to use for instrument

        Returns
        -------
        None.

        """
        super().__init__(*args, channel=channel, **kwargs)
        self.driver_name = "PowerSupplyKeysight"

    def _get_active_channel(self):
        # TODO: Verify this works
        return int(self.query("INST:NSEL?"))

    def _set_active_channel(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        self.write(f"INST:NSEL {channel}")

    def get_output_state(self, channel: int = None):
        self._set_active_channel(channel)
        result = self.query(":OUTP?")
        self.logger.debug("get_output_sttate = %s", str(result))
        return result

    def set_output_state(self, state: bool, channel: int = None):
        self._set_active_channel(channel)
        if not isinstance(state, bool):
            raise TypeError("state must be boolean")

        statestr = "ON" if state else "OFF"

        self.write(f":OUTP {statestr}")

    def get_voltage(self, channel: int = None):
        self._set_active_channel(channel)
        return float(self.query("VOLT?"))

    def set_voltage(self, value: float, channel: int = None, readback=False):
        self._set_active_channel(channel)
        self.write(f"VOLT {value}")
        if readback:
            result = self.get_voltage(channel)
            self.logger.debug("Readback = %g", result)
            return result

    def get_over_voltage_protection(self, channel: int = None):
        self._set_active_channel(channel)
        result = self.query("VOLT:PROT?")
        return result

    def set_over_voltage_protection(
        self, value: float, channel: int = None, readback=False
    ):
        self._set_active_channel(channel)
        self.write(f"VOLT:PROT {value}")

    def get_current(self, channel: int = None):
        self._set_active_channel(channel)
        return float(self.query("CURR?"))

    def set_current(self, value: float, channel: int = None, readback: bool = False):
        self._set_active_channel(channel)
        self.write(f"CURR {value}")
        if readback:
            result = self.get_current(channel)
            self.logger.debug("Readback = %g", result)
            return result

    def measure_voltage(self, channel: int = None):
        self._set_active_channel(channel)
        result = float(self.query(":MEAS:VOLT?"))
        self.logger.debug("Measured Voltage = %g")
        return result

    def measure_current(self, channel: int = None):
        self._set_active_channel(channel)
        result = float(self.query(":MEAS:CURR?"))
        self.logger.debug("Measured Current = %g")
        return result

    def get_status(self, channel: int = None):
        channel = self.get_default_channel(default=channel)

        b_status = self.query(f"STAT:QUES:INST:ISUM{channel}:COND?")

        # Now check bits inside of STATUS byte.  THey are as follows:  (Remember
        # that bit references in MATLAB need to be incremented by one as compared
        # to the correct nomencalture, since MATLAB is "one referenced" instead of
        # "zero referenced")
        # %
        # % Condition               bit     bit(MATLAB)
        # % Lost Voltage Reg (CC)   0           1
        # % Lost Current Reg (CV)   1           2
        # % Over Voltage            9           10

        result = {}
        result["cc"] = b_status & 0b0000000001
        result["cv"] = b_status & 0b0000000010
        result["ov"] = b_status & 0b1000000000

        return result


@Instrument.register_models(["MODEL 24[0-9]0"])
class PowerSupplyKeithley2400(PowerSupply):
    """
    Instrument driver for Keithley 2400 SMU
    """

    def __init__(self, *args, channel=None, **kwargs):
        """
        Constructor 

        Parameters
        ----------
        channel : int, optional
            Default channel to use for instrument

        Returns
        -------
        None.

        """
        super().__init__(*args, channel=channel, **kwargs)
        self.driver_name = "PowerSupplyKeithley2400"

    def get_output_state(self, channel: int = None):
        return self.get_basic_parameter(":OUTP:STAT", dtype=bool)

    def set_output_state(self, state: bool, channel: int = None):
        self.check_parameter("state", state, bool, None)
        return self.set_basic_parameter(":OUTP:STAT", state, dtype=bool)

    def get_voltage(self, channel: int = None):
        return self.get_basic_parameter(":SOUR:VOLT", dtype=float)

    def set_voltage(
        self, voltage: float, channel: int = None, current_limit=None, readback=False
    ):
        self.check_parameter("voltage", voltage, float, None)

        self.write(":SOUR:FUNC VOLT")
        # :SOUR:VOLT:MODE FIXED
        # :SOUR:VOLT:RANG 20
        # :SOUR:VOLT:LEV 10
        # :SENS:CURR:PROT 10E-3
        result = self.set_basic_parameter(":SOUR:VOLT:LEV", voltage, dtype=float)

        if current_limit is not None:
            self.check_parameter("current_limit", current_limit, float, None)
            self.set_basic_parameter(":SENS:CURR:PROT", current_limit, dtype=float)

    def get_over_voltage_protection(self, channel: int = None):
        return self.get_basic_parameter(":SOUR:VOLT:PROT", dtype=float)

    def set_over_voltage_protection(
        self, voltage: float, channel: int = None, readback=False
    ):
        self.check_parameter("voltage", voltage, float, None)
        return self.set_basic_parameter(":SOUR:VOLT:PROT", voltage, dtype=float)

    def get_current(self, channel: int = None):
        return self.get_basic_parameter(":SOUR:CURR", dtype=float)

    def set_current(self, current: float, channel: int = None, readback=False):
        self.check_parameter("Current", current, float, None)
        self.write(":SOUR:FUNC CURR")
        return self.set_basic_parameter(":SOUR:CURR", current, dtype=float)

    def measure(self, channel: int = None):
        self.write(":FORMat:ELEMents VOLT,CURR")
        raw = self.query(":READ?")
        return [float(x) for x in raw.split(",")]

    def measure_voltage(self, channel: int = None):
        # self.write(":CONF:VOLT") # This does not seem to be the 'right' way

        self.write(':SENS:FUNC "VOLT"')
        self.write(":FORMat:ELEMents VOLT")
        return self.get_basic_parameter(":READ", dtype=float)

    def measure_current(self, channel: int = None):
        # self.write(":CONF:CURR") # This does not seem to be the 'right' way

        self.write(':SENS:FUNC "CURR"')
        self.write(":FORMat:ELEMents CURR")
        return self.get_basic_parameter(":READ", dtype=float)

    def get_beep_state(self, channel: int = None):
        return self.get_basic_parameter(":SYST:BEEP:STAT", dtype=bool)

    def set_beep_state(self, state, channel: int = None):
        self.check_parameter("state", state, bool, None)
        return self.set_basic_parameter(":SYST:BEEP:STAT", state, dtype=bool)
