'''
Created on Jul 4, 2017

@author: kyleh
'''

from .instrument import Instrument
import numpy as np

class Vsg(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Vsg'
        
    def preset(self):
        self.res.write(':SYSTem:PREset')
        self.res.query('*OPC?')
        
    def getFrequency(self):
        return float(self.res.query('SOUR:FREQ?'))

    def getAmplitude(self):
        return self.res.query('SOUR:POW:LEV:IMM:AMPL?')
            
    def setAmplitude(self, level):
        self.res.query('SOUR:POW:LEV:IMM:AMPL {:g}DBM;*OPC?'.format(level))
        
    def setOutputState(self, enable):
        if enable:
            self.res.write('OUTP 1')
        else:
            self.res.write('OUTP 0')
            
@Instrument.registerModels(['E8267D'])
class VsgAgilent(Vsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsgAgilent'

    def setFrequency(self, freq):
        self.res.write('SOUR:FREQ:FIX {:g}GHz'.format(freq/1e9))
        
        
    def sendWaveform(self, iq):
        print('Version 2')
        iq = np.array(iq)   # Ensure numpy array
        
        # Flatten array of complex numbers to  RIRIRIRIRI format
        iqflat = np.stack((iq.real, iq.imag), axis=1).flatten(order='C')
        
        # Normalzie to full-scale
        iqflat = np.round( 32767 * iqflat / np.max(np.abs(iqflat)));

        # Supposedly keeps bit-order while converting to unsigned data format
        iqflat = np.uint16(np.mod(65536 + iqflat, 65536))
        
        name = 'matlab'
            
        self.res.write(':SOUR:RAD:ARB:STAT OFF\n')           # Turn of ARB
        self.res.write_binary_values(':MMEM:DATA "WFM1:{:s}",'.format(name), 
                                     iqflat, datatype='H', is_big_endian=True)
        self.res.query('*OPC?')
        #self.res.write(':SOUR:RAD:ARB:MDES:ALCH M4')         # ALC Hold marker assignment
        #self.res.write(':SOUR:RAD:ARB:MDES:PULS M3');        # RF blanking marker assignment

#@Instrument.registerModels(['DG1032Z'])
class VsgRohde(Vsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsgRohde'

    def setFrequency(self, freq):
        self.res.write('SOUR:FREQ {:g}GHz'.format(freq/1e9))
