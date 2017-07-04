'''
Created on Jul 4, 2017

@author: kyleh
'''

import instrumentdrivers.core as idcore

class Vsg(idcore.Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Vsg'
        
    def preset(self):
        self.res.write(':SYSTem:PREset')
        self.res.query('*OPC?')
        
    def getFrequency(self):
        return float(self.res.query('SOUR:FREQ?'))
            
    def setLevel(self, level):
        self.res.query('SOUR:POW:LEV:IMM:AMPL {:g}DBM;*OPC?'.format(level))
        
    def setOutputEnable(self, enable):
        if enable:
            self.res.write('OUTP 1')
        else:
            self.res.write('OUTP 0')

class VsgAgilent(Vsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsgAgilent'

    def setFrequency(self, freq):
        self.res.write('SOUR:FREQ:FIX {:g}GHz'.format(freq/1e9))

class VsgRohde(Vsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsgRohde'

    def setFrequency(self, freq):
        self.res.write('SOUR:FREQ {:g}GHz'.format(freq/1e9))
