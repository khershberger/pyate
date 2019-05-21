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
        return float(self.query('SOUR:POW:LEV:IMM:AMPL?'))
            
    def setAmplitude(self, level):
        self.query('*OPC;SOUR:POW:LEV:IMM:AMPL {:g}DBM;*OPC?'.format(level))

    def getOutputState(self):
        return bool(int(self.query('OUTP?')))
        
    def setOutputState(self, enable):
        if enable:
            self.write('OUTP 1')
        else:
            self.write('OUTP 0')
            
    def getModulationState(self):
        raise NotImplementedError
        
    def setModulationState(self, enable):
        raise NotImplementedError
            
@Instrument.registerModels(['E8267D', 'N5182B'])
class VsgAgilent(Vsg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsgAgilent'

    def setFrequency(self, freq):
        self.write('SOUR:FREQ:FIX {:g}GHz'.format(freq/1e9))
        
        
    def sendWaveform(self, iq, markers=None):
        # Typical marker assignment
        # 1:  Rear-panel trigger out
        # 2:  ?
        # 3:  RF Blanking
        # 4:  ALC Hold
        
        print('Version 2')
        iq = np.array(iq)   # Ensure numpy array
        if markers is not None:
            if len(markers) != len(iq):
                raise ValueError('markers must be same length as IQ data')
            markers = np.uint8(markers)
            
        
        # Flatten array of complex numbers to  RIRIRIRIRI format
        iqflat = np.stack((iq.real, iq.imag), axis=1).flatten(order='C')
        
        # Normalzie to full-scale
        iqflat = np.round( 32767 * iqflat / np.max(np.abs(iqflat)));

        # Supposedly keeps bit-order while converting to unsigned data format
        iqflat = np.uint16(np.mod(65536 + iqflat, 65536))
        
        name = 'PYTHONi'
            
        self.write(':SOUR:RAD:ARB:STAT OFF\n')           # Turn of ARB
        self.write_binary_values(':MMEM:DATA "WFM1:{:s}",'.format(name), 
                                     iqflat, datatype='H', is_big_endian=True)
        self.query('*OPC?')
        if markers is not None:
            self.write_binary_values(':MMEM:DATA "MKR1:{:s}",'.format(name), 
                                         markers, datatype='B', is_big_endian=True)
            self.write(':SOUR:RAD:ARB:MDES:ALCH M4')         # ALC Hold marker assignment
            self.write(':SOUR:RAD:ARB:MDES:PULS M3');        # RF blanking marker assignment

    def setModulationState(self, enable):
        if enable:
            self.write(':OUTPut:MODulation:STATe 1')
        else:
            self.write(':OUTPut:MODulation:STATe 0')

    def setAttenuator(self, level=None, auto=None):
        if level is not None:
            raise NotImplementedError()
        if auto is not None:
            self.checkParameter('auto', auto, bool, None)
            self.write(':SOUR:POW:ATT:AUTO {:d}'.format(auto))

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
