"""
Manages ResourceManager and Resource instances
"""

import logging
import pyvisa
from . import prologix

from pyvisa.errors import VisaIOError
from pyvisa.constants import StatusCode


class InitializationError(Exception):
    pass


class ResourceTimeout(Exception):
    pass


class ResourceManager:
    """
    Singleton to store resource instances

    Attributes:

    """

    resourcemanagers = {}
    resources = {}

    @classmethod
    def getResourceManager(cls, rmtype):
        logger = logging.getLogger(__name__)

        if rmtype not in cls.resourcemanagers:
            if rmtype == "pyvisa":
                logger.debug("Creating new pyvisa.ResourceManager instance")
                cls.resourcemanagers[rmtype] = pyvisa.ResourceManager()
            elif rmtype in ["pyvisa-py", "pyvisa-ivi"]:
                logger.debug("Creating new pyvisa-py.ResourceManager instance")
                cls.resourcemanagers[rmtype] = pyvisa.ResourceManager("@ivi")
            elif rmtype == "prologix":
                logger.debug("Creating new prologixManager instance")
                cls.resourcemanagers[rmtype] = prologix.ResourceManager()
            else:
                raise ValueError("Unknown ResourceManager type: %s", rmtype)
        else:
            logger.debug("Returning existing ResourceManager instance")

        return cls.resourcemanagers[rmtype]

    @classmethod
    def open_resource_old(cls, resource_name, backend="@py", **kwargs):
        logger = logging.getLogger(__name__)
        # First see if this resource_name is already created
        if resource_name in cls.resources:
            logger.info("Resource already exists: {:s}".format(resource_name))
            resource = cls.resources[resource_name]

            # We're fixing this hopefully
            # resource.close()
            # resource.open()
        else:
            logger.info("Creating new resource: {:s}".format(resource_name))
            resource_prefix = resource_name.split(sep="::")[0]
            if backend == "@prologix":
                # Create prologix resource
                rm = cls.getResourceManager("prologix")
            elif backend == "@py":
                rm = cls.getResourceManager("pyvisa-py")
            else:
                # Create pyvisa rsource
                rm = cls.getResourceManager("pyvisa")

            resource = rm.open_resource(resource_name, **kwargs)
            cls.addResource(resource_name, resource)

        resource.open()

        return resource

    @classmethod
    def open_resource(cls, resource_name, backend="@py", **kwargs):
        logger = logging.getLogger(__name__)

        # rm.visalib.open_default_resource_manager

        if backend == "@prologix":
            # Create prologix resource
            rm = cls.getResourceManager("prologix")
        elif backend == "@py":
            rm = cls.getResourceManager("pyvisa-py")
        else:
            # Create pyvisa rsource
            rm = cls.getResourceManager("pyvisa")

        # Check if it is already open
        resource_valid = False
        for resource in rm.list_opened_resources():
            # Check if it is what we want
            try:
                if resource_name == resource.resource_name:
                    logger.debug("Resource %s found in opened_resources list", resource_name)
                    resource_valid = True
                    break
            except VisaIOError as e:
                if e.error_code == StatusCode.error_invalid_object:
                    logger.debug("Resource %s found in opened_resources list but is invalid", resource_name)
                    # Bad session
                    break
                else:
                    raise

        if not resource_valid:
            logger.info("Creating new resource: {:s}".format(resource_name))

            resource = rm.open_resource(resource_name, **kwargs)
            cls.addResource(resource_name, resource)
        
        return resource

    @classmethod
    def addResource(cls, name, newResource):
        # if name in cls.resources:
        #     raise KeyError(name + " already exists")
        # else:
        cls.resources[name] = newResource

    @classmethod
    def getResources(cls):
        logger = logging.getLogger(__name__)
        logger.info("getResources()")
        return cls.resources

    @classmethod
    def getResource(cls, name):
        return cls.resources[name]

    @classmethod
    def closeAll(cls):
        logger = logging.getLogger(__name__)
        for keyRes in cls.resources:
            logger.info("Closing: {:s}".format(keyRes))
            try:
                cls.resources[keyRes].close()
            except pyvisa.VisaIOError:
                logger.warning(
                    "VisaIOError occured while trying to close {:s}".format(keyRes))
