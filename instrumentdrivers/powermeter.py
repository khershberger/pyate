'''
Created on Jul 12, 2017

@author: kyleh
'''

from .instrument import Instrument

#pm.res.query('SENS1:SPE?')
#pm.res.query('INIT1:CONT?')
#pm.res.query('TRIG:SOUR?')
#
#pm.res.write('CONF1? DEF,{3},(@{1})')
#pm.res.write('SENS1:SPE 40')
#pm.res.write('SENS1:AVER:COUN:AUTO 0')
#pm.res.write('SENS1:AVER:COUN 8')
#pm.res.write('INIT1')
#
#stat = 0
#pm.res.write('*OPC')
#pm.res.write('INIT1')
#while(not (stat & 1)):
##for k in range(0,5):
#     stat = int(pm.res.query('*ESR?'))
#     print('{0:d} {0:b}'.format(stat, stat))
#
#pm.res.query('FETC1?')
#
#pm.res.query('INIT1;FETC1?')

@Instrument.registerModels(['E4417A'])
class PowerMeter(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'PowerMeter'
        
    def setOffset(self, channel, enable=None, value=None):
        if value is not None:
            self.res.write('SENS{:d}:CORR:GAIN2 {:g}'.format(channel, value))
            
        if enable is not None:
            self.res.write('SENS{:d}:CORR:GAIN2:STAT {:b}'.format(channel, enable))

    def getFrequency(self, channel):
        return float(self.res.query('SENS{:d}:FREQ?'.format(channel)))

    def setFrequency(self, channel, freq):
        self.res.write('SENS{:d}:FREQ {:g}HZ'.format(channel, freq))
        
    def setSettings(self, channel, 
                    readingsPerSecond=40,
                    continuous=True,
                    trigSource='IMM',
                    averaging='AUTO'):
        
        self.res.write('INIT{:d}:CONT {:d}'.format(channel, int(continuous)))
        self.res.write('TRIG{:d}:SOUR {:s}'.format(channel, trigSource))
        self.res.write('SENS{:d}:SPE {:d}'.format(channel, readingsPerSecond))
        
        if (averaging == 'AUTO'):
            self.res.write('SENS{:d}:AVER:COUN:AUTO 1'.format(channel))
        elif (averaging == 0):
            self.res.write('SENS{:d}:AVER 0'.format(channel))
        else:
            self.res.write('SENS{:d}:AVER:COUN {:d}'.format(channel,averaging))
    
    def getPower(self, channel, resolution=3):
        self.res.write('CONF{:d}? DEF,{:d},(@{:d})'.format(channel, resolution, channel))
        self.res.write('INIT{:d}'.format(channel))
        self.res.write('FETC{:d}?'.format(channel))

        return float(self.res.read())
    