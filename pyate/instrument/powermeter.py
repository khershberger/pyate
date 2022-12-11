"""
Created on Jul 12, 2017

@author: kyleh
"""


"""
Some notes for later:

This block should directly read the operation complete flag from
the <can't remember exact name of it> status register.
It works, but it takes a long time for the flag to be set.

stat = 0
pm.res.write('*OPC')
pm.res.write('INIT1')
while(not (stat & 1)):
     stat = int(pm.res.query('*ESR?'))
     print('{0:d} {0:b}'.format(stat, stat))

"""

import time

from pyate.instrument import Instrument
from pyate.instrument.error import InstrumentNothingToRead


@Instrument.register_models(["E4417A"])
class PowerMeter(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "PowerMeter"

        # increase timeout
        ##### WARNING!!!  Apparently pyfisa timeout is in milliseconds
        # Prologix is in seconds
        # self.res.timeout = 500.0          # This is due to periodically long read times
        self.delay = 0.05  # Prevent instrument from getting hung up by talking to it too fast

    def set_offset(self, channel, value=None, enable=None):
        if value is not None:
            self.write("SENS{:d}:CORR:GAIN2 {:g}".format(channel, value))

        if enable is not None:
            self.write("SENS{:d}:CORR:GAIN2:STAT {:b}".format(channel, enable))

    def set_duty_cycle(self, channel, value=None, enable=None):
        if value is not None:
            self.write("SENS{:d}:CORR:DCYC {:g}".format(channel, value * 100.0))

        if enable is not None:
            self.write("SENS{:d}:CORR:DCYC:STAT {:b}".format(channel, enable))

    def get_frequency(self, channel):
        return float(self.query("SENS{:d}:FREQ?".format(channel)))

    def set_frequency(self, channel, freq):
        self.write("SENS{:d}:FREQ {:g}HZ".format(channel, freq))

    def set_settings(
        self,
        channel,
        readings_per_second=None,
        continuous=None,
        trig_source=None,
        averaging=None,
        resolution=None,
        offset=None,
        dutycycle=None,
    ):

        # This must be set before averaging as it will reset the averaging settings
        if resolution is not None:
            init_status = self.query("INIT{:d}:CONT?".format(channel))
            self.write("CONF{:d} DEF,{:d},(@{:d})".format(channel, resolution, channel))
            self.write("INIT{:d}:CONT {:s}".format(channel, init_status))

        if continuous is not None:
            self.write("INIT{:d}:CONT {:d};".format(channel, int(continuous)))
        if trig_source is not None:
            self.write("TRIG{:d}:SOUR {:s}".format(channel, trig_source))
        if readings_per_second is not None:
            self.write("SENS{:d}:SPE {:d}".format(channel, readings_per_second))
        if averaging is not None:
            if averaging == False:
                self.write("SENS{:d}:AVER 0".format(channel))
            elif (averaging == "auto") or (averaging == "AUTO"):
                self.write("SENS{:d}:AVER 1".format(channel))
                self.write("SENS{:d}:AVER:COUN:AUTO 1".format(channel))
            else:
                self.write("SENS{:d}:AVER 1".format(channel))
                self.write("SENS{:d}:AVER:COUN:AUTO 0".format(channel))
                self.write("SENS{:d}:AVER:COUN {:d}".format(channel, averaging))

        if offset is not None:
            if isinstance(offset, bool):
                self.write("SENS{:d}:CORR:GAIN2:STAT {:b}".format(channel, offset))
            else:
                self.write("SENS{:d}:CORR:GAIN2:STAT 1".format(channel))
                self.write("SENS{:d}:CORR:GAIN2 {:g}".format(channel, offset))

        if dutycycle is not None:
            if isinstance(dutycycle, bool):
                self.write("SENS{:d}:CORR:DCYC:STAT {:d}".format(channel, dutycycle))
            else:
                self.write("SENS{:d}:CORR:DCYC:STAT 1".format(channel))
                self.write("SENS{:d}:CORR:DCYC {:g}".format(channel, dutycycle * 100.0))

    #    def get_settings(self,channel):
    #        result = {}
    #        result['readings_per_second'] = self.query('SENS{:d}:SPE?'.format(channel))
    #        result['continuous']        = self.query('INIT{:d}:CONT?'.format(channel))
    #        result['trig_source']        = self.query('TRIG:SOUR?'.format(channel))
    #
    #        if (self.query('SENS{:d}.AVER:COUN:AUTO?'.format(channel)) == 'AUTO'):
    #            result['averaging']     = 'AUTO'
    #        else:
    #            result['averaging']     = self.query('SENS{:d}:AVER:COUN?'.format(channel))
    #
    #        return result

    def get_settings(self, channel):
        result = {}
        result["continuous"] = bool(int(self.query("INIT{:d}:CONT?".format(channel))))
        result["trig_source"] = self.query("TRIG{:d}:SOUR?".format(channel))
        result["readings_per_second"] = int(self.query("SENS{:d}:SPE?".format(channel)))

        avgen = bool(int(self.query("SENS{:d}:AVER?".format(channel))))
        avgauto = bool(int(self.query("SENS{:d}:AVER:COUN:AUTO?".format(channel))))
        avgcnt = int(self.query("SENS{:d}:AVER:COUN?".format(channel)))
        if not avgen:
            result["averaging"] = False
        elif avgauto:
            result["averaging"] = "auto"
        else:
            result["averaging"] = avgcnt

        # result['resolution'] = self.query('TRIG{:d}:SOUR'.format(channel))

        offseten = bool(int(self.query("SENS{:d}:CORR:GAIN2:STAT?".format(channel))))
        if not offseten:
            result["offset"] = False
        else:
            result["offset"] = float(self.query("SENS{:d}:CORR:GAIN2?".format(channel)))

        dutyen = bool(int(self.query("SENS{:d}:CORR:DCYC:STAT?".format(channel))))
        if not dutyen:
            result["dutycycle"] = False
        else:
            result["dutycycle"] = float(self.query("SENS{:d}:CORR:DCYC?".format(channel)))
        return result

    def meas_power(self, channel, resolution=None):
        if resolution is not None:
            self.set_resolution(channel, resolution)
        # self.write('INIT{:d}:CONT 1'.format(channel))
        # self.write('INIT{:d}'.format(channel), delay=self.delay)
        result = self.query("FETC{:d}?".format(channel), delay=self.delay)
        return float(result)

    def set_defaults(self, channel):
        self.set_settings(
            channel,
            readings_per_second=40,
            continuous=True,
            trig_source="IMM",
            averaging="auto",
            resolution=3,
            offset=False,
            dutycycle=False,
        )

        # self.set_offset(channel, enable=False, value=0.)
        # self.set_duty_cycle(channel, enable=False, value=0.01)
