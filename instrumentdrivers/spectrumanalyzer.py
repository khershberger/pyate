'''
Created on Jul 4, 2017

@author: kyleh
'''

from .instrument import Instrument
import numpy as np

class Vsa(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Vsa'

    def checkIfNumeric(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
### System Commands
    def preset(self):
        self.res.write('*RST')
        self.res.query('*OPC?')
        
    def align(self, automatic=False):
        if (automatic):
            self.res.write(':CAL:AUTO ON')
        else:
            self.res.write(':CAL:AUTO OFF')
            self.res.write(':CAL:ALL')
            self.res.query('*OPC?') 
          
            #try:
            #    # Check how many minutes passed since last
            #    # alignment
            #    elapsed_time=toc(LAST_ALIGMENT_TIME)/60
            #catch:
            #    # Alignment has never done since program
            #    # started
            #    elapsed_time=1000
            #
            #if elapsed_time>ALIGNMENT_INTERVAL
            #    self.logger.info('{:g} minutes since last VSA alignment - Alignment is needed'.format(elapsed_time))
            #    PriorTimeOut = v_vsa.TimeOut
            #    v_vsa.Timeout=200
            #    self.res.write':CAL:AUTO OFF')
            #    self.res.write(':CAL:ALL')
            #    result = self.res.query(v_vsa,'*OPC?') 
            #    v_vsa.Timeout=PriorTimeOut
            #    LAST_ALIGMENT_TIME=tic
            #else
            #    printlog(3, sprintf('%g minutes since last VSA alignment - Skipping alignment',elapsed_time))
            
    def init(self):
        self.res.write('INIT:IMM')
    def opc(self):
        return self.res.query('*OPC?')
    def options(self):
        return self.res.query(':SYST:OPTions?')
    
    def setBlockFormat(self, datatype):
        if   datatype == 'ascii':
            self.res.write(':FORM ASC')
        elif datatype == 'single':
            self.res.write(':FORM REAL32')
        elif datatype == 'double':
            self.res.write(':FORM REAL')
        else:
            self.logger.warning('{:s}.setBlockFormat(): Unknown mode {:s}'.format(self.drivername, datatype))

### Spectrum Analyzer Commands

    def setBandwidth(self, video=None, resolution=None):
        if video is not None:
            if video == 'auto':
                self.res.write('BAND:VID:AUTO ON')
            else:
                self.res.write('BAND:VID {:g} HZ'.format(video))

        if resolution is not None:
            if resolution == 'auto':
                self.res.write('BAND:RES:AUTO ON')
            else:
                self.res.write('BAND:RES {:g} HZ'.format(resolution))
                
    def getResolutionBandwidth(self):
        return self.res.query('BAND:RES?')

    def getVideoBandwidth(self):
        return self.res.query('BAND:VID?')
                
    def setFreq(self, start=None, stop=None, center=None, span=None):
        if ( (start is not None or stop is not None) and (center is not None or span is not None)):
            self.logger.warning('{:s}.setFreq(): Conflicting parameters specified.  Defaulting to center/span'.format(self.drivername))

        if start is not None:
            self.res.write('FREQ:STARt {:g} GHZ', start/1e9)

        if stop is not None:
            self.res.write('FREQ:STOP {:g} GHZ', stop/1e9)
        
        if center is not None:
            self.res.write('FREQ:CENTer {:g} GHZ', center/1e9)

        if span is not None:
            self.res.write('FREQ:SPAN {:g} HZ', span)

    def setAttenuation(self, attenuation):
        if attenuation == 'AUTO':
            self.res.write(':SENse:POWer:RF:ATTenuation:AUTO ON')
        else:
            self.res.write(':SENse:POWer:RF:ATTenuation {:g}'.format(float(attenuation)))

    def getRefLevel(self):
        return self.res.query(':DISP:WIND1:TRAC:Y:RLEV?')
            
    def setRefLevel(self, level):
        self.res.write(':DISP:WIND1:TRAC:Y:RLEV {:g} dBm'.format(level))
        
    def setYAxis(self, scale=100, refPosition=1.0):
        refPositionPct = round(100*refPosition)
        self.res.write(':DISP:TRAC:Y {:g}'.format(scale))
        self.res.write(':DISP:TRAC:Y:RPOS {:d}PCT'.format(refPositionPct))
        
    def sweep_time(self, sweeptime):
        self.res.write('SENS:SWE:TIME {:g}'.format(float(sweeptime)))

class VsaAgilent(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsaAgilent'
        
            
    def getMode(self):
        mode = self.res.query('INST:SEL?')
        
        modes = {
                'WIMAXOFDMA': 'wimax',
                'SA': 'spectrum',
                'VSA': 'vsa',
                'VSA89601':'vsa89601',
                'WLAN': 'wlan'
                }
        return modes.get(mode, 'Unknown')
    
    def initBasebandIQ(self):
        pass
#         self.res.write( ':INST BASIC')                 % Switch to IQ analyzer mode
#         self.res.write( ':CONF:WAV')                   % Waveform analysis measurement
#         self.res.write( ':ROSC:EXT:FREQ 10 MHz')       % Set External reference to 10 MHz
#         self.res.write( ':ROSC:SOUR EXT')              % Select external reference
#         self.res.write( ':TRIG:WAV:SOUR EXT1')         % External Trigger
#         self.res.write( ':INIT:CONT OFF')              % Single trigger
#         self.res.write( ':WAV:AVER:STAT OFF')          % TURN AVERAGING OFF

    def iqSweepTime(self):
        pass
#         self.res.write( sprintf(':WAV:SWE:TIME %g', varargin{k+1}))

    def iqBandwidth(self):
        """
        Information BW
        """
        #self.res.write( sprintf(':WAV:BAND %g', varargin{k+1}))
    def iqSamplerate(self):
        """
        IQ Sample Rate
        """
        #self.res.write( sprintf(':WAV:SRAT %g', varargin{k+1}))
    def iqFetchData(self):
        """
        This assumes that a measurement has already been triggered 
        and aquired.  All that needs to be done is load the result
        into the output buffer and read it
        """
        
        """
        self.res.write( ':FORM:BORD SWAP')         % Set to little-endian byte order (PC)
        
        % Don't know if this works....
        self.res.write( ':FORM REAL,32')           % Set to 64 bit real numbers (32 should work as well)
        self.res.write( ':FETCh:WAV1?')
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
        
        self.res.write( ':FETCh:WAV0?')
        sadata = binblockread(v_vsa, 'single')

        sadata = transpose(reshape(sadata, 2, length(sadata)/2))
        result.iq = complex(sadata(:,1), sadata(:,2))
        """
        pass

    def setMode(self, mode='spectrum'):
        if   mode == 'spectrum':
            self.res.write(':INST SA')
            self.res.write( 'CONFigure:SANalyzer')
        elif mode == 'wimax':
            self.res.write(':INST WIMAXOFDMA')
            self.res.query('*OPC?')
        elif mode == 'wlan':
            self.res.write(':INST WLAN')
            self.res.write(':RAD:STAN AG') 
            self.res.query('*OPC?')
        elif mode == 'vsa':
            self.res.write(':INST VSA')
        else:
            self.logger.warning('{:s}.setMode():  Unknown mode: {:s}'.format(self.drivername, mode))

    def getTrace(self):
        print('Changed3!')
        self.res.write(':FORM REAL,32')
        self.res.write(':FORM:BORD SWAP')
        yy = self.res.query_binary_values('TRAC? TRACE1', datatype='f', is_big_endian=False)
        
        numPoints = int(self.res.query('SWE:POIN?'))
        sweepTime = float(self.res.query('SWE:TIME?'))
        xx = np.linspace(0, sweepTime, num=numPoints)
        
        return np.stack((xx,yy))


class VsaRohde(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsaRohde'
        
    def setMode(self, mode='spectrum'):
        if   mode == 'spectrum':
            self.res.write( 'INST SAN')
            #self.res.write( 'DISP:WIND1:SIZE LARGE')
        elif mode == 'wimax':
            self.res.write( '*RST')
            self.res.write( 'INST:SEL WIMAX')
            #pause(10)
            self.res.query('*OPC?')
        elif mode == 'wlan':
            self.res.write( '*RST')
            self.res.write( 'INST:SEL WLAN')
            self.res.query('*OPC?')
        elif mode == 'vsa':
            self.res.write(':INST VSA')
        else:
            self.logger.warning('{:s}.setMode():  Unknown mode: {:s}'.format(self.drivername, mode))

                
    def getMode(self):
        mode = self.res.query('INST:SEL?')
        
        modes = {
            'WIM': 'wimax',
            'SAN': 'spectrum',
            'WLAN': 'wlan'
            }
        return modes.get(mode, 'Unknown')

    def getTrace(self):
        self.res.write(':FORM REAL,32')
        # self.res.write(':FORM:BORD SWAP')     # Command doesn't exist
        yy = self.res.query_binary_values('TRAC? TRACE1', 
                                              datatype='f', is_big_endian=False)
        
        numPoints = int(self.res.query('SWE:POIN?'))
        sweepTime = float(self.res.query('SWE:TIME?'))
        xx = np.linspace(0, sweepTime, num=numPoints)
        
        return np.stack((xx,yy))