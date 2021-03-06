'''
Created on Jul 12, 2017

@author: kyleh
'''


'''
Some notes for later:

This block should directly read the operation complete flag from
the <can't remember exact name of it> status register.
It works, but it takes a long time for the flag to be set.

stat = 0
pm.res.write('*OPC')
pm.res.write('INIT1')
while(not (stat & 1)):
     stat = int(pm.res.query('*ESR?'))
     print('{0:d} {0:b}'.format(stat, stat))

'''

import time

from .instrument import Instrument
from .instrument import InstrumentNothingToRead

@Instrument.registerModels(['E4417A'])
class PowerMeter(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'PowerMeter'
        
        #increase timeout
        ##### WARNING!!!  Apparently pyfisa timeout is in milliseconds
        # Prologix is in seconds
        #self.res.timeout = 500.0          # This is due to periodically long read times
        self.delay = 0.05               # Prevent instrument from getting hung up by talking to it too fast
        
    def setOffset(self, channel, value=None, enable=None):
        if value is not None:
            self.write('SENS{:d}:CORR:GAIN2 {:g}'.format(channel, value))
            
        if enable is not None:
            self.write('SENS{:d}:CORR:GAIN2:STAT {:b}'.format(channel, enable))
            
    def setDutyCycle(self, channel, value=None, enable=None):
        if value is not None:
            self.write('SENS{:d}:CORR:DCYC {:g}'.format(channel, value*100.))
            
        if enable is not None:
            self.write('SENS{:d}:CORR:DCYC:STAT {:b}'.format(channel, enable))

    def getFrequency(self, channel):
        return float(self.query('SENS{:d}:FREQ?'.format(channel)))

    def setFrequency(self, channel, freq):
        self.write('SENS{:d}:FREQ {:g}HZ'.format(channel, freq))
        
    def setSettings(self, channel, 
                    readingsPerSecond=None,
                    continuous=None,
                    trigSource=None,
                    averaging=None,
                    resolution=None,
                    offset=None,
                    dutycycle=None):
        
        # This must be set before averaging as it will reset the averaging settings
        if resolution is not None:
            initStatus = self.query('INIT{:d}:CONT?'.format(channel))
            self.write('CONF{:d} DEF,{:d},(@{:d})'.format(channel, resolution, channel))
            self.write('INIT{:d}:CONT {:s}'.format(channel, initStatus))
        
        if continuous is not None:
            self.write('INIT{:d}:CONT {:d};'.format(channel, int(continuous)))
        if trigSource is not None:
            self.write('TRIG{:d}:SOUR {:s}'.format(channel, trigSource))
        if readingsPerSecond is not None:
            self.write('SENS{:d}:SPE {:d}'.format(channel, readingsPerSecond))
        if averaging is not None:
            if   (averaging == False):
                self.write('SENS{:d}:AVER 0'.format(channel))
            elif (averaging == 'auto') or (averaging == 'AUTO'):
                self.write('SENS{:d}:AVER 1'.format(channel))
                self.write('SENS{:d}:AVER:COUN:AUTO 1'.format(channel))
            else:
                self.write('SENS{:d}:AVER 1'.format(channel))
                self.write('SENS{:d}:AVER:COUN:AUTO 0'.format(channel))
                self.write('SENS{:d}:AVER:COUN {:d}'.format(channel,averaging))

        if offset is not None:
            if isinstance(offset, bool):
                self.write('SENS{:d}:CORR:GAIN2:STAT {:b}'.format(channel, offset))
            else:
                self.write('SENS{:d}:CORR:GAIN2:STAT 1'.format(channel))
                self.write('SENS{:d}:CORR:GAIN2 {:g}'.format(channel, offset))

        if dutycycle is not None:
            if isinstance(dutycycle, bool):
                self.write('SENS{:d}:CORR:DCYC:STAT {:d}'.format(channel, dutycycle))
            else:
                self.write('SENS{:d}:CORR:DCYC:STAT 1'.format(channel))
                self.write('SENS{:d}:CORR:DCYC {:g}'.format(channel, dutycycle*100.))

#    def getSettings(self,channel):
#        result = {}
#        result['readingsPerSecond'] = self.query('SENS{:d}:SPE?'.format(channel))
#        result['continuous']        = self.query('INIT{:d}:CONT?'.format(channel))
#        result['trigSource']        = self.query('TRIG:SOUR?'.format(channel))
#        
#        if (self.query('SENS{:d}.AVER:COUN:AUTO?'.format(channel)) == 'AUTO'):
#            result['averaging']     = 'AUTO'
#        else:
#            result['averaging']     = self.query('SENS{:d}:AVER:COUN?'.format(channel))
#        
#        return result  

    def getSettings(self, channel):
        result = {}
        result['continuous'] = bool(int(self.query('INIT{:d}:CONT?'.format(channel))))
        result['trigSource'] = self.query('TRIG{:d}:SOUR?'.format(channel))
        result['readingsPerSecond'] = int(self.query('SENS{:d}:SPE?'.format(channel)))
        
        avgen   = bool(int(self.query('SENS{:d}:AVER?'.format(channel))))
        avgauto = bool(int(self.query('SENS{:d}:AVER:COUN:AUTO?'.format(channel))))
        avgcnt  = int(self.query('SENS{:d}:AVER:COUN?'.format(channel)))
        if not avgen:
            result['averaging'] = False
        elif avgauto:
            result['averaging'] = 'auto'
        else:
            result['averaging'] = avgcnt
        
        #result['resolution'] = self.query('TRIG{:d}:SOUR'.format(channel))
        
        offseten = bool(int(self.query('SENS{:d}:CORR:GAIN2:STAT?'.format(channel))))
        if not offseten:
            result['offset'] = False
        else:
            result['offset'] = float(self.query('SENS{:d}:CORR:GAIN2?'.format(channel)))
            
        dutyen = bool(int(self.query('SENS{:d}:CORR:DCYC:STAT?'.format(channel))))
        if not dutyen:
            result['dutycycle'] = False
        else:
            result['dutycycle'] = float(self.query('SENS{:d}:CORR:DCYC?'.format(channel)))
        return result

    def measPower(self, channel, resolution=None):
        if resolution is not None:
            self.setResolution(channel, resolution)
        #self.write('INIT{:d}:CONT 1'.format(channel))
        #self.write('INIT{:d}'.format(channel), delay=self.delay)
        result = self.query('FETC{:d}?'.format(channel), delay=self.delay)
        return float(result)
    
    def setDefaults(self, channel):
            self.setSettings(channel, 
                        readingsPerSecond=40,
                        continuous=True,
                        trigSource='IMM',
                        averaging='auto',
                        resolution=3,
                        offset=False,
                        dutycycle=False)
            
            #self.setOffset(channel, enable=False, value=0.)
            #self.setDutyCycle(channel, enable=False, value=0.01)