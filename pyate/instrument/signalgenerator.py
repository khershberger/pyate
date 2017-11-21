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
        self.write(':SYSTem:PREset')
        self.query('*OPC?')
        
    def getFrequency(self):
        return float(self.query('SOUR:FREQ?'))

    def getAmplitude(self):
        return self.query('SOUR:POW:LEV:IMM:AMPL?')
            
    def setAmplitude(self, level):
        self.query('*OPC;SOUR:POW:LEV:IMM:AMPL {:g}DBM;*OPC?'.format(level))
        
    def setOutputState(self, enable):
        if enable:
            self.write('OUTP 1')
        else:
            self.write('OUTP 0')
            
@Instrument.registerModels(['E8267D', 'N5182B'])
class VsgAgilent(Vsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsgAgilent'

    def setFrequency(self, freq):
        self.write('SOUR:FREQ:FIX {:g}GHz'.format(freq/1e9))
        
        
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
            
        self.write(':SOUR:RAD:ARB:STAT OFF\n')           # Turn of ARB
        self.write_binary_values(':MMEM:DATA "WFM1:{:s}",'.format(name), 
                                     iqflat, datatype='H', is_big_endian=True)
        self.query('*OPC?')
        #self.write(':SOUR:RAD:ARB:MDES:ALCH M4')         # ALC Hold marker assignment
        #self.write(':SOUR:RAD:ARB:MDES:PULS M3');        # RF blanking marker assignment

    def setModulationState(self, enable):
        if enable:
            self.write(':OUTPut:MODulation:STATe 1')
        else:
            self.write(':OUTPut:MODulation:STATe 0')

#@Instrument.registerModels(['DG1032Z'])
class VsgRohde(Vsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsgRohde'

    def setFrequency(self, freq):
        self.write('SOUR:FREQ {:g}GHz'.format(freq/1e9))
        
    def setModulationState(self, enable):
        if enable:
            self.write('SOUR:MOD:STAT 1')
        else:
            self.write('SOUR:MOD:STAT 0')        
