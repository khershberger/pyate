# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 14:09:15 2017

@author: kyleh
"""

#from .instrument import Instrument
# from . import powersupply
# from . import spectrumanalyzer
# from . import signalgenerator
# from . import networkanalyzer
# from . import waveformgenerator
# from . import powermeter
# from . import oscilloscope

import logging
import pyate.visawrapper as visawrapper

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
    def createInstrument(cls, addr, instrumenttype='generic'):
        logger = logging.getLogger(__name__)
        
        # First get instrument resource
        #res = pyvisa.ResourceManager().open_resource(addr)
        res = visawrapper.ResourceManager.open_resource(addr)
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
    def parseIdnString(cls, idn):
        parsed = idn.split(sep=',')
        return {'vendor':   parsed[0].strip(),
                'model' :   parsed[1].strip(),
                'serial':   parsed[2].strip(),
                'frimware': parsed[3].strip() }     

class InstrumentDriverException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
 
                
        