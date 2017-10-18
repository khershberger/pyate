# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 14:09:15 2017

@author: kyleh
"""

from .instrument import Instrument
from . import powersupply
from . import spectrumanalyzer
from . import signalgenerator
from . import networkanalyzer
from . import waveformgenerator
from . import powermeter
from . import oscilloscope

import logging
import visawrapper

def createInstrument(addr, type='generic'):
    logger = logging.getLogger(__name__)
    
    # First get instrument resource
    #res = pyvisa.ResourceManager().open_resource(addr)
    res = visawrapper.ResourceManager.open_resource(addr)
    identity = Instrument.parseIdnString(res.query('*IDN?'))
    res.close()

    model = identity['model']

    logger.debug('Model = ' + model)    
    availableDrivers = {
            'DP832':   powersupply.PowerSupplyDP832,
            'FSQ-26':  spectrumanalyzer.VsaRohde,
            'E8267D':  signalgenerator.VsgAgilent,
            'E5071B':  networkanalyzer.VnaAgilentENA,
            'DG1032Z': waveformgenerator.WaveformGenerator,
            'E4417A':  powermeter.PowerMeter,
            'DS1054Z': oscilloscope.Oscilloscope
        }

    if model in availableDrivers:
        return availableDrivers[model](resource=res)
    else:
        logger.error('Unknown model: ' + model)
        return None

 
                
        