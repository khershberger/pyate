"""
Manages ResourceManager and Resource instances
"""

import logging
import pyvisa
from . import prologix

class InitializationError(Exception):
    pass

class ResourceTimeout(Exception):
    pass

class ResourceManager():
    """
    Singleton to store resource instances
    
    Attributes:
    
    """ 
    
    resourcemanager = None
    _prologixManager = {}
    resources = {}
    
    @classmethod
    def getResourceManager(cls):
        logger = logging.getLogger(__name__) 
        if cls.resourcemanager is None:
            logger.debug('Creating new pyvisa.ResourceManager instance')
            cls.resourcemanager = pyvisa.ResourceManager()
        else:
            logger.debug('Returning existing pyvisa.ResourceManager instance')
            
        return cls.resourcemanager

    @classmethod
    def getPrologixInterface(cls, ipAddress):
        logger = logging.getLogger(__name__) 
        if ipAddress not in cls.prologix:
            logger.debug('Creating new PrologixInterface instance')
            cls._prologixManager[ipAddress] = prologix.PrologixEthernet(ipAddress)
        else:
            logger.debug('Returning existing PrologixInterface instance')
            
        return cls._prologixManager[ipAddress]
    
    @classmethod
    def open_resource(cls, resource_name, **kwargs):
        logger = logging.getLogger(__name__) 
        # First see if this resource_name is already created
        if resource_name in cls.resources:
            logger.info('Resource already exists: {:s}'.format(resource_name))
            resource = cls.resources[resource_name]
            
            resource.close()
            resource.open()
        else:
            logger.info('Creating new resource: {:s}'.format(resource_name))
            resource_prefix = resource_name.split(sep='::')[0]
            if resource_prefix == 'PROLOGIX':
                # Create prologix resource
                resource = ResourcePrologix(resource_name)
            else:
                # Create pyvisa rsource
                rm = cls.getResourceManager()
                resource = rm.open_resource(resource_name, **kwargs)
                
            cls.addResource(resource_name, resource)
        
        return resource
    
    @classmethod
    def addResource(cls, name, newResource):
        if name in cls.resources:
            raise KeyError(name + ' already exists')
        else:
            cls.resources[name] = newResource
        
    @classmethod
    def getResources(cls):
        logger = logging.getLogger(__name__) 
        logger.info('getResources()')
        return cls.resources
    
    @classmethod
    def getResource(cls, name):
        return cls.resources[name]

    @classmethod
    def closeAll(cls):
        for res in cls.resources:
            cls.resources[res].close()

class ResourcePrologix():
    """
        'PROLOGIX::172.29.92.133::1234::13'
    """

    def __init__(self, resource_name):
        self.logger = logging.getLogger(__name__)
        self._resource_name = resource_name
        
        resource_params = resource_name.split(sep='::')
        
        self._ip   = resource_params[1]
        self._port = int(resource_params[2])
        self._addr = int(resource_params[3])

        if self._port != 1234:
            raise AttributeError('Prologix interface only supports port 1234')
        
        self.interface = ResourceManager.getPrologixInterface(self._ip)

    def read(self):
        self.interface.addr = self._addr
        return self.interface.readall()
        
    def write(self, command, delay=0.1):
        self.interface.addr = self._addr
        return self.interface.write(command, lag=delay)
    
    def query(self, command, delay=0.1):
        self.interface.addr = self._addr
        self.interface.write(command, lag=delay)
        #return self.interface.readall()
        return self.read()

    def open(self):
        pass
    
    def close(self):
        pass
        
    def read_termination(self, char):
        self.logger.warning('read_termination(char) not yet implemented')
        
        