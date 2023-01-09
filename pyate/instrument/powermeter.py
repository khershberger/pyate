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


class PowerMeter(Instrument):
    """
    Superclass for all Power Meter instruments

    Outliens required functionality for all Power Meter drivers and provies
    helper methods.
    """

    def __init__(self, *args, channel=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "PowerMeter"
        self.set_default_channel(channel)

        # increase timeout
        ##### WARNING!!!  Apparently pyfisa timeout is in milliseconds
        # Prologix is in seconds
        # self.res.timeout = 500.0          # This is due to periodically long read times
        self.delay = 0.05  # Prevent instrument from getting hung up by talking to it too fast


@Instrument.register_models(["E4417A"])
class PowerMeterKeysight(PowerMeter):
    def __init__(self, *args, channel=None, **kwargs):
        """
        Constructor for Keysight RF Power Meters

        Parameters
        ----------
        channel : int, optional
            Default channel to use for instrument

        Returns
        -------
        None.

        """
        super().__init__(*args, channel=channel, **kwargs)
        self.driver_name = "PowerMeterKeysight"

    def set_offset(self, value: float = None, enable: bool = None, channel: int = None):
        channel = self.get_default_channel(default=channel)
        if value is not None:
            self.write(f"SENS{channel}:CORR:GAIN2 {value}")

        if enable is not None:
            self.write(f"SENS{channel}:CORR:GAIN2:STAT {enable}")

    def set_duty_cycle(self, value: float = None, enable: bool = None, channel: int = None):
        channel = self.get_default_channel(default=channel)
        if value is not None:
            self.write(f"SENS{channel}:CORR:DCYC {value * 100.0}")

        if enable is not None:
            self.write(f"SENS{channel}:CORR:DCYC:STAT {enable}")

    def get_frequency(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        return float(self.query(f"SENS{channel}:FREQ?"))

    def set_frequency(self, frequency, channel: int = None):
        channel = self.get_default_channel(default=channel)
        self.write(f"SENS{channel}:FREQ {frequency/1E9:.3f}GHZ")

    def set_settings(
        self,
        channel: int = None,
        readings_per_second: int = None,
        continuous: bool = None,
        trig_source: str = None,
        averaging: str = None,
        resolution: int = None,
        offset: float = None,
        dutycycle: bool = None,
    ):

        channel = self.get_default_channel(default=channel)

        # This must be set before averaging as it will reset the averaging settings
        if resolution is not None:
            init_status = self.query(f"INIT{channel}:CONT?")
            self.write(f"CONF{channel} DEF,{resolution},(@{channel})")
            self.write(f"INIT{channel}:CONT {init_status}")

        if continuous is not None:
            self.write(f"INIT{channel}:CONT {int(continuous)};")
        if trig_source is not None:
            self.write(f"TRIG{channel}:SOUR {trig_source}")
        if readings_per_second is not None:
            self.write(f"SENS{channel}:SPE {readings_per_second}")
        if averaging is not None:
            if averaging == False:
                self.write(f"SENS{channel}:AVER 0")
            elif (averaging == "auto") or (averaging == "AUTO"):
                self.write(f"SENS{channel}:AVER 1")
                self.write(f"SENS{channel}:AVER:COUN:AUTO 1")
            else:
                self.write(f"SENS{channel}:AVER 1")
                self.write(f"SENS{channel}:AVER:COUN:AUTO 0")
                self.write(f"SENS{channel}:AVER:COUN {averaging}")

        if offset is not None:
            if isinstance(offset, bool):
                self.write(f"SENS{channel}:CORR:GAIN2:STAT {offset}")
            else:
                self.write(f"SENS{channel}:CORR:GAIN2:STAT 1")
                self.write(f"SENS{channel}:CORR:GAIN2 {offset}")

        if dutycycle is not None:
            if isinstance(dutycycle, bool):
                self.write(f"SENS{channel}:CORR:DCYC:STAT {dutycycle}")
            else:
                self.write(f"SENS{channel}:CORR:DCYC:STAT 1")
                self.write(f"SENS{channel}:CORR:DCYC {dutycycle * 100.0}")

    def get_settings(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        result = {}
        result["continuous"] = bool(int(self.query(f"INIT{channel}:CONT?")))
        result["trig_source"] = self.query(f"TRIG{channel}:SOUR?")
        result["readings_per_second"] = int(self.query(f"SENS{channel}:SPE?"))

        avgen = bool(int(self.query(f"SENS{channel}:AVER?")))
        avgauto = bool(int(self.query(f"SENS{channel}:AVER:COUN:AUTO?")))
        avgcnt = int(self.query(f"SENS{channel}:AVER:COUN?"))
        if not avgen:
            result["averaging"] = False
        elif avgauto:
            result["averaging"] = "auto"
        else:
            result["averaging"] = avgcnt

        # result['resolution'] = self.query(f'TRIG{channel}:SOUR')

        offseten = bool(int(self.query(f"SENS{channel}:CORR:GAIN2:STAT?")))
        if not offseten:
            result["offset"] = False
        else:
            result["offset"] = float(self.query(f"SENS{channel}:CORR:GAIN2?"))

        dutyen = bool(int(self.query(f"SENS{channel}:CORR:DCYC:STAT?")))
        if not dutyen:
            result["dutycycle"] = False
        else:
            result["dutycycle"] = float(self.query(f"SENS{channel}:CORR:DCYC?"))
        return result

    def measure_power(self, resolution=None, channel: int = None):
        channel = self.get_default_channel(default=channel)
        if resolution is not None:
            self.set_settings(resolution=resolution, channel=channel)
        # self.write('INIT{:d}:CONT 1'.format(channel))
        # self.write('INIT{:d}'.format(channel), delay=self.delay)
        result = self.query(f"FETC{channel}?", delay=self.delay)
        return float(result)

    def set_defaults(self, channel: int = None):
        self.set_settings(
            channel=channel,
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

