"""
Created on 2017-11-13

@author: kyleh
"""

from pyate.instrument import Instrument


@Instrument.register_models(["8845A", "34401A"])
class Multimeter(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "Multimeter"

    def set_settings(self, mode="DCV", trig_source="IMM", filter=20):

        self.write("DET:BAND {:g}".format(filter))
        self.write("TRIG:SOUR {:s}".format(trig_source))

        if averaging == "AUTO":
            self.write("SENS{:d}:AVER:COUN:AUTO 1".format(channel))
        elif averaging == 0:
            self.write("SENS{:d}:AVER 0".format(channel))
        else:
            self.write("SENS{:d}:AVER:COUN {:d}".format(channel, averaging))

    def meas_current_dc(self, mode="MEAS"):
        if mode == "MEAS":
            result = self.query("MEAS:CURR:DC?")
        elif mode == "READ":
            result = self.query("READ?")
        else:
            raise Exception("Unknown measurement mode {:s}".format(mode))

        try:
            value = float(result)
        except ValueError as e:
            value = float("nan")
        return value

    def meas_voltage_dc(self):
        # self.write('CONF:VOLT:DC AUTO')
        # self.write('INIT')
        # result = self.query('FETC?')
        result = self.query("MEAS:VOLT:DC?")
        try:
            value = float(result)
        except ValueError as e:
            value = float("nan")
        return value


class MultimeterFluke(Multimeter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "MultimeterFluke"
