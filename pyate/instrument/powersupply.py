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

        result = self.write(f":OUTP {statestr}")
        return result

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

    def set_over_voltage_protection(self, value: float, channel: int = None, readback=False):
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
