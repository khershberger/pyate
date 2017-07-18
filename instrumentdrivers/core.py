# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 14:09:15 2017

@author: kyleh
"""

import instrumentdrivers as idrv
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
            'DP832':  idrv.powersupply.PowerSupplyDP832,
            'FSQ-26': idrv.spectrumanalyzer.VsaRohde,
            'E8267D': idrv.signalgenerator.VsgAgilent,
            'E5071B': idrv.networkanalyzer.VnaAgilentENA,
            'DG1032Z': idrv.waveformgenerator.PulseGenerator
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
        
    def testConnection(self, attemptReset=False, triesLeft=1):
        try:
            self.refreshIDN()
            return True
        except visawrapper.pyvisa.errors.VisaIOError as e:
            if attemptReset and (triesLeft > 0):
                self.res.close()
                self.res.open()
                return self.testConnection(attemptReset=attemptReset, 
                                           triesLeft=triesLeft-1)
            else:
                return False

                    
                
        