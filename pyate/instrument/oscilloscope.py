"""
Created on Aug 23, 2017

@author: kyleh
"""

from pyate.instrument import Instrument
import numpy as np


@Instrument.register_models(["DS1054Z", "DS1104Z"])
class Oscilloscope(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "Oscilloscope"
        self.channels = 4
        self.timescalerange = (5e-9, 50)
        self.yscalerange = (1e-3, 10)

        self._map_chan_short = {"off": "OFF", "ch1": "CH1", "ch2": "CH2", "ch3": "CH3", "ch4": "CH4", "math": "MATH"}
        self._map_trig_mode = {"edge": "EDGE"}
        self._map_channels = {"ch1": "CHAN1", "ch2": "CHAN2", "ch3": "CHAN3", "ch4": "CHAN4", "math": "MATH"}
        self._map_slope = {"pos": "POS", "neg": "NEG"}

        self._map_trig_sweep = {"auto": "AUTO", "norm": "NORM", "single": "SING"}

    def int_to_chan_str(self, x):
        return "ch{:d}".format(x)

    def get_trace(self, channel):
        self.write(":WAV:SOUR {:s}", channel)
        xorigin = float(self.query(":WAV:XOR?"))
        xreference = float(self.query(":WAV:XREF?"))
        xincrement = float(self.query(":WAV:XINC?"))
        yorigin = float(self.query(":WAV:YOR?"))
        yreference = float(self.query(":WAV:YREF?"))
        yincrement = float(self.query(":WAV:YINC?"))

        self.write(":WAV:MODE NORM")
        self.write(":WAV:FORM BYTE")

        raw = self.query_binary_values(":WAV:DATA? ", datatype="B", is_big_endian=False)

        # Scale to voltage:
        # V = (BYTE - YORigin - YREFerence) * YINCrement   From Prog. Manual
        yy = (np.array(raw, dtype="float32") - yorigin - yreference) * yincrement

        # Construct time axis
        xx = (np.arange(0, len(yy)) - xorigin - xreference) * xincrement

        return np.stack((xx, yy))

    def set_scale_x(self, scale):
        # Check for valid value
        self.check_parameter("scale", scale, float, self.timescalerange)

        # Further check to make sure scale has correct mantissa (1, 2, or 5)
        # Nevermind, I'm too lazy
        self.write(":TIM:SCAL {:g}".format(scale))

    def get_scale_x(self):
        return float(self.query(":TIM:SCAL?"))

    def set_offset_x(self, offset):
        self.check_parameter("offset", offset, float, None)

        self.write(":TIMebase:OFFSet {:g}".format(offset))

    def get_offset_x(self):
        return float(self.query(":TIMebase:OffSet?"))

    def set_scale_y(self, channel, scale):
        self.check_parameter("channel", channel, int, (1, self.channels))
        self.check_parameter("scale", scale, float, None)

        # Used to check for valid scale ranging
        # Decided to leave this out for now
        # probeRatio = self.get_probe_ratio(channel)
        # yscalelimits = (self.yscalerange[0]*probeRatio,
        #                self,yscalerange[1]*proberatio)

        # Further check to make sure scale has correct mantissa (1, 2, or 5)
        # Nevermind, I'm too lazy
        self.write(":CHAN{:d}:SCAL {:g}".format(channel, scale))

    def get_scale_y(self, channel):
        self.check_parameter("channel", channel, int, (1, self.channels))
        return float(self.query(":CHAN{:g}:SCAL?").format(channel))

    def set_offset_y(self, channel, offset):
        self.check_parameter("channel", channel, int, (1, self.channels))
        self.check_parameter("offset", offset, float, None)
        self.write(":CHAN{:d}:OFFSet {:g}".format(channel, offset))

    def get_offset_y(self, channel):
        self.check_parameter("channel", channel, int, (1, self.channels))
        return float(self.query(":CHAN{:d}:OffSet?".format(channel)))

    def get_probe_ratio(self, channel):
        self.check_parameter("channel", channel, int, (1, self.channels))
        return float(self.query(":CHAN{:d}?".format(channel)))

    def set_cursor(self, sourcea=None, sourceb=None, ax=None, bx=None):
        self.write(":CURSor:MODE TRACk")
        if sourcea is not None:
            self.check_parameter("sourcea", sourcea, int, (1, self.channels))
            channel_name = self.int_to_chan_str(sourcea)
            self.write(":CURSor:TRACk:SOURce1 {:s}".format(self._map_channels[channel_name]))
        if sourceb is not None:
            self.check_parameter("sourceb", sourceb, int, (1, self.channels))
            channel_name = self.int_to_chan_str(sourcea)
            self.write(":CURSor:TRACk:SOURce2 {:s}".format(self._map_channels[channel_name]))

        if (ax is not None) or (bx is not None):
            # Figure out time scale
            offset = self.get_offset_x()
            scale = self.get_scale_x()
            xstep = scale * 12 / 600
            self.logger.debug("offset=%g  scale=%g  xstep=%g", offset, scale, xstep)

            # minx = -297*xstep + offset
            # maxx = +294*xstep + offset

        if ax is not None:
            self.check_parameter("ax", ax, float, None)
            xpixel = round((ax - offset) / xstep + 300)
            self.logger.debug("Set AX to %d", xpixel)
            self.write(":CURSor:TRACk:AX {:d}".format(xpixel))
        if bx is not None:
            self.check_parameter("bx", bx, float, None)
            xpixel = round((bx - offset) / xstep + 300)
            self.logger.debug("Set BX to %d", xpixel)
            self.write(":CURSor:TRACk:BX {:d}".format(xpixel))

    def get_cursor_values(self):
        d = {}
        d["ax"] = float(self.query(":CURSor:TRACk:AXValue?"))
        d["bx"] = float(self.query(":CURSor:TRACk:BXValue?"))
        d["ay"] = float(self.query(":CURSor:TRACk:AYValue?"))
        d["by"] = float(self.query(":CURSor:TRACk:BYValue?"))
        return d

    def set_trigger(self, mode=None, source=None, slope=None, level=None, sweep=None):

        if mode is not None:
            self.check_parameter("mode", mode, str, self._map_trig_mode)
            mode_parsed = self._map_trig_mode[mode]
            self.write(":TRIG:MODE {:s}".format(mode_parsed))
        else:
            mode_parsed = self.get_trigger()["mode"]

        if sweep is not None:
            self.check_parameter("sweep", sweep, str, self._map_trig_sweep)
            self.write(":TRIG:SWEep {:s}".format(self._map_trig_sweep[sweep]))

        if mode_parsed == "EDGE":
            if level is not None:
                self.check_parameter("level", level, float, None)
                self.write(":TRIG:EDGe:LEVel {:g}".format(level))
            if source is not None:
                if isinstance(source, int):
                    self.check_parameter("source", source, int, (1, self.channels))
                    source = self.int_to_chan_str(source)
                else:
                    self.check_parameter("source", source, str, self._map_channels)
                self.write(":TRIG:EDGe:SOUR {:s}".format(self._map_channels[source]))
            if slope is not None:
                self.check_parameter("slope", slope, str, self._map_slope)
                self.write(":TRIG:EDGe:SLOP {:s}".format(self._map_slope[slope]))

    def get_trigger(self):
        d = {}
        d["mode"] = self.query(":TRIG:MODE?")
        d["status"] = self.query(":TRIG:STAT?")

        if d["mode"] == "EDGE":
            d["level"] = float(self.query(":TRIG:EDGe:LEVel?"))
            d["source"] = self.query(":TRIG:EDGe:SOUR?")
            d["slope"] = self.query(":TRIG:EDGe:SLOP?")

        return d

    def get_measurement(self, channel, meas):
        self.check_parameter("channel", channel, int, (1, self.channels))
        channel_name = self.int_to_chan_str(channel)

        _map_meas = {
            "dutycycle": "PDUTy",
            "pulsewidth": "PWIDth",
            "period": "PERiod",
            "vlower": "VLOWer",
            "vupper": "VUPper",
        }

        # if meas is not None:
        self.check_parameter("meas", meas, str, _map_meas)
        return float(self.query(":MEAS:ITEM? {:s},{:s}".format(_map_meas[meas], self._map_channels[channel_name])))
