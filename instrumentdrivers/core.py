# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 14:09:15 2017

@author: kyleh
"""

import logging
import visawrapper
import math
import numpy as np

def InstrumentDriverException(Exception):
    pass

def parseIdnString(idn):
    parsed = idn.split(sep=',')
    return {'vendor':   parsed[0].strip(),
            'model' :   parsed[1].strip(),
            'serial':   parsed[2].strip(),
            'frimware': parsed[3].strip() } 
    
def createInstrument(addr, type='generic'):
    logger = logging.getLogger(__name__)
    
    # First get instrument resource
    #res = pyvisa.ResourceManager().open_resource(addr)
    res = visawrapper.ResourceManager.open_resource(addr)
    identity = parseIdnString(res.query('*IDN?'))
    res.close()

    model = identity['model']

    logger.debug('Model = ' + model)    
    availableDrivers = {
            'DP832':  PowerSupplyDP832,
            'FSQ-26': VsaRohde,
            'E8267D': VsgAgilent,
            'E5071B': VnaAgilentENA
        }

    if model in availableDrivers:
        return availableDrivers[model](resource=res)
    else:
        logger.error('Unknown model: ' + model)
        return None

class Instrument:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.drivername = 'Instrument'

        if 'resource' in kwargs:
            if 'addr' in kwargs:
                self.logger.warning('Called with res and addr.  res will take precidence')
            self.res = kwargs['resource']
        elif 'addr' in kwargs:
            self.res = visawrapper.ResourceManager.open_resource(kwargs['addr'])
        else:
            self.logger.error('Attempt to create instrument without address')
            raise InstrumentDriverException('Attempt to create instrument without address')
        
        self.res.open()
        self.res.read_termination = '\n'
        self.refreshIDN()

    @property
    def res(self):
        return self._res
    @res.setter
    def res(self, resource):
        self._res = resource
        
    @property
    def resource(self):
        return self._res
    @resource.setter
    def resource(self, resource):
        self._res = resource

    def refreshIDN(self):
        self.identity = parseIdnString(self.res.query('*IDN?'))
        
    def open(self):
        self.res.open()
        
    def close(self):
        self.res.close()
        
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
    
class Vsg(Instrument):
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
            
class Vsa(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Vsa'

    def setBandwidth(self, video=None, resolution=None):
        if video is not None:
            if video == 'auto':
                self.res.write('BAND:VID:AUTO ON')
            else:
                self.res.write('BAND:VID {:g} HZ'.format(video))

        if resolution is not None:
            if resolution == 'auto':
                self.res.write('BAND:RES:AUTO ON')
            else:
                self.res.write('BAND:RES {:g} HZ'.format(resolution))
                
    def getBandwidth(self):
        return self.res.query('BAND:RES?')
                
    def setFreq(self, start=None, stop=None, center=None, span=None):
        if start is not None:
            self.res.write('FREQ:STARt {:g} GHZ', start/1e9)

        if stop is not None:
            self.res.write('FREQ:STOP {:g} GHZ', stop/1e9)
        
        if center is not None:
            self.res.write('FREQ:CENTer {:g} GHZ', center/1e9)

        if span is not None:
            self.res.write('FREQ:SPAN {:g} HZ', span)


class VsaAgilent(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsaAgilent'
        
            
    def getMode(self):
        mode = self.res.query('INST:SEL?')
        
        modes = {
                'WIMAXOFDMA': 'wimax',
                'SA': 'spectrum',
                'VSA': 'vsa',
                'VSA89601':'vsa89601',
                'WLAN': 'wlan'
                }
        return modes.get(mode, 'Unknown')

class VsaRohde(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsaRohde'
                
    def getMode(self):
        mode = self.res.query('INST:SEL?')
        
        modes = {
            'WIM': 'wimax',
            'SAN': 'spectrum',
            'WLAN': 'wlan'
            }
        return modes.get(mode, 'Unknown')

class NetworkAnalyzer(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'NetworkAnalyzer'
        
class VnaAgilentENA(NetworkAnalyzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'NetworkAnalyzerAgilentENA'
        

    def setupAnalyzer(self, numPorts=2):
#                      ifbandwidth=1e3,
#                      freqStart=50e6,
#                      freqStop=20e9,
#                      rfpower=-20,
#                      numAverage=1,
#                      numPoints=201,
        
        self.numPorts = numPorts
        numTraces = round(math.pow(2,numPorts))
        
        # Create a list of measurement definitions
        self.traces = {}
        self.traces['definitions'] = []
        self.traces['indices'] = []
        for k1 in range(0,numPorts):
            for k2 in range(0,numPorts):
                self.traces['definitions'].append('S{:d}{:d}'.format(k1+1,k2+1))
                self.traces['indices'].append( (k1,k2) )
                
        # Apply these measurements to VNA
        self.res.write(':CALC:PAR:COUN {:d}'.format(numTraces))
        for index, measurement in enumerate(self.traces['definitions']):
            self.res.write(':CALC:PAR{:d}:DEF {:s}'.format(index+1, measurement))

    def getSParameters(self):
        sdata = {}
        sdata['f'] = self.getFrequencyList()

        numPoints = len(sdata['f'])
        sdata['s'] = np.ndarray(shape=(numPoints, self.numPorts, self.numPorts),
                                dtype='complex')
        
        for index, measurement in enumerate(self.traces['definitions']):
            self.res.write(':CALC:PAR{:d}:SEL'.format(index+1))
            #defreadback = self.res.query(':CALC:PAR{:d}:DEF?'.format(index+1))
            #self.logging.debug('{:s}  =  {:s}'.format(measurement, defreadback))
            indices = self.traces['indices'][index]
            sdata['s'][:,indices[0],indices[1]] = self.getTraceData()
            
        return(sdata)
        
    def setBlockMode(self, datatype, is_big_endian=True):
        if (datatype=='ascii'):
            self.res.write(':FORM:DATA ASC')
        else:
            if (datatype=='float'):
                self.res.write(':FORM:DATA REAL32')
            elif (datatype=='double'):
                self.res.write(':FORM:DATA REAL')
                
            if (is_big_endian):
                self.res.write(':FORM:BORD NORM')
            else:
                self.res.write(':FORM:BORD SWAP')
        
    def getFrequencyList(self):
#        self.res.write(':FORM:BORD NORMAL')      # Big Endian format
#        self.res.write(':FORM:DATA REAL32')      # Single precision
        self.setBlockMode('float', is_big_endian=True)
        
        # Ask for independant axis values
        result = self.res.query_binary_values(':SENS:FREQ:DATA?', datatype='f', is_big_endian=True)
        return result

    def triggerSingle(self):
        self.res.write(':TRIG:SOUR BUS')
        self.res.write(':TRIG:SING')
        self.res.query('*OPC?')
        
    def getTraceData(self):
        """
        Reads y-axis values for currently selected trace.
        Measurement must already be complete.
        """

        # self.res.write(':CALC:PAR1:SEL')   # Select Trace 1 on active channel

        self.setBlockMode('float', is_big_endian=True)       
        tracedata = self.res.query_binary_values(':CALC:DATA:SDAT?', datatype='f', is_big_endian=True)
        
        if ((len(tracedata) % 2) != 0):
            self.logger.error('S-Parameter trace read results malformed')
        
        numPoints = round(len(tracedata)/2)
        tracedata2 = np.reshape(tracedata, (numPoints,2))
        
        sdata = [ np.complex(c[0], c[1]) for c in tracedata2]

        return sdata