# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 14:09:15 2017

@author: kyleh
"""

import logging
import visawrapper

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
            'E8267D': VsgAgilent
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
