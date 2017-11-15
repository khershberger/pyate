'''
Created on Jul 4, 2017

@author: kyleh
'''

from .instrument import Instrument

class PowerSupply(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'PowerSupply'
        
    def setOutput(self, state):
        if state is True:   
            result = self.res.write(':OUTP ON')
        else:
            result = self.res.write(':OUTP OFF')
        return result
    
    def setVoltage(self, channel, value):
        self.res.write(':SOUR{:d}:VOLT {:g}'.format(channel, value))
        result = float(self.res.query(':SOUR{:d}:VOLT?'.format(channel)))
        
        self.logger.info('Readback = {:g}'.format(result))
        return result

    def setCurrent(self, channel, value):
        self.res.write(':SOUR{:d}:CURR {:g}'.format(channel, value))
        result = float(self.res.query(':SOUR{:d}:CURR?'.format(channel)))
        
        self.logger.info('Readback = {:g}'.format(result))
        return result
        
    def measVoltage(self, channel):
        result = float(self.res.query(':MEAS:VOLT? CH{:d}'.format(channel)))
        
        self.logger.info('Measured Voltage = {:g}'.format(result))
        return result

    def measCurrent(self, channel):
        result = float(self.res.query(':MEAS:CURR? CH{:d}'.format(channel)))
        
        self.logger.info('Measured Voltage = {:g}'.format(result))
        return result

@Instrument.registerModels(['DP832'])
class PowerSupplyDP832(PowerSupply):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'PowerSupplyDP832'
