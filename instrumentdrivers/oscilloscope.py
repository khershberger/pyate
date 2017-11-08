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
        self.res.write(':WAV:SOUR {:s}', channel)
        xorigin    = float(self.res.query(':WAV:XOR?'))
        xreference = float(self.res.query(':WAV:XREF?'))
        xincrement = float(self.res.query(':WAV:XINC?'))
        yorigin    = float(self.res.query(':WAV:YOR?'))
        yreference = float(self.res.query(':WAV:YREF?'))
        yincrement = float(self.res.query(':WAV:YINC?'))
        
        self.res.write(':WAV:MODE NORM')
        self.res.write(':WAV:FORM BYTE')
        
        raw = self.res.query_binary_values(':WAV:DATA? ', datatype='B', is_big_endian=False)
        
        # Scale to voltage:
        # V = (BYTE - YORigin - YREFerence) * YINCrement   From Prog. Manual
        yy = (np.array(raw,dtype='float32') - yorigin - yreference) * yincrement

        # Construct time axis
        xx = (np.arange(0,len(yy)) - xorigin - xreference) * xincrement
  
        return np.stack((xx,yy))
