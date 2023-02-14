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

from math import log10
import time

from pyate.instrument import Instrument
from pyate.instrument.error import InstrumentNothingToRead
from pyate.instrument.instrument import pyvisaExceptionHandler


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
        self.delay = (
            0.05  # Prevent instrument from getting hung up by talking to it too fast
        )


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

    def set_duty_cycle(
        self, value: float = None, enable: bool = None, channel: int = None
    ):
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
        trigger_source: str = None,
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
        if trigger_source is not None:
            self.write(f"TRIG{channel}:SOUR {trigger_source}")
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
        result["trigger_source"] = self.query(f"TRIG{channel}:SOUR?")
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
            trigger_source="IMM",
            averaging="auto",
            resolution=3,
            offset=False,
            dutycycle=False,
        )

        # self.set_offset(channel, enable=False, value=0.)
        # self.set_duty_cycle(channel, enable=False, value=0.01)


@Instrument.register_models(["NRP-Z[0-9][0-9]"])
class PowerMeterRohdeNRP(PowerMeter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "PowerMeterRohdeNRP"

        # increase timeout
        ##### WARNING!!!  Apparently pyfisa timeout is in milliseconds
        # Prologix is in seconds
        # self.res.timeout = 500.0          # This is due to periodically long read times
        self.delay = (
            0.05  # Prevent instrument from getting hung up by talking to it too fast
        )

        self.resource.read_termination = (
            ""  # The ZRP does not seem to use termination chars by default
        )
        self.set_default_channel(1)  # Single channel device

    mapping_trigger_source = (
        ("1", "hold", "HOLD"),
        ("2", "immediate", "IMM"),
        ("4", "internal", "INT"),
        ("8", "bus", "BUS"),
        ("16", "external", "EXT"),
    )

    mapping_on_off = (("1", False, "OFF"), ("2", True, "ON"))

    mapping_avg_tcon = (("1", "moving", "MOV"), ("2", "repeat", "REP"))

    mapping_function = (
        ("POWER:AVG", "continuous_average", "POWER:AVG"),
        ("POWER:TSLOT:AVG", "timeslot_average", "POWER:TSLOT:AVG"),
        ("POWER:BURST:AVG", "burst_average", "POWER:BURST:AVG"),
        ("XTIME:POWER", "trace", "XTIME:POWER"),
    )

    mapping_sampling = (("1", "134.4e3", "FREQ1"), ("2", "119.467e3", "FREQ2"))

    mapping_sensitivity = (("0", "high", "0"), ("1", "medium", "1"), ("2", "low", "2"))

    mapping_auto_type = (
        ("1", "resolution", "RESolution"),
        ("2", "ns_ratio", "NSRatio"),
    )

    # @pyvisaExceptionHandler
    # def write(self, command, delay=0.0, retries=3):
    #     result = self.res.visalib.write(self.res.session, command)
    #     time.sleep(delay)
    #     return result

    # @pyvisaExceptionHandler
    # def read(self, retries=3):
    #     return self.res.visalib.read(self.res.session, 1024)[0].decode()

    def check_error(self):
        return not bool(int(self.query("SYST:ERR?")))

    def wait_for_completion(self):
        for k in range(20):
            status = int(self.query("STAT:OPER:COND?"))
            if status == 0:
                break
            time.sleep(0.05)

    def calibration_zero_sensor(self):
        self.write("CAL:ZERO:AUTO ONCE")

    def get_frequency(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        return float(self.query("SENS:FREQ?"))

    def set_frequency(self, frequency, channel: int = None):
        channel = self.get_default_channel(default=channel)
        self.write(f"SENS:FREQ {frequency}")

    def set_resolution(self, resolution, channel: int = None):
        channel = self.get_default_channel(default=channel)
        self.write("SENSe:AVERage:COUNt:AUTO ON")
        self.write("SENSe:AVERage:COUNt:AUTO:TYPE RES")
        self.write(f"SENS:AVER:COUN:AUTO:RES {resolution}")

    def w_to_dbm(self, power_watts):
        # Cap value at -174 dBm as the sensor has a habit of returning negative watt readings
        # with no signal present
        result = max(power_watts, 3.9811e-21)
        return 10 * log10(result) + 30

    def measure_power(self, resolution=None):
        self.wait_for_completion()
        if resolution is not None:
            self.set_resolution(resolution)

        self.wait_for_completion()
        self.write("INIT:IMM")
        result = self.query("FETCH?")
        result = float(result.split(",")[0])

        return self.w_to_dbm(result)

    def get_settings(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        result = {}
        result["function"] = self.map_value(
            self.query("SENSe:FUNCtion?"), "from", self.mapping_function
        )
        result["continuous"] = self.map_value(
            self.query("INIT:CONT?"), "from", self.mapping_on_off
        )
        result["trigger_source"] = self.map_value(
            self.query("TRIG:SOUR?"), "from", self.mapping_trigger_source
        )
        result["sample_rate"] = self.map_value(
            self.query("SENSe:SAMPling?"), "from", self.mapping_sampling
        )

        result["frequency"] = float(self.query("SENS:FREQ?"))

        result["range_sensitivity"] = self.map_value(
            self.query("SENSe:RANGe?"), "from", self.mapping_sensitivity
        )
        result["range_auto"] = self.map_value(
            self.query("SENSe:RANGe:AUTO?"), "from", self.mapping_on_off
        )

        avgen = self.map_value(
            self.query("SENS:AVER:STAT?"), "from", self.mapping_on_off
        )
        avgauto = self.map_value(
            self.query("SENS:AVER:COUN:AUTO?"), "from", self.mapping_on_off
        )
        avgcnt = int(self.query("SENS:AVER:COUN?"))
        avgtcon = self.map_value(
            self.query("SENS:AVER:TCON?"), "from", self.mapping_avg_tcon
        )
        # SENSe:AVERage:COUNt:AUTO ONCE

        if not avgen:
            result["averaging"] = False
        elif avgauto:
            result["averaging"] = "auto"
        else:
            result["averaging"] = avgcnt

        result["average_count"] = avgcnt
        result["average_auto_type"] = self.map_value(
            self.query("SENSe:AVERage:COUNt:AUTO:TYPE?"), "from", self.mapping_auto_type
        )
        result["average_mtime"] = float(self.query("SENSe:AVERage:COUNt:AUTO:MTIM?"))
        result["average_nsratio"] = float(
            self.query("SENSe:AVERage:COUNt:AUTO:NSRatio?")
        )
        result["average_resolution"] = int(
            self.query("SENSe:AVERage:COUNt:AUTO:RESolution?")
        )
        result["average_aperture_time"] = float(self.query(":SENS:POW:AVG:APER?"))
        result["averaging_smooth"] = self.map_value(
            self.query("SENSe:POWer:AVG:SMOothing:STATe?"), "from", self.mapping_on_off
        )
        result["averaging_tcon"] = avgtcon

        result["buffer"] = self.map_value(
            self.query(":SENS:POW:AVG:BUFF:STAT?"), "from", self.mapping_on_off
        )

        offseten = self.map_value(
            self.query("SENS:CORR:OFFS?"), "from", self.mapping_on_off
        )
        if not offseten:
            result["offset"] = False
        else:
            result["offset"] = float(self.query("SENS:CORR:OFFS?"))

        dutyen = bool(int(self.query("SENS:CORR:DCYC:STAT?")))
        if not dutyen:
            result["dutycycle"] = False
        else:
            result["dutycycle"] = float(self.query("SENS:CORR:DCYC?"))

        result["min_power"] = self.w_to_dbm(float(self.query("SYSTem:MINPower?")))
        return result


@Instrument.register_models(["8542C"])
class PowerMeterGigatronics(Instrument):
    def __init__(self, *args, channel=None, **kwargs):
        super().__init__(*args, channel=channel, **kwargs)
        self.driver_name = "PowerMeterGigatronics"
        self.delay = (
            0.05  # Prevent instrument from getting hung up by talking to it too fast
        )

    def set_offset(self, value: float = None, enable: bool = None, channel: int = None):
        channel = self.get_default_channel(default=channel)
        if value is not None:
            # Set meter offset
            self.write(f"{channel}E:OS:{value}:EN")

        if enable is not None:
            # Turn offset on/off
            self.write(f"{channel}E:OF{enable}")

    def set_duty_cycle(
        self, value: float = None, enable: bool = None, channel: int = None
    ):
        raise NotImplementedError()

    def get_frequency(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        # Might not be possible in gigatronics?
        return float(self.query("{channel}E:FR?"))

    def set_frequency(self, frequency, channel: int = None):
        channel = self.get_default_channel(default=channel)

        self.write(f"{channel:d}E:FR {frequency/1e9:f}GHZ")

    def set_settings(
        self,
        channel: int = None,
        readings_per_second=None,
        continuous=None,
        trigger_source=None,
        averaging=None,
        resolution=None,
        offset=None,
        dutycycle=None,
    ):

        channel = self.get_default_channel(default=channel)

        # This must be set before averaging as it will reset the averaging settings
        if resolution is not None:
            init_status = self.query(f"{channel:d}E:RE")
            self.write(f"{channel:d}E:RE:2:EN")
            self.write(f"{channel:d}E:EN {init_status}")

        if continuous is not None:
            self.write(f"CW {int(continuous)}")
        if trigger_source is not None:
            self.write(f"{channel:d}E:TR2?")
        if readings_per_second is not None:
            self.write(f"SENS{channel:d}:SPE {readings_per_second:d}")
        if averaging is not None:
            if averaging == False:
                self.write(f"{channel:d}E:FA")
            elif (averaging == "auto") or (averaging == "AUTO"):
                self.write(f"{channel:d}E FA")
                self.write(f"{channel:d}E FA PCT")
            else:
                self.write(f"{channel:d}E:FM")
                self.write(f"{channel:d}E:FM")
                self.write(f"{channel:d}E FM {averaging:g} EN")

        if offset is not None:
            if isinstance(offset, bool):
                self.write(f"{channel:d}E:OF{offset:g}")
            else:
                self.write(f"{channel:d}E:OF1")
                self.write(f"{channel:d}E OS {offset:g} EN")

        if dutycycle is not None:
            if isinstance(dutycycle, bool):
                self.write(f"{channel:d}E:DC{dutycycle:d}")
            else:
                self.write(f"{channel:d}E:DC1")
                self.write(f"{channel:s}E DY {dutycycle * 100.0:f} PCT")

    def get_settings(self, channel: int = None):
        channel = self.get_default_channel(default=channel)
        result = {}
        result["continuous"] = bool(int(self.query(f"PEAK {channel:d} CW")))
        result["trigger_source"] = self.query(f"{channel:d}E:TR3?")
        result["readings_per_second"] = int(self.query(f"SENS{channel:d}:SPE?"))

        avgen = bool(int(self.query(f"{channel:d}E:FM?")))
        avgauto = bool(int(self.query(f"{channel:d}E FA?")))
        avgcnt = int(self.query(f"{channel:d}E FA PCT?"))
        if not avgen:
            result["averaging"] = False
        elif avgauto:
            result["averaging"] = "auto"
        else:
            result["averaging"] = avgcnt

        # result['resolution'] = self.query('TRIG{:d}:SOUR'.format(channel))

        offseten = bool(int(self.query(f"{channel:d}E:OS?")))
        if not offseten:
            result["offset"] = False
        else:
            result["offset"] = float(self.query(f"{channel:d}E:OF1?"))

        dutyen = bool(int(self.query(f"{channel:d}E:DC1?")))
        if not dutyen:
            result["dutycycle"] = False
        else:
            result["dutycycle"] = float(self.query(f"{channel:d}E:DC1"))
        return result

    def measure_power(self, resolution=None, channel: int = None):
        channel = self.get_default_channel(default=channel)
        if resolution is not None:
            self.set_settings(resolution=resolution, channel=channel)
        # self.write('INIT{:d}:CONT 1'.format(channel))
        # self.write('INIT{:d}'.format(channel), delay=self.delay)
        result = self.query(f"{channel:d}P?", delay=self.delay)
        return float(result)

    def set_defaults(self, channel: int = None):
        self.set_settings(
            channel=channel,
            readings_per_second=40,
            continuous=True,
            trigger_source="IMM",
            averaging="auto",
            resolution=3,
            offset=False,
            dutycycle=False,
        )
