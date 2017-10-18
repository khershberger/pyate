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
    
    def setVoltage(self, value):
        result = self.res.query(':VOLT {:g};:VOLT?'.format(value))
        self.logger.info('Readback = {:g}'.format(result))
        return result

    def setCurrent(self, value):
        result = self.res.query(':CURR {:g};:CURR?'.format(value))
        self.logger.info('Readback = {:g}'.format(result))
        return result
        
    def measVoltage(self):
        result = self.res.query(':MEAS:CURR?')
        self.logger.info('Measured Voltage = {:g}'.format(result))
        return result

class PowerSupplyDP832(PowerSupply):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'PowerSupplyDP832'
