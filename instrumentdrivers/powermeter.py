'''
Created on Jul 12, 2017

@author: kyleh
'''

from .instrument import Instrument

@Instrument.registerModels(['E4417A'])
class PowerMeter(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'PowerMeter'
        
    def setOffset(self, channel, enable=None, value=None):
        if value is not None:
            self.res.write('SENS{:d}:CORR:GAIN2 {:g}DB'.format(channel, value))
            
        if enable is not None:
            self.res.write('SENS{:d}:CORR:GAIN2:STAT {:b}'.format(channel. enable))

    def getFrequency(self, channel):
        return float(self.res.query('SENS{:d}:FREQ?'.format(channel)))

    def setFrequency(self, channel, freq):
        self.res.write('SENS{:d}:FREQ {:g}HZ'.format(channel.freq))
        
    def getPower(self, channel, resolution=3):
        self.res.write('MEAS{:d}? DEF,{:d},(@{:d})'.format(channel, resolution, channel))
        return float(self.res.read())
    