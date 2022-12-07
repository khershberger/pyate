# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 14:09:15 2017

@author: kyleh
"""

import logging
from pyate import visawrapper

class InstrumentManager(object):
    
    #_models = []
    _models = dict()
    
    @classmethod
    def registerInstrument(cls, models, pyclass):
        if isinstance(models, str):
            cls._models[models] = pyclass
        elif isinstance(models, list):        
            for model in models:
                cls._models[model] = pyclass
                
    @classmethod
    def getAvailableInstruments(cls):
        return cls._models

    @classmethod
    def getResourceManager(cls, backend='pyvisa'):
        return visawrapper.ResourceManager.getResourceManager(backend)
                
    @classmethod
    def createInstrument(cls, addr, backend='pyvisa', instrumenttype='generic'):
        logger = logging.getLogger(__name__)
        
        # First get instrument resource
        #res = pyvisa.ResourceManager().open_resource(addr)
        res = visawrapper.ResourceManager.open_resource(addr, backend)
        identity = cls.parseIdnString(res.query('*IDN?'))
        res.close()
    
        model = identity['model']
    
        logger.debug('Model = ' + model)    
#         availableDrivers = {
#                 'DP832':   powersupply.PowerSupplyDP832,
#                 'FSQ-26':  spectrumanalyzer.VsaRohde,
#                 'E8267D':  signalgenerator.VsgAgilent,
#                 'E5071B':  networkanalyzer.VnaAgilentENA,
#                 'DG1032Z': waveformgenerator.WaveformGenerator,
#                 'E4417A':  powermeter.PowerMeter,
#                 'DS1054Z': oscilloscope.Oscilloscope
#             }
    
        if model in cls._models:
            return cls._models[model](resource=res)
        else:
            logger.error('Unknown model: ' + model)
            return None
        
    @classmethod
    def getIden(cls, addr):
        res = visawrapper.ResourceManager.open_resource(addr)
        idn = res.query('*IDN?')
        res.close()        
        return idn
        
    @classmethod
    def parseIdnString(cls, idn):
        parsed = idn.split(sep=',')
        if len(parsed) != 4:
            return {'vendor':   'Unknown',
                    'model':    'Unknown',
                    'serial':   'Unknown',
                    'firmware': 'Unknown',
                    'ident':    idn}
        else:
            return {'vendor':   parsed[0].strip(),
                    'model' :   parsed[1].strip(),
                    'serial':   parsed[2].strip(),
                    'frimware': parsed[3].strip() }     

class InstrumentDriverException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
 
                
        