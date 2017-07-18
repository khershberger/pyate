'''
Created on Jul 12, 2017

@author: kyleh
'''

import instrumentdrivers.core as idcore
import math
import numpy as np
import time

class PulseGenerator(idcore.Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'PulseGenerator'
        
    def sendWaveform(self, data, samplerate, amplitude, offset=0, channel=1):
        """
        Input waveform is assumed to be signed.
        Output range is symmetric about zero.
          Fullscale negative = -8192
          Fullscale positive = +8192
        """
        
        # First offset waveform to move zero to +8192
        data = data + 2**13
        
        self.res.write(':SOUR{:d}:APPL:ARB {:g}, {:g}, {:g}'.format(channel, samplerate, amplitude, offset))
        self.res.query('*OPC?')
        # There does not seem to be the capability of setting binary
        # data format or byte order.
        # Looks like the default is:
        # Little endian
        # Short INT
        # Since it is only 14 bits, sign doesn't matter?
        self.res.write_binary_values(':SOUR{:d}:DATA:DAC VOLATILE,'.format(channel), data, 
                                     datatype='h', is_big_endian=False)
        self.res.query('*OPC?')
        time.sleep(0.1)

    def getOutputState(self, channel):
        return True if self.res.query(':OUTP{:d}?'.format(channel)) == 'ON' else False
        
    def setOutputState(self, channel, state):
        self.res.write(':OUTP{:d} {:s}'.format(channel, 'ON' if state else 'OFF'))
        self.res.query('*OPC?')
        time.sleep(0.1)
        
    def setupBurst(self, channel):
        self.res.write(':SOUR{:d}:BURS:MODE TRIG'.format(channel))
        self.res.write(':SOUR{:d}:BURS:NCYC 1'.format(channel))
        self.res.write(':SOUR{:d}:BURS:TRIG:SOUR EXT'.format(channel))
        self.res.write(':SOUR{:d}:BURS:TRIG:SLOP POS'.format(channel))
        self.res.write(':SOUR{:d}:BURS:STAT ON'.format(channel))
        self.res.query('*OPC?')
        time.sleep(0.1)
        
    def setupPulse(self, channel, mode, period, width, vlow, vhigh):
        #stateStart = self.getOutputState(channel)
        #self.setOutputState(channel, False)
        self.res.write(':SOUR{:d}:APPL:PULS'.format(channel))
        #self.res.write(':SOUR{:d}:PULS:HOLD WIDT'.format(channel))
        self.res.write(':SOUR{:d}:FUNC:PULS:PER {:g}'.format(channel, period))
        self.res.write(':SOUR{:d}:FUNC:PULS:WIDT {:g}'.format(channel, width))
        self.res.write(':SOUR{:d}:VOLT:LEV:HIGH {:g}'.format(channel, vhigh))
        self.res.write(':SOUR{:d}:VOLT:LEV:LOW {:g}'.format(channel, vlow))
        self.res.query('*OPC?')
        # The following is required for the above settigns to take effect
        # The front panel of the instrument will show the new seetings,
        # but the actual waveform output will remain unchanged
        time.sleep(0.1)  
        #self.setOutputState(channel, stateStart)
        
        
#    def getMode(self):
