# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 13:51:46 2017

@author: kyleh
"""

import logging
import visawrapper
import pyvisa.errors
from . import manager 

class InstrumentIOError(Exception):
    pass

class InstrumentNothingToRead(Exception):
    pass

class Instrument:
    @classmethod
    def registerModels(cls, models):
        def _internal(pyclass):
            manager.InstrumentManager.registerInstrument(models, pyclass)
            return pyclass
        return _internal
    
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
            raise manager.InstrumentDriverException('Attempt to create instrument without address')
        
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
        self.identity = manager.InstrumentManager.parseIdnString(self.res.query('*IDN?'))
        
    def open(self):
        self.res.open()
        
    def close(self):
        self.res.close()
        
    def write(self, command, retries=3):
        for n in range(retries):
            try:
                self.res.write(command)
                return
            except visawrapper.prologix.PrologixTimeout as e:
                self.logger.warning('Prologix Timeout occured during Instrument.write() operation')
            except pyvisa.VisaIOError as e:
                if e.error_code == pyvisa.errors.VI_ERROR_TMO:
                    self.logger.warning('NI Timeout occured during Instrument.write() operation')
                else:
                    raise e
        
        raise InstrumentIOError('Instrument.write() Max retries exceeded')
        
    def read(self):
        try:
            return self.res.read()
        except visawrapper.prologix.PrologixTimeout as e:
            self.logger.warning('Prologix Timeout occured during Instrument.write() operation')
            raise InstrumentNothingToRead('Instrument.read() Nothing to read???')
        except pyvisa.VisaIOError as e:
            if e.error_code == pyvisa.errors.VI_ERROR_TMO:
                self.logger.warning('NI Timeout occured during Instrument.read() operation')
                raise InstrumentNothingToRead('Instrument.read() Nothing to read???')
            else:
                raise e

        
    def query(self, command, retries=3):
        for n in range(retries):
            self.write(command, retries)
            try:
                return self.res.read()
            except visawrapper.prologix.PrologixTimeout as e:
                self.logger.warning('Prologix Timeout occured during Instrument.read() operation')
            except pyvisa.VisaIOError as e:
                if e.error_code == pyvisa.errors.VI_ERROR_TMO:
                    self.logger.warning('NI Timeout occured during Instrument.query() operation')
                else:
                    raise e
                        
        
        raise InstrumentNothingToRead('Instrument.read() Nothing to read???')
        
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