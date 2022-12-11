"""
Created on Jul 12, 2017

@author: kyleh
"""

from pyate.instrument import Instrument
import time


class WaveformGenerator(Instrument):
    _scpi_prefix = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "WaveformGenerator"

    def get_output_state(self, channel):
        return True if self.query(":OUTP{:d}?".format(channel)) == "ON" else False

    def set_output_state(self, channel, state):
        self.write(":OUTP{:d} {:s}".format(channel, "ON" if state else "OFF"))
        self.query("*OPC?")
        time.sleep(0.1)


@Instrument.register_models(["DG1032Z"])
class WaveformGeneratorRigol(WaveformGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "WaveformGeneratorRigol"
        self._scpi_prefix = ":APPL{:d}"
        self.delay = 0.1

        self._map_slope = {"pos": "POS", "neg": "NEG"}

    def send_waveform(self, data, samplerate, amplitude, offset=0, channel=1):
        """
        Input waveform is assumed to be signed.
        Output range is symmetric about zero.
          Fullscale negative = -8192
          Fullscale positive = +8191
        """

        # Attempt to clear VOLATILE meomory
        # self.write('DATA{:d}:POIN VOLATILE,9'.format(channel))

        # Offset waveform
        # Rigol instrument expects value to be between 0 and 16383
        # Zero output is 8192
        data = data + 2 ** 13

        self.write(":SOUR{:d}:APPL:ARB {:g}, {:g}, {:g}".format(channel, samplerate, amplitude, offset))
        self.query("*OPC?")
        # There does not seem to be the capability of setting binary
        # data format or byte order.
        # Looks like the default is:
        # Little endian
        # Short INT
        # Since it is only 14 bits, sign doesn't matter?
        self.write_binary_values(
            ":SOUR{:d}:DATA:DAC VOLATILE,".format(channel), data, datatype="h", is_big_endian=False
        )
        self.query("*OPC?")
        time.sleep(self.delay)

    def setup_burst(self, channel, **kwargs):
        if "mode" in kwargs:
            arg_value = kwargs["mode"]
            _map = {"trig": "TRIG", "gate": "GATE"}
            self.check_parameter("mode", arg_value, str, _map)
            self.write(":SOUR{:d}:BURS:MODE {:s}".format(channel, _map[arg_value]))

        if "cycles" in kwargs:
            arg_value = kwargs["cycles"]
            self.check_parameter("cycles", arg_value, int, range(1, 9999999))
            self.write(":SOUR{:d}:BURS:NCYC {:d}".format(channel, arg_value))

        if "idle" in kwargs:
            arg_value = kwargs["idle"]
            _map = {"first": "FPT", "top": "TOP", "center": "CENTER", "bottom": "BOTTOM"}
            self.check_parameter("idle", arg_value, str, _map)
            self.write(":SOUR{:d}:BURS:IDLE {:s}".format(channel, _map[arg_value]))

        if "source" in kwargs:
            arg_value = kwargs["source"]
            _map = {"ext": "EXT", "int": "INT"}
            self.check_parameter("source", arg_value, str, _map)
            self.write(":SOUR{:d}:BURS:TRIG:SOUR {:s}".format(channel, _map[arg_value]))

        if "slope" in kwargs:
            arg_value = kwargs["slope"]
            _map = {"pos": "POS", "neg": "NEG"}
            self.check_parameter("slope", arg_value, str, _map)
            self.write(":SOUR{:d}:BURS:TRIG:SLOP {:s}".format(channel, _map[arg_value]))

        if "state" in kwargs:
            arg_value = kwargs["state"]
            self.check_parameter("state", arg_value, bool, None)
            arg_value = "ON" if arg_value else "OFF"
            self.write(":SOUR{:d}:BURS:STAT {:s}".format(channel, arg_value))

        if "delay" in kwargs:
            arg_value = kwargs["delay"]
            self.check_parameter("delay", arg_value, float, None)
            self.write(":SOUR{:d}:BURS:TDELay {:g}".format(channel, arg_value))

        self.query("*OPC?")
        time.sleep(self.delay)

    def get_mode(self, channel):
        """ Queries instrument for current mode and returns relevant settings"""
        prop_waveform = self.query("SOUR{:d}:APPL?".format(channel))

        # For whatever reason it puts double quotes around it
        prop_waveform = prop_waveform.replace('"', "")

        prop_values = prop_waveform.split(sep=",")

        d = {}
        d["waveform"] = prop_values[0]
        d["frequency"] = float(prop_values[1])
        d["amplitude"] = float(prop_values[2])
        d["offset"] = float(prop_values[3])
        d["phase"] = float(prop_values[4])
        d["period"] = 1 / d["frequency"]
        d["vhi"] = d["offset"] + d["amplitude"] / 2
        d["vlo"] = d["offset"] - d["amplitude"] / 2
        if d["waveform"] == "PULSE":
            d["pulsewidth"] = float(self.query("SOUR{:d}:PULS:WIDT?".format(channel)))
        d["dutycycle"] = d["pulsewidth"] / d["period"]
        return d

    def setup_pulse(self, channel, mode=None, period=None, width=None, vlow=None, vhigh=None):
        # state_start = self.get_output_state(channel)
        # self.set_output_state(channel, False)
        self.write(":SOUR{:d}:APPL:PULS".format(channel))
        # self.write(':SOUR{:d}:PULS:HOLD WIDT'.format(channel))
        if period is not None:
            self.write(":SOUR{:d}:FUNC:PULS:PER {:g}".format(channel, period))
        if width is not None:
            self.write(":SOUR{:d}:FUNC:PULS:WIDT {:g}".format(channel, width))
        if vhigh is not None:
            self.write(":SOUR{:d}:VOLT:LEV:HIGH {:g}".format(channel, vhigh))
        if vlow is not None:
            self.write(":SOUR{:d}:VOLT:LEV:LOW {:g}".format(channel, vlow))

        self.query("*OPC?")
        # The following is required for the above settigns to take effect
        # The front panel of the instrument will show the new seetings,
        # but the actual waveform output will remain unchanged
        time.sleep(0.1)
        # self.set_output_state(channel, state_start)

    def set_channel(self, channel, sync=None, syncpol=None):
        self.check_parameter("channel", channel, int, (1, 2))
        if syncpol is not None:
            self.check_parameter("syncpol", syncpol, str, self._map_slope)
            self.write(":OUTP{:d}:SYNC:POL {:s}".format(channel, self._map_slope[syncpol]))
        if sync is not None:
            self.check_parameter("sync", sync, bool, None)
            self.write(":OUTP{:d}:SYNC:STAT {:d}".format(channel, int(sync)))


@Instrument.register_models(["81150A"])
class WaveformGenerator81150(WaveformGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "WaveformGenerator81150"

        self._scpi_prefix = ":APPL{:d}"

    def send_waveform(self, data, samplerate, amplitude, offset=0, channel=1):
        """
        Input waveform is assumed to be signed.
        Output range is symmetric about zero.
          Fullscale negative = -8192
          Fullscale positive = +8191
        """

        # Calculate repeat frequency since this is what the ARB
        # wants instaed of sample rate
        freq = samplerate / len(data)

        # Assume default of BigEndian is still set
        # Should explicitly set this though.
        self.write_binary_values("DATA{:d}:DAC VOLATILE,".format(channel), data, datatype="h", is_big_endian=True)
        self.query("*OPC?")
        self.write("FUNC{:d}:USER VOLATILE".format(channel))
        self.write("APPL{:d}:USER {:g}, {:g}, {:g}".format(channel, freq, amplitude, offset))
        self.query("*OPC?")
        time.sleep(0.1)

    def setup_burst(self, channel):
        self.write(":ARM:IMP MAX")  # Set EXT-IN imput impedance to 10kOhm
        self.write(":ARM:SOUR{:d} EXT".format(channel))
        self.write(":ARM:SLOP{:d} POS".format(channel))
        self.query("*OPC?")
        time.sleep(0.1)

    def setup_pulse(self, channel, mode, period, width, vlow, vhigh):
        # state_start = self.get_output_state(channel)
        # self.set_output_state(channel, False)
        self.write(":APPL{:d}:PULS".format(channel))
        # self.write(':SOUR{:d}:PULS:HOLD WIDT'.format(channel))
        self.write(":PER{:d} {:g}".format(channel, period))
        self.write(":FUNC{:d}:PULS:WIDT {:g}".format(channel, width))
        self.write(":VOLT{:d}:HIGH {:g}".format(channel, vhigh))
        self.write(":VOLT{:d}:LOW {:g}".format(channel, vlow))
        self.query("*OPC?")
        # The following is required for the above settigns to take effect
        # The front panel of the instrument will show the new seetings,
        # but the actual waveform output will remain unchanged
        time.sleep(0.1)
        # self.set_output_state(channel, state_start)
