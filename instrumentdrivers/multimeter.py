'''
Created on 2017-11-13

@author: kyleh
'''

from .instrument import Instrument

class Multimeter(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Multimeter'
        
    def measCurrentDC(self):
        #self.res.write('INST:SEL OUT1')
        result = self.res.query('MEAS:CURR:DC?')
        try:
            value = float(result)
        except ValueError as e:
            value = float('nan')
        return value
        
    def measVoltageDC(self):
        #self.res.write('CONF:VOLT:DC AUTO')
        #self.res.write('INIT')
        #result = self.res.query('FETC?')
        result = self.res.query('MEAS:VOLT:DC?')
        try:
            value = float(result)
        except ValueError as e:
            value = float('nan')
        return value
    
@Instrument.registerModels(['8845A'])
class MultimeterFluke(Multimeter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'MultimeterFluke'
