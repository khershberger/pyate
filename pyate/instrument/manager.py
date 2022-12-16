# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 14:09:15 2017

@author: kyleh
"""

import logging
from re import search

from pyate import visawrapper


class InstrumentManager(object):

    # _models = []
    _models = dict()

    @classmethod
    def register_instrument(cls, models, pyclass):
        if isinstance(models, str):
            cls._models[models] = pyclass
        elif isinstance(models, list):
            for model in models:
                cls._models[model] = pyclass

    @classmethod
    def get_available_instruments(cls):
        return cls._models

    @classmethod
    def get_resource_manager(cls, backend="pyvisa"):
        return visawrapper.ResourceManager.get_resource_manager(backend)

    @classmethod
    def create_instrument(cls, addr, backend="pyvisa", instrumenttype="generic"):
        logger = logging.getLogger(__name__)

        # First get instrument resource
        # res = pyvisa.ResourceManager().open_resource(addr)
        res = visawrapper.ResourceManager.open_resource(addr, backend)
        identity = cls.parse_ident_string(res.query("*IDN?"))
        res.close()

        model = identity["model"]

        logger.debug("Model = " + model)

        driver_class = cls.find_instrument_class(cls, model)

        if driver_class is not None:
            logger.debug("Found match for %s: %s", model, str(driver_class))
            return driver_class(resource=res)
        else:
            # No driver found, return the bad news...
            logger.error("Unknown model: " + model)
            return None

    @classmethod
    def find_instrument_class(cls, model_to_find):
        for model in cls._models.keys():
            if search(model, model_to_find):
                driver_class = cls._models[model]
                return driver_class
        return None

    @classmethod
    def get_ident(cls, addr):
        res = visawrapper.ResourceManager.open_resource(addr)
        idn = res.query("*IDN?")
        res.close()
        return idn

    @classmethod
    def parse_ident_string(cls, idn):
        parsed = idn.split(sep=",")
        if len(parsed) != 4:
            return {"vendor": "Unknown", "model": "Unknown", "serial": "Unknown", "firmware": "Unknown", "ident": idn}
        else:
            return {
                "vendor": parsed[0].strip(),
                "model": parsed[1].strip(),
                "serial": parsed[2].strip(),
                "frimware": parsed[3].strip(),
            }


class InstrumentDriverException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
