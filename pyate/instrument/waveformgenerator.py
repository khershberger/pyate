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
        self.drivername = "WaveformGenerator"

    def getOutputState(self, channel):
        return True if self.query(":OUTP{:d}?".format(channel)) == "ON" else False

    def setOutputState(self, channel, state):
        self.write(":OUTP{:d} {:s}".format(channel, "ON" if state else "OFF"))
        self.query("*OPC?")
        time.sleep(0.1)


@Instrument.registerModels(["DG1032Z"])
class WaveformGeneratorRigol(WaveformGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = "WaveformGeneratorRigol"
        self._scpi_prefix = ":APPL{:d}"
        self.delay = 0.1

        self._mapSlope = {"pos": "POS", "neg": "NEG"}

    def sendWaveform(self, data, samplerate, amplitude, offset=0, channel=1):
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

    def setupBurst(self, channel, **kwargs):
        if "mode" in kwargs:
            argValue = kwargs["mode"]
            _map = {"trig": "TRIG", "gate": "GATE"}
            self.checkParameter("mode", argValue, str, _map)
            self.write(":SOUR{:d}:BURS:MODE {:s}".format(channel, _map[argValue]))

        if "cycles" in kwargs:
            argValue = kwargs["cycles"]
            self.checkParameter("cycles", argValue, int, range(1, 9999999))
            self.write(":SOUR{:d}:BURS:NCYC {:d}".format(channel, argValue))

        if "idle" in kwargs:
            argValue = kwargs["idle"]
            _map = {"first": "FPT", "top": "TOP", "center": "CENTER", "bottom": "BOTTOM"}
            self.checkParameter("idle", argValue, str, _map)
            self.write(":SOUR{:d}:BURS:IDLE {:s}".format(channel, _map[argValue]))

        if "source" in kwargs:
            argValue = kwargs["source"]
            _map = {"ext": "EXT", "int": "INT"}
            self.checkParameter("source", argValue, str, _map)
            self.write(":SOUR{:d}:BURS:TRIG:SOUR {:s}".format(channel, _map[argValue]))

        if "slope" in kwargs:
            argValue = kwargs["slope"]
            _map = {"pos": "POS", "neg": "NEG"}
            self.checkParameter("slope", argValue, str, _map)
            self.write(":SOUR{:d}:BURS:TRIG:SLOP {:s}".format(channel, _map[argValue]))

        if "state" in kwargs:
            argValue = kwargs["state"]
            self.checkParameter("state", argValue, bool, None)
            argValue = "ON" if argValue else "OFF"
            self.write(":SOUR{:d}:BURS:STAT {:s}".format(channel, argValue))

        if "delay" in kwargs:
            argValue = kwargs["delay"]
            self.checkParameter("delay", argValue, float, None)
            self.write(":SOUR{:d}:BURS:TDELay {:g}".format(channel, argValue))

        self.query("*OPC?")
        time.sleep(self.delay)

    def getMode(self, channel):
        """ Queries instrument for current mode and returns relevant settings"""
        propWaveform = self.query("SOUR{:d}:APPL?".format(channel))

        # For whatever reason it puts double quotes around it
        propWaveform = propWaveform.replace('"', "")

        propValues = propWaveform.split(sep=",")

        d = {}
        d["waveform"] = propValues[0]
        d["frequency"] = float(propValues[1])
        d["amplitude"] = float(propValues[2])
        d["offset"] = float(propValues[3])
        d["phase"] = float(propValues[4])
        d["period"] = 1 / d["frequency"]
        d["vhi"] = d["offset"] + d["amplitude"] / 2
        d["vlo"] = d["offset"] - d["amplitude"] / 2
        if d["waveform"] == "PULSE":
            d["pulsewidth"] = float(self.query("SOUR{:d}:PULS:WIDT?".format(channel)))
        d["dutycycle"] = d["pulsewidth"] / d["period"]
        return d

    def setupPulse(self, channel, mode=None, period=None, width=None, vlow=None, vhigh=None):
        # stateStart = self.getOutputState(channel)
        # self.setOutputState(channel, False)
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
        # self.setOutputState(channel, stateStart)

    def setChannel(self, channel, sync=None, syncpol=None):
        self.checkParameter("channel", channel, int, (1, 2))
        if syncpol is not None:
            self.checkParameter("syncpol", syncpol, str, self._mapSlope)
            self.write(":OUTP{:d}:SYNC:POL {:s}".format(channel, self._mapSlope[syncpol]))
        if sync is not None:
            self.checkParameter("sync", sync, bool, None)
            self.write(":OUTP{:d}:SYNC:STAT {:d}".format(channel, int(sync)))


@Instrument.registerModels(["81150A"])
class WaveformGenerator81150(WaveformGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = "WaveformGenerator81150"

        self._scpi_prefix = ":APPL{:d}"

    def sendWaveform(self, data, samplerate, amplitude, offset=0, channel=1):
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

    def setupBurst(self, channel):
        self.write(":ARM:IMP MAX")  # Set EXT-IN imput impedance to 10kOhm
        self.write(":ARM:SOUR{:d} EXT".format(channel))
        self.write(":ARM:SLOP{:d} POS".format(channel))
        self.query("*OPC?")
        time.sleep(0.1)

    def setupPulse(self, channel, mode, period, width, vlow, vhigh):
        # stateStart = self.getOutputState(channel)
        # self.setOutputState(channel, False)
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
        # self.setOutputState(channel, stateStart)
