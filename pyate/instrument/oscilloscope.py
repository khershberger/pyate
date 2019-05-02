'''
Created on Aug 23, 2017

@author: kyleh
'''

from .instrument import Instrument
import numpy as np


@Instrument.registerModels(['DS1054Z', 'DS1104Z'])
class Oscilloscope(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Oscilloscope'
        self.channels = 4
        self.timescalerange = (5e-9, 50)
        self.yscalerange = (1e-3, 10)
        
        self._mapChanShort = {'off':'OFF',
                              'ch1':'CH1',
                              'ch2':'CH2',
                              'ch3':'CH3',
                              'ch4':'CH4',
                              'math':'MATH'}
        self._mapTrigMode  = {'edge':'EDGE'}
        self._mapChannels  = {'ch1':'CHAN1',
                              'ch2':'CHAN2',
                              'ch3':'CHAN3',
                              'ch4':'CHAN4',
                              'math':'MATH'}
        self._mapSlope     = {'pos':'POS',
                              'neg':'NEG'}
        
        self._mapTrigSweep = {'auto':'AUTO',
                              'norm':'NORM',
                              'single':'SING'}
        
    def intToChanNum(self, x):
        return 'ch{:d}'.format(x)        
        
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
    
    def setXScale(self, scale):
        # Check for valid value
        self.checkParameter('scale', scale, float, self.timescalerange)
        
        # Further check to make sure scale has correct mantissa (1, 2, or 5)
        # Nevermind, I'm too lazy
        self.write(':TIM:SCAL {:g}'.format(scale))

    def getXScale(self):
        return float(self.query(':TIM:SCAL?'))
    
    def setXOffset(self, offset):
        self.checkParameter('offset', offset, float, None)
        
        self.write(':TIMebase:OFFSet {:g}'.format(offset))

    def getXOffset(self):
        return float(self.query(':TIMebase:OffSet?'))
        
    def setYScale(self, channel, scale):
        self.checkParameter('channel', channel, int, (1,self.channels))    
        self.checkParameter('scale', scale, float, None)

        # Used to check for valid scale ranging
        # Decided to leave this out for now
        #probeRatio = self.getProbeRatio(channel)
        #yscalelimits = (self.yscalerange[0]*probeRatio, 
        #                self,yscalerange[1]*proberatio)
        
        
        # Further check to make sure scale has correct mantissa (1, 2, or 5)
        # Nevermind, I'm too lazy
        self.write(':CHAN{:d}:SCAL {:g}'.format(channel,scale))

    def getYScale(self, channel):
        self.checkParameter('channel', channel, int, (1,self.channels))    
        return float(self.query(':CHAN{:g}:SCAL?').format(channel))
    
    def setYOffset(self, channel, offset):
        self.checkParameter('channel', channel, int, (1,self.channels)) 
        self.checkParameter('offset', offset, float, None)
        self.write(':CHAN{:d}:OFFSet {:g}'.format(channel,offset))   
    
    def getYOffset(self,channel):
        self.checkParameter('channel', channel, int, (1,self.channels)) 
        return float(self.query(':CHAN{:d}:OffSet?'.format(channel)))    
    
    def getProbeRatio(self, channel):
        self.checkParameter('channel', channel, int, (1,self.channels))
        return float(self.query(':CHAN{:d}?'.format(channel)))
    
    def setCursor(self, sourcea=None, sourceb=None, ax=None, bx=None):
        self.write(':CURSor:MODE TRACk')
        if sourcea is not None:
            self.checkParameter('sourcea', sourcea, int, (1,self.channels))
            channelName = self.intToChanNum(sourcea)
            self.write(':CURSor:TRACk:SOURce1 {:s}'.format(self._mapChannels[channelName]))
        if sourceb is not None:
            self.checkParameter('sourceb', sourceb, int, (1,self.channels))
            channelName = self.intToChanNum(sourcea)
            self.write(':CURSor:TRACk:SOURce2 {:s}'.format(self._mapChannels[channelName]))

        if (ax is not None) or (bx is not None):
            # Figure out time scale
            offset = self.getXOffset()
            scale  = self.getXScale()
            xstep = scale*12/600
            self.logger.debug('offset=%g  scale=%g  xstep=%g', offset, scale, xstep)
            
            #minx = -297*xstep + offset
            #maxx = +294*xstep + offset
            
            
        if ax is not None:
            self.checkParameter('ax', ax, float, None)
            xpixel = round((ax-offset)/xstep + 300)
            self.logger.debug('Set AX to %d', xpixel)
            self.write(':CURSor:TRACk:AX {:d}'.format(xpixel))
        if bx is not None:
            self.checkParameter('bx', bx, float, None)
            xpixel = round((bx-offset)/xstep + 300)
            self.logger.debug('Set BX to %d', xpixel)
            self.write(':CURSor:TRACk:BX {:d}'.format(xpixel))

    def getCursorValues(self):
        d = {}
        d['ax'] = float(self.query(':CURSor:TRACk:AXValue?'))
        d['bx'] = float(self.query(':CURSor:TRACk:BXValue?'))
        d['ay'] = float(self.query(':CURSor:TRACk:AYValue?'))
        d['by'] = float(self.query(':CURSor:TRACk:BYValue?'))
        return d

    def setTrigger(self, mode=None, source=None, slope=None, level=None, sweep=None):

        if mode is not None:
            self.checkParameter('mode', mode, str, self._mapTrigMode)
            modeParsed = self._mapTrigMode[mode]
            self.write(':TRIG:MODE {:s}'.format(modeParsed))
        else:
            modeParsed = self.getTrigger()['mode']
            
        if sweep is not None:
            self.checkParameter('sweep', sweep, str, self._mapTrigSweep)
            self.write(':TRIG:SWEep {:s}'.format(self._mapTrigSweep[sweep]))
            
        if modeParsed == 'EDGE':
            if level is not None:
                self.checkParameter('level', level, float, None)
                self.write(':TRIG:EDGe:LEVel {:g}'.format(level))
            if source is not None:
                if isinstance(source, int):
                    self.checkParameter('source', source, int, (1, self.channels))
                    source = self.intToChanNum(source)
                else:
                    self.checkParameter('source', source, str, self._mapChannels)
                self.write(':TRIG:EDGe:SOUR {:s}'.format(self._mapChannels[source]))
            if slope is not None:
                self.checkParameter('slope', slope, str, self._mapSlope)
                self.write(':TRIG:EDGe:SLOP {:s}'.format(self._mapSlope[slope]))
            
    def getTrigger(self):
        d = {}
        d['mode'] = self.query(':TRIG:MODE?')
        d['status'] = self.query(':TRIG:STAT?')
        
        if d['mode'] == 'EDGE':
            d['level'] = float(self.query(':TRIG:EDGe:LEVel?'))
            d['source'] = self.query(':TRIG:EDGe:SOUR?')
            d['slope'] = self.query(':TRIG:EDGe:SLOP?')
        
        return d
    
    def getMeasurement(self, channel, meas):
        self.checkParameter('channel', channel, int, (1,self.channels))
        channelName = self.intToChanNum(channel)
        
        _mapMeas = {'dutycycle':'PDUTy',
                    'pulsewidth':'PWIDth',
                    'period':'PERiod',
                    'vlower':'VLOWer',
                    'vupper':'VUPper'}
        
        #if meas is not None:
        self.checkParameter('meas', meas, str, _mapMeas)
        return float(self.query(':MEAS:ITEM? {:s},{:s}'.format(_mapMeas[meas], self._mapChannels[channelName])))