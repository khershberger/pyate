'''
Created on Aug 23, 2017

@author: kyleh
'''

from .instrument import Instrument
import numpy as np


@Instrument.registerModels(['DS1054Z'])
class Oscilloscope(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Oscilloscope'
        
    def getTrace(self, channel):
        self.write(':WAV:SOUR {:s}', channel)
        xorigin    = float(self.query(':WAV:XOR?'))
        xreference = float(self.query(':WAV:XREF?'))
        xincrement = float(self.query(':WAV:XINC?'))
        yorigin    = float(self.query(':WAV:YOR?'))
        yreference = float(self.query(':WAV:YREF?'))
        yincrement = float(self.query(':WAV:YINC?'))
        
        self.write(':WAV:MODE NORM')
        self.write(':WAV:FORM BYTE')
        
        raw = self.query_binary_values(':WAV:DATA? ', datatype='B', is_big_endian=False)
        
        # Scale to voltage:
        # V = (BYTE - YORigin - YREFerence) * YINCrement   From Prog. Manual
        yy = (np.array(raw,dtype='float32') - yorigin - yreference) * yincrement

        # Construct time axis
        xx = (np.arange(0,len(yy)) - xorigin - xreference) * xincrement
  
        return np.stack((xx,yy))
