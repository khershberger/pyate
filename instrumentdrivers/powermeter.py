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
            self.write('SENS{:d}:CORR:GAIN2 {:g}'.format(channel, value))
            
        if enable is not None:
            self.write('SENS{:d}:CORR:GAIN2:STAT {:b}'.format(channel, enable))

    def getFrequency(self, channel):
        return float(self.query('SENS{:d}:FREQ?'.format(channel)))

    def setFrequency(self, channel, freq):
        self.write('SENS{:d}:FREQ {:g}HZ'.format(channel, freq))
        
    def setSettings(self, channel, 
                    readingsPerSecond=40,
                    continuous=True,
                    trigSource='IMM',
                    averaging='AUTO'):
        
        self.write('INIT{:d}:CONT {:d}'.format(channel, int(continuous)))
        self.write('TRIG{:d}:SOUR {:s}'.format(channel, trigSource))
        self.write('SENS{:d}:SPE {:d}'.format(channel, readingsPerSecond))
        
        if (averaging == 'AUTO'):
            self.write('SENS{:d}:AVER:COUN:AUTO 1'.format(channel))
        elif (averaging == 0):
            self.write('SENS{:d}:AVER 0'.format(channel))
        else:
            self.write('SENS{:d}:AVER:COUN {:d}'.format(channel,averaging))
    
    def getPower(self, channel, resolution=3):
        self.write('CONF{:d}? DEF,{:d},(@{:d})'.format(channel, resolution, channel))
        self.write('INIT{:d}'.format(channel))
        self.write('FETC{:d}?'.format(channel))

        return float(self.read())

    