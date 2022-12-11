"""
Created on Jul 4, 2017

@author: kyleh
"""

from pyate.instrument import Instrument


class PowerSupply(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "PowerSupply"


@Instrument.register_models(["DP832"])
class PowerSupplyDP832(PowerSupply):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "PowerSupplyDP832"

    def set_output_state(self, channel, state):
        if type(state) is not bool:
            raise ValueError("State must be boolean")
        if channel not in [1, 2, 3]:
            raise ValueError("channel must be integer of value 1-3")

        # Get proper string representatiosn of arguments
        statestr = "ON" if state else "OFF"
        chanstr = {1: "CH1", 2: "CH2", 3: "CH3"}[channel]

        result = self.write(":OUTP {:s},{:s}".format(chanstr, statestr))
        return result

    def set_output(self, channel, state):
        return self.set_output_state(channel, state)

    def get_voltage(self, channel):
        return float(self.query(":SOUR{:d}:VOLT?".format(channel)))

    def set_voltage(self, channel, value):
        self.write(":SOUR{:d}:VOLT {:g}".format(channel, value))
        result = self.get_voltage(channel)

        self.logger.debug("Readback = {:g}".format(result))
        return result

    def get_current(self, channel):
        return float(self.query(":SOUR{:d}:CURR?".format(channel)))

    def set_current(self, channel, value):
        self.write(":SOUR{:d}:CURR {:g}".format(channel, value))
        result = self.get_current(channel)

        self.logger.debug("Readback = {:g}".format(result))
        return result

    def meas_voltage(self, channel):
        result = float(self.query(":MEAS:VOLT? CH{:d}".format(channel)))

        self.logger.debug("Measured Voltage = {:g}".format(result))
        return result

    def meas_current(self, channel):
        result = float(self.query(":MEAS:CURR? CH{:d}".format(channel)))

        self.logger.debug("Measured Current = {:g}".format(result))
        return result


@Instrument.register_models(["E3646A"])
class PowerSupplyKeysight(PowerSupply):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "PowerSupplyKeysight"

    def select_channel(self, channel):
        self.write("INST:NSEL {:d}".format(channel))

    def set_output(self, channel, state):
        self.select_channel(channel)
        if state is True:
            result = self.write(":OUTP ON")
        else:
            result = self.write(":OUTP OFF")
        return result

    def set_voltage(self, channel, value):
        self.select_channel(channel)
        self.write("VOLT {:g}".format(value))
        result = float(self.query(":VOLT?"))

        self.logger.debug("Readback = {:g}".format(result))
        return result

    def set_current(self, channel, value):
        self.select_channel(channel)
        self.write("CURR {:g}".format(value))
        result = float(self.query("CURR?"))

        self.logger.debug("Readback = {:g}".format(result))
        return result

    def set_voltage_protection(self, channel, value):
        self.select_channel(channel)
        self.write("VOLT:PROT {:d}".format(value))

    def get_voltage_protection(self, channel):
        self.select_channel(channel)
        result = self.query("VOLT:PROT?")
        return result

    def meas_voltage(self, channel):
        self.select_channel(channel)
        result = float(self.query(":MEAS:VOLT?"))

        self.logger.debug("Measured Voltage = {:g}".format(result))
        return result

    def meas_current(self, channel):
        self.select_channel(channel)
        result = float(self.query(":MEAS:CURR?"))

        self.logger.debug("Measured Voltage = {:g}".format(result))
        return result

    def get_status(self):
        b_status = self.query("STAT:QUES:INST:ISUM{:d}:COND?".format(channel))

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
