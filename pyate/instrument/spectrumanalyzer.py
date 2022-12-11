"""
Created on Jul 4, 2017

@author: kyleh
"""

from pyate.instrument import Instrument
import numpy as np


class Vsa(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "Vsa"

    def check_if_numeric(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    ### System Commands
    def preset(self):
        self.write("*RST")
        self.query("*OPC?")

    def align(self, automatic=False):
        if automatic:
            self.write(":CAL:AUTO ON")
        else:
            self.write(":CAL:AUTO OFF")
            self.write(":CAL:ALL")
            self.query("*OPC?")

            # try:
            #    # Check how many minutes passed since last
            #    # alignment
            #    elapsed_time=toc(LAST_ALIGMENT_TIME)/60
            # catch:
            #    # Alignment has never done since program
            #    # started
            #    elapsed_time=1000
            #
            # if elapsed_time>ALIGNMENT_INTERVAL
            #    self.logger.info('{:g} minutes since last VSA alignment - Alignment is needed'.format(elapsed_time))
            #    PriorTimeOut = v_vsa.TimeOut
            #    v_vsa.Timeout=200
            #    self.write':CAL:AUTO OFF')
            #    self.write(':CAL:ALL')
            #    result = self.query(v_vsa,'*OPC?')
            #    v_vsa.Timeout=PriorTimeOut
            #    LAST_ALIGMENT_TIME=tic
            # else
            #    printlog(3, sprintf('%g minutes since last VSA alignment - Skipping alignment',elapsed_time))

    def init(self):
        self.write("INIT:IMM")

    def opc(self):
        return self.query("*OPC?")

    def options(self):
        return self.query(":SYST:OPTions?")

    def set_block_format(self, datatype):
        if datatype == "ascii":
            self.write(":FORM ASC")
        elif datatype == "single":
            self.write(":FORM REAL32")
        elif datatype == "double":
            self.write(":FORM REAL")
        else:
            self.logger.warning("{:s}.set_block_format(): Unknown mode {:s}".format(self.driver_name, datatype))

    ### Spectrum Analyzer Commands

    def set_bandwidth(self, video=None, resolution=None):
        if video is not None:
            if video == "auto":
                self.write("BAND:VID:AUTO ON")
            else:
                self.write("BAND:VID {:g} HZ".format(video))

        if resolution is not None:
            if resolution == "auto":
                self.write("BAND:RES:AUTO ON")
            else:
                self.write("BAND:RES {:g} HZ".format(resolution))

    def get_resolution_bandwidth(self):
        return self.query("BAND:RES?")

    def get_video_bandwidth(self):
        return self.query("BAND:VID?")

    def set_frequency(self, start=None, stop=None, center=None, span=None):
        if (start is not None or stop is not None) and (center is not None or span is not None):
            self.logger.warning(
                "{:s}.setFreq(): Conflicting parameters specified.  Defaulting to center/span".format(self.driver_name)
            )

        if start is not None:
            self.write("FREQ:STARt {:g} GHZ", start / 1e9)

        if stop is not None:
            self.write("FREQ:STOP {:g} GHZ", stop / 1e9)

        if center is not None:
            self.write("FREQ:CENTer {:g} GHZ", center / 1e9)

        if span is not None:
            self.write("FREQ:SPAN {:g} HZ", span)

    def set_attenuation(self, attenuation):
        if attenuation == "AUTO":
            self.write(":SENse:POWer:RF:ATTenuation:AUTO ON")
        else:
            self.write(":SENse:POWer:RF:ATTenuation {:g}".format(float(attenuation)))

    def get_ref_level(self):
        return self.query(":DISP:WIND1:TRAC:Y:RLEV?")

    def set_ref_level(self, level):
        self.write(":DISP:WIND1:TRAC:Y:RLEV {:g} dBm".format(level))

    def set_y_axis(self, scale=100, ref_position=1.0):
        ref_positionPct = round(100 * ref_position)
        self.write(":DISP:TRAC:Y {:g}".format(scale))
        self.write(":DISP:TRAC:Y:RPOS {:d}PCT".format(ref_positionPct))

    def sweep_time(self, sweeptime):
        self.write("SENS:SWE:TIME {:g}".format(float(sweeptime)))

    def set_markerX(self, xvalue, marker=1):
        self.write("CALC:MARK{:d}:X {:g}".format(marker, xvalue))

    def get_marker(self, marker=1):
        xvalue = self.query("CALC:MARK{:d}:X?".format(marker))
        yvalue = self.query("CALC:MARK{:d}:Y?".format(marker))
        xvalue = float(xvalue)
        yvalue = float(yvalue)
        return (xvalue, yvalue)


# @Instrument.register_models(['UNK'])
class VsaAgilent(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "VsaAgilent"

    def get_mode(self):
        mode = self.query("INST:SEL?")

        modes = {"WIMAXOFDMA": "wimax", "SA": "spectrum", "VSA": "vsa", "VSA89601": "vsa89601", "WLAN": "wlan"}
        return modes.get(mode, "Unknown")

    def init_baseband_iq(self):
        pass

    #         self.write( ':INST BASIC')                 % Switch to IQ analyzer mode
    #         self.write( ':CONF:WAV')                   % Waveform analysis measurement
    #         self.write( ':ROSC:EXT:FREQ 10 MHz')       % Set External reference to 10 MHz
    #         self.write( ':ROSC:SOUR EXT')              % Select external reference
    #         self.write( ':TRIG:WAV:SOUR EXT1')         % External Trigger
    #         self.write( ':INIT:CONT OFF')              % Single trigger
    #         self.write( ':WAV:AVER:STAT OFF')          % TURN AVERAGING OFF

    def iq_sweep_time(self):
        pass

    #         self.write( sprintf(':WAV:SWE:TIME %g', varargin{k+1}))

    def iq_bandwidth(self):
        """
        Information BW
        """
        # self.write( sprintf(':WAV:BAND %g', varargin{k+1}))

    def iq_samplerate(self):
        """
        IQ Sample Rate
        """
        # self.write( sprintf(':WAV:SRAT %g', varargin{k+1}))

    def iq_fetch_data(self):
        """
        This assumes that a measurement has already been triggered 
        and aquired.  All that needs to be done is load the result
        into the output buffer and read it
        """

        """
        self.write( ':FORM:BORD SWAP')         % Set to little-endian byte order (PC)
        
        % Don't know if this works....
        self.write( ':FORM REAL,32')           % Set to 64 bit real numbers (32 should work as well)
        self.write( ':FETCh:WAV1?')
        params = binblockread(v_vsa, 'single')
        % Documented on page 304 of X-Series signal analyzer I/Q
        % mode users and programmers reference
        %
        % 1: Sample time
        % 2: Mean Power (latest acquisition only)
        % 3: Mean Power (averaged)
        % 4: # of samples
        % 5: Peak-to-mean ratio
        % 6: Maximum value
        % 7: Minimum value
        result = struct()
        result.t_sample = params(1)               % Sample time
        result.f_sample = 1/result.t_sample       % Calc sample rate
        result.p_mean   = params(2)               % Mean power in dBm
        result.num_samples = params(4)            % # of samples
        
        % Close interface and reopen with correct buffer size
        fclose(v_vsa)
        v_vsa.InputBufferSize = 8*result.num_samples + 256
        fopen(v_vsa)
        
        self.write( ':FETCh:WAV0?')
        sadata = binblockread(v_vsa, 'single')

        sadata = transpose(reshape(sadata, 2, length(sadata)/2))
        result.iq = complex(sadata(:,1), sadata(:,2))
        """
        pass

    def set_mode(self, mode="spectrum"):
        if mode == "spectrum":
            self.write(":INST SA")
            self.write("CONFigure:SANalyzer")
        elif mode == "wimax":
            self.write(":INST WIMAXOFDMA")
            self.query("*OPC?")
        elif mode == "wlan":
            self.write(":INST WLAN")
            self.write(":RAD:STAN AG")
            self.query("*OPC?")
        elif mode == "vsa":
            self.write(":INST VSA")
        else:
            self.logger.warning("{:s}.set_mode():  Unknown mode: {:s}".format(self.driver_name, mode))

    def get_trace(self):
        print("Changed3!")
        self.write(":FORM REAL,32")
        self.write(":FORM:BORD SWAP")
        yy = self.query_binary_values("TRAC? TRACE1", datatype="f", is_big_endian=False)

        num_points = int(self.query("SWE:POIN?"))
        sweep_time = float(self.query("SWE:TIME?"))
        xx = np.linspace(0, sweep_time, num=num_points)

        return np.stack((xx, yy))


@Instrument.register_models(["FSQ-26"])
class VsaRohde(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "VsaRohde"

    def set_mode(self, mode="spectrum"):
        if mode == "spectrum":
            self.write("INST SAN")
            # self.write( 'DISP:WIND1:SIZE LARGE')
        elif mode == "wimax":
            self.write("*RST")
            self.write("INST:SEL WIMAX")
            # pause(10)
            self.query("*OPC?")
        elif mode == "wlan":
            self.write("*RST")
            self.write("INST:SEL WLAN")
            self.query("*OPC?")
        elif mode == "vsa":
            self.write(":INST VSA")
        else:
            self.logger.warning("{:s}.set_mode():  Unknown mode: {:s}".format(self.driver_name, mode))

    def get_mode(self):
        mode = self.query("INST:SEL?")

        modes = {"WIM": "wimax", "SAN": "spectrum", "WLAN": "wlan"}
        return modes.get(mode, "Unknown")

    def get_trace(self):
        self.write(":FORM REAL,32")
        # self.write(':FORM:BORD SWAP')     # Command doesn't exist
        yy = self.query_binary_values("TRAC? TRACE1", datatype="f", is_big_endian=False)

        num_points = int(self.query("SWE:POIN?"))
        sweep_time = float(self.query("SWE:TIME?"))
        xx = np.linspace(0, sweep_time, num=num_points)

        return np.stack((xx, yy))
