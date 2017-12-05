'''
Created on Jul 12, 2017

@author: kyleh
'''

from .instrument import Instrument
import time

class WaveformGenerator(Instrument):
    _scpi_prefix = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'WaveformGenerator'

    def getOutputState(self, channel):
        return True if self.query(':OUTP{:d}?'.format(channel)) == 'ON' else False
        
    def setOutputState(self, channel, state):
        self.write(':OUTP{:d} {:s}'.format(channel, 'ON' if state else 'OFF'))
        self.query('*OPC?')
        time.sleep(0.1)
        
@Instrument.registerModels(['DG1032Z'])
class WaveformGeneratorRigol(WaveformGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'WaveformGeneratorRigol'

        self._scpi_prefix = ':APPL{:d}'
        
    def sendWaveform(self, data, samplerate, amplitude, offset=0, channel=1):
        """
        Input waveform is assumed to be signed.
        Output range is symmetric about zero.
          Fullscale negative = -8192
          Fullscale positive = +8191
        """
        
        # Attempt to clear VOLATILE meomory
        #self.write('DATA{:d}:POIN VOLATILE,9'.format(channel))
        

        
        # Offset waveform
        # Rigol instrument expects value to be between 0 and 16383
        # Zero output is 8192
        data = data + 2**13
                
        self.write(':SOUR{:d}:APPL:ARB {:g}, {:g}, {:g}'.format(channel, samplerate, amplitude, offset))
        self.query('*OPC?')
        # There does not seem to be the capability of setting binary
        # data format or byte order.
        # Looks like the default is:
        # Little endian
        # Short INT
        # Since it is only 14 bits, sign doesn't matter?
        self.write_binary_values(':SOUR{:d}:DATA:DAC VOLATILE,'.format(channel), data, 
                                     datatype='h', is_big_endian=False)
        self.query('*OPC?')
        time.sleep(0.1)
        
    def setupBurst(self, channel):
        self.write(':SOUR{:d}:BURS:MODE TRIG'.format(channel))
        self.write(':SOUR{:d}:BURS:NCYC 1'.format(channel))
        
        #self.write(':SOUR{:d}:BURS:MODE GAT'.format(channel))
        
        self.write(':SOUR{:d}:BURS:IDLE BOTTOM'.format(channel))
        
        self.write(':SOUR{:d}:BURS:TRIG:SOUR EXT'.format(channel))
        self.write(':SOUR{:d}:BURS:TRIG:SLOP POS'.format(channel))
        self.write(':SOUR{:d}:BURS:STAT ON'.format(channel))
        self.query('*OPC?')
        time.sleep(0.1)
        
    def setupPulse(self, channel, mode, period, width, vlow, vhigh):
        #stateStart = self.getOutputState(channel)
        #self.setOutputState(channel, False)
        self.write(':SOUR{:d}:APPL:PULS'.format(channel))
        #self.write(':SOUR{:d}:PULS:HOLD WIDT'.format(channel))
        self.write(':SOUR{:d}:FUNC:PULS:PER {:g}'.format(channel, period))
        self.write(':SOUR{:d}:FUNC:PULS:WIDT {:g}'.format(channel, width))
        self.write(':SOUR{:d}:VOLT:LEV:HIGH {:g}'.format(channel, vhigh))
        self.write(':SOUR{:d}:VOLT:LEV:LOW {:g}'.format(channel, vlow))
        self.query('*OPC?')
        # The following is required for the above settigns to take effect
        # The front panel of the instrument will show the new seetings,
        # but the actual waveform output will remain unchanged
        time.sleep(0.1)  
        #self.setOutputState(channel, stateStart)

        
@Instrument.registerModels(['81150A'])
class WaveformGenerator81150(WaveformGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'WaveformGenerator81150'
        
        self._scpi_prefix = ':APPL{:d}'

    def sendWaveform(self, data, samplerate, amplitude, offset=0, channel=1):
        """
        Input waveform is assumed to be signed.
        Output range is symmetric about zero.
          Fullscale negative = -8192
          Fullscale positive = +8191
        """
        
        # Calculate repeat frequency since this is what the ARB
        # wants instaed of sample rate
        freq = samplerate/len(data)
        
        # Assume default of BigEndian is still set
        # Should explicitly set this though.
        self.write_binary_values('DATA{:d}:DAC VOLATILE,'.format(channel), data, 
                                     datatype='h', is_big_endian=True)
        self.query('*OPC?')
        self.write('FUNC{:d}:USER VOLATILE'.format(channel))
        self.write('APPL{:d}:USER {:g}, {:g}, {:g}'.format(channel, freq, amplitude, offset))
        self.query('*OPC?')
        time.sleep(0.1)
        
    def setupBurst(self, channel):
        self.write(':ARM:IMP MAX')  # Set EXT-IN imput impedance to 10kOhm
        self.write(':ARM:SOUR{:d} EXT'.format(channel))
        self.write(':ARM:SLOP{:d} POS'.format(channel))
        self.query('*OPC?')
        time.sleep(0.1)
        
    def setupPulse(self, channel, mode, period, width, vlow, vhigh):
        #stateStart = self.getOutputState(channel)
        #self.setOutputState(channel, False)
        self.write(':APPL{:d}:PULS'.format(channel))
        #self.write(':SOUR{:d}:PULS:HOLD WIDT'.format(channel))
        self.write(':PER{:d} {:g}'.format(channel, period))
        self.write(':FUNC{:d}:PULS:WIDT {:g}'.format(channel, width))
        self.write(':VOLT{:d}:HIGH {:g}'.format(channel, vhigh))
        self.write(':VOLT{:d}:LOW {:g}'.format(channel, vlow))
        self.query('*OPC?')
        # The following is required for the above settigns to take effect
        # The front panel of the instrument will show the new seetings,
        # but the actual waveform output will remain unchanged
        time.sleep(0.1)  
        #self.setOutputState(channel, stateStart)
