"""
This module enables you to control various instruments over GPIB using
low-cost `Prologix controllers`_. The interface aims to emulate that
of PyVISA_, such that :class:`wanglib.prologix.instrument` objects
can be a drop-in replacement for :func:`visa.instrument`.

.. _`Prologix controllers`: http://prologix.biz/
.. _PyVISA: http://pyvisa.sourceforge.net/

For example, the canonical PyVISA three-liner

>>> import visa
>>> keithley = visa.instrument("GPIB::12")
>>> print keithley.ask("*IDN?")

is just one line longer with :mod:`wanglib.prologix`:

>>> from wanglib import prologix
>>> plx = prologix.prologix_USB('/dev/ttyUSBgpib')
>>> keithley = plx.instrument(12)
>>> print keithley.ask("*IDN?")

This extra verbosity is necessary to specify which GPIB controller to
use. Here we are using a Prologix GPIB-USB controller at
``/dev/ttyUSBgpib``. If we later switch to using a Prologix
GPIB-Ethernet controller, we would instead use

>>> plx = prologix.prologix_ethernet('128.223.xxx.xxx')

for our ``plx`` controller object (replace the ``xxx``es
with the controller's actual ip address, found using the
Prologix Netfinder tool).

Original code from https://github.com/baldwint/wanglib

"""

#from wanglib.util import Serial
from serial import Serial
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY
from time import sleep
import logging

import time
import select

from pyvisa import constants, attributes, errors
StatusCode = constants.StatusCode


class PrologixTimeout(Exception):
    pass

class ResourceManager(object):
    _prologixManager = {}
    
    
    @classmethod
    def getPrologixController(cls, ipAddress):
        logger = logging.getLogger(__name__) 
        if ipAddress not in cls._prologixManager:
            logger.debug('Creating new PrologixInterface instance')
            cls._prologixManager[ipAddress] = PrologixEthernet(ipAddress)
        else:
            logger.debug('Returning existing PrologixInterface instance')
            
        return cls._prologixManager[ipAddress]
     
    @classmethod
    def open_resource(cls, resource_name):
        resource = ResourcePrologix(resource_name)
        return resource
    
    @classmethod
    def getResourceParameters(cls, resource_name):
        params = resource_name.split(sep='::')
        if len(params) == 4:
            raise Exception('Incorrect resource string: %s', resource_name)
        dResource = {'controller': params[0],
                     'ipaddress': params[1],
                     'gpibaddress': params[2]}
        
        # Convert PROLOGIX to lower case
        if dResource['controller'] == 'PROLOGIX':
            dResource['controler'] = 'prologix'
        
        return dResource

class ResourcePrologix():
    """
        'PROLOGIX::172.29.92.133::1234::13'
    """

    def __init__(self, resource_name):
        self.logger = logging.getLogger(__name__)
        self._resource_name = resource_name
        
        self.timeout = 2.0
        
        resource_params = ResourceManager.getResourceParameters(resource_name)
        self._ip   = resource_params['ipaddress']
        self._addr = int(resource_params['gpibaddress'])

        self.interface = ResourceManager.getPrologixController(self._ip)

    def read(self):
        return self.interface.read(self._addr, timeout=self.timeout)
        
    def write(self, message):
        return self.interface.write(self._addr, message)
    
    def query(self, message):
        self.interface.write(self._addr, message)
        return self.interface.read(self._addr, timeout=self.timeout)

    def open(self):
        self.interface.open()
    
    def close(self):
        self.interface.close()
        pass
    
    def clear(self):
        self.interface.clear(self._addr)
        
    def read_termination(self, char):
        self.logger.warning('read_termination(char) not yet implemented')
        raise NotImplementedError
        
class _prologix_base(object):
    """
    Base class for Prologix controllers (ethernet/usb)
    """

    def __init__(self):
        """
        initialization routines common to USB and ethernet

        """
        self.logger = logging.getLogger(__name__)
        self.iolog  = logging.getLogger(__name__ + '.io')

        self._bufferPending = {}   # Separate buffer for each gpibaddr
        self._auto = None
        self._addr = None
        self._addrLast = None
        self.term_char = 10  # Decimal ASCII code for '\n'

    @property
    def addr(self):
        """
        The Prologix controller can calk to one instrument
        at a time. This sets the GPIB address of the
        currently addressed instrument.

        Use this attribute to set or check which instrument
        is currently selected:

        >>> plx.addr
        9
        >>> plx.addr = 12
        >>> plx.addr
        12

        """
        # query the controller for the current address
        # and save it in the _addr variable (why not)
        self.write(None, '++addr')
        addrReported = int(self.read(None))
        if addrReported != self._addr:
            self.logger.error('Address mismatch between Prologix device (%s) and manager (%s).  This is likely due to multiple connections to device.', str(addrReported), str(self._a_addr))
        self._addr = addrReported
        return self._addr
    
    @addr.setter
    def addr(self, new_addr, flush=False):
        """ Handles multiplexing betwween GPIB addresses.
        Ensures buffers are created.
        Ensures remaing data in data bus gets sved to appropriate buffer 
        
        new_addr:  Integer or None  (None is used to signify prologix controller commands) """
        
        # Make sure buffer exists for this address
        if new_addr not in self._bufferPending:
            self._bufferPending[new_addr] = bytearray()
        
        # Only change if new address is different than current
        if new_addr != self._addrLast:
            # We've switched to a new addresss, so need to clear out buffer for last addreess
            self.read_last(flush)
        
            self.logger.debug('Setting addr to %s from %s', str(new_addr), str(self._addrLast))
        
            # update local record
            # This will trigger storing of all data in bus to buffer
            self._addr = new_addr
    
            # Only need to update hardware if actual GPIB addres
            # 'None' is used to "address" the prolgix controller
            if new_addr is not None:
                # change to the new address
                self.write_raw('++addr {:d}'.format(new_addr), delay=0.1)
                # we update the local variable first because the 'write'
                # command may have a built-in delay. if we intterupt a program
                # during this period, the local attribute will be wrong
            
            # _addrLast must be updated after ++addr command to avoid 'issues'
            self._addrLast = new_addr

        else:
            self.logger.debug('Setting addr to %s (No Change)', str(new_addr))


    @property
    def auto(self):
        """
        Boolean. Read-after-write setting.

        The Prologix 'read-after-write' setting can
        automatically address instruments to talk after
        writing to them. This is usually convenient, but
        some instruments do poorly with it.

        """
        self.write(None, '++auto')
        self._auto = bool(int(self.read(None)))
        return self._auto
    @auto.setter
    def auto(self, val):
        self._auto = bool(val)
        self.write(None, '++auto {:d}'.format(self._auto))

    def version(self):
        """ Check the Prologix firmware version. """
        self.write(None, '++ver')
        return self.read(None)

    @property
    def savecfg(self):
        """
        Boolean. Determines whether the controller should save its
        settings in EEPROM.

        It is usually best to turn this off, since it will
        reduce `wear on the EEPROM`_ in applications that
        involve talking to more than one instrument.

        .. _`wear on the EEPROM`: http://www.febo.com/pipermail/time-nuts/2009-July/038952.html

        """
        self.write(None, '++savecfg')
        resp = self.read(None)
        
        if resp == 'Unrecognized command':
            raise Exception("""
                Prologix controller does not support ++savecfg
                update firmware or risk wearing out EEPROM
                            """)
        return bool(int(resp))
    @savecfg.setter
    def savecfg(self, val):
        d = bool(val)
        self.write(None, '++savecfg {:d}'.format(d))
    
    def assertDefaultConfiguration(self):
        # Disable configuration saving by default
        self.savecfg = False

        # Configure as controller
        self.write(None, '++mode 1')

        # Disable 'Read-after-Write'
        self.auto = True
        
        # Turn on EOI (Network to GPIB)
        self.write(None, '++eoi 1')
        
        # set EOS termination (GPIB writs)
        self.write(None, '++eos 0')  # Append CR+LF to instrument commands
        
        # Set EOT
        self.write(None, '++eot_enable 0')  # No character added to network reads
        
    def ping(self):
        return self.query(None, '++ver') 
    
class PrologixEthernet(_prologix_base):
    """
    Interface to a Prologix GPIB-Ethernet controller.

    To instantiate, use the ``prologix_ethernet`` factory:

    >>> plx = prologix.prologix_ethernet('128.223.xxx.xxx')

    Replace the ``xxx``es with the controller's actual ip
    address, found using the Prologix Netfinder tool.


    """

    def __init__(self, ip):
        # do common startup routines
        super(PrologixEthernet, self).__init__()

        self.max_recv_size = 1024
        self.select_timeout_default = 10e-6 
        self.timeout = 2.0   # In seconds  (I think this is right?)

        self.ip = ip
        
        # Open a socket to the controller
        self.open()

        # Set defaults
        self.assertDefaultConfiguration()

    @property
    def ip(self):
        return self._ip
    @ip.setter
    def ip(self, ipAddress):
        self._ip = ipAddress

    def testSocket(self):
        self.logger.info('Testing socket state')
        if self.bus.fileno() == -1:
            self.logger.info('Socket fileno = -1.')
            self.open()
        else:
            self.logger.info('Socket looks OK?')

    def open(self):
        self.logger.debug('Opening socket connection')
        self.logger.info('Establishing socket connection')
        self.iolog.info('*** Establishing socket connection ***')
        self.bus = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        #self.bus = socket(AF_INET, SOCK_STREAM)  #IPPROTO_TCP
        #self.bus.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        
        self.bus.settimeout(5)
        self.bus.connect((self._ip, 1234))
        
    def close(self):
        self.logger.debug('Closing socket connection')
        self.bus.close()

    def write_raw(self, message, delay=0.):
        self.logger.debug('write_raw(%s, delay=%g)', message, delay)
        messageFormatted  = '{:s}\r\n'.format(message).encode()

        for retries in range(3):
            try:
                self.testSocket()
                self.iolog.info(messageFormatted)
                self.bus.send(messageFormatted)
                sleep(delay)
                return
            except ConnectionResetError as e:
                self.logger.info('Connection reset.  Re-establishing')
                self.iolog.warning('*** Connection reset.  Re-establishing ***')
                self.open()
                self.testSocket()
            except ConnectionAbortedError as e:
                self.logger.warning('Connection aborted.  Re-establishing')
                self.open()
                self.testSocket()
        # If we made it here we failed 3 retry attempts
        raise ConnectionError('Cannot re-establish connection')

    def write(self, gpibaddr, message, delay=0.):
        # Change address
        self.addr = gpibaddr
        self.read_last()
        self.write_raw(message, delay=delay)


    def read_raw(self, count, buffer, term_char_en=True, timeout=None):
        """Reads data from device or interface synchronously.

        Copied from pyvisa-py.tcpip.TCPIPSocketSession

        Corresponds to viRead function of the VISA library.

        :param count: Number of bytes to be read.
        :return: data read, return value of the library call.
        :rtype: bytes, VISAStatus
        """

        if (count is not None) and (count < self.max_recv_size):
            chunk_length = count
        else:
            chunk_length = self.max_recv_size

        term_byte = bytes([self.term_char]) if self.term_char else b''
        term_char_en = True

        read_fun = self.bus.recv

        if timeout is None:
            timeout = self.timeout

        # minimum is in interval 1 - 100ms based on timeout, 1sec if no timeout
        # defined
        min_select_timeout = (1 if timeout is None else
                              max(min(timeout / 100.0, 0.1), 0.001))
        # initial 'select_timout' is half of timeout or max 2 secs
        # (max blocking time). min is from 'min_select_timeout'
        select_timout = (2.0 if timeout is None else
                         max(min(timeout / 2.0, 2.0), min_select_timeout))
        # time, when loop shall finish, None means never ending story if no
        # data arrives
        finish_time = (None if timeout is None else
                       (time.time() + timeout))

        while True:
            # check, if we have any data received (from pending buffer or
            # further reading)
            if count is not None:
                if len(buffer) >= count:
                    return StatusCode.success_max_count_read
            
            if term_char_en and term_byte in buffer:
                return StatusCode.success_termination_character_read

            # use select to wait for read ready, max `select_timout` seconds
            r, w, x = select.select([self.bus], [], [], select_timout)

            read_data = b''
            if self.bus in r:
                read_data = read_fun(chunk_length)
                buffer.extend(read_data)

            if not read_data:
                # can't read chunk or timeout
                if buffer:
                    # we have some data without termchar but no further data
                    # expected
                    return StatusCode.succes
                if finish_time and time.time() >= finish_time:
                    self.logger.warning('read_raw():  Timeout!')
                    return StatusCode.error_timeout

                # `select_timout` decreased to 50% of previous or
                # min_select_timeout
                select_timout = max(select_timout / 2.0, min_select_timeout)

    def read_last(self, flush=False):
        # Clears everything from bus.  Puts data into buffer if it was provided
        if (self._addrLast is None) or (flush):
            # FLush the socket since we don't have anywhere to put the data
            self.logger.debug('Discarding read buffer')
            buffer = bytearray()
        else:
            self.logger.debug('Saving read buffer to %s', self._addrLast)
            buffer = self._bufferPending[self._addrLast]    

        # Read all available data.  We don't acare about the ruesult
        # Just need to stash the results in the buffer for the last
        # addressed isntrument.
        # Extremely short timeout set since we only want what was already there.
        status = self.read_raw(None, buffer, term_char_en=False, timeout=0.001)
        
    def read(self, gpibaddr, count=None, timeout=None):
        if count is None:
            count = self.max_recv_size
            
        # Change address
        self.addr = gpibaddr
            
        # Send reqd request if a GPIB address provided
        if not self._auto and gpibaddr is not None:
            self.write_raw('++read eoi')

        # Get reference to the appropriate buffer
        buffer = self._bufferPending[gpibaddr]

        # Try to read data, if fail, send read request and try again
        status = self.read_raw(count, 
                               buffer, 
                               term_char_en=True,
                               timeout=timeout)
            
        if   status == StatusCode.success_termination_character_read:
            term_byte = bytes([self.term_char]) if self.term_char else b''
            term_byte_index = buffer.index(term_byte) + 1
        elif status == StatusCode.success_max_count_read:
            term_byte_index = len(buffer)
        elif status == StatusCode.error_timeout:
            raise errors.VisaIOError(errors.VI_ERROR_TMO)
        else:
            raise errors.VisaIOError('Unknown Error')
            
        out = buffer[:term_byte_index].decode().rstrip()  # Extract out output
        buffer[:term_byte_index] = []           # Remove otuput from buffer
        self.logger.debug('PrologiXEthernet.read():  %s', out)
        return out
            
        
        
    def clear(self, addr):
        # First write anyting in bus to last addressed buffer
        self.read_last()
        
        def clearHelper(addr):
            if isinstance(addr, int):
                self.write_raw('++addr {:d}'.format(addr))  # Switch to address
                self.write_raw('++clr')                     # Clear GPIB buffer
                self._bufferPending[addr].clear()           # Clear local buffer
                
        if addr == 'all':
            # Wipe out everything
            self.logger.debug('Clearing all buffers')
            for key in self._bufferPending:
                clearHelper(key)
        else:
            self.logger.debug('Clearing buffer %s', str(addr))
            clearHelper(addr)
            
        # Set addr back to where it should be
        self.write_raw('++addr {:d}'.format(self._addrLast))

class PrologixUSB(_prologix_base):
    """
    Interface to a Prologix GPIB-USB controller.

    To instantiate, specify the virtual serial port where the
    controller is plugged in:

    >>> plx = prologix.prologix_USB('/dev/ttyUSBgpib')

    On Windows, you could use something like

    >>> plx = prologix.prologix_USB('COM1')

    """

    def __init__(self, port='/dev/ttyUSBgpib', log=False):
        # do common startup routines
        super(PrologixUSB, self).__init__()
        
        # create a serial port object
        self.bus = Serial(port, baudrate=115200, rtscts=1, log=log)
        # if this doesn't work, try settin rtscts=0

        # flush whatever is hanging out in the buffer
        self.bus.readall()

        # Set defaults
        self.assertDefaultConfiguration()

    def write(self, command, delay=0.1):
        formattedCommand = '{:s}\r'.format(command)
        self.iolog.info(formattedCommand)
        self.bus.write(formattedCommand)
        sleep(delay)

    def readall(self):
        resp = self.bus.readall()
        self.iolog.info(resp)
        return resp.rstrip()

    def query(self, query, *args, **kwargs):
        """ Write to the bus, then read response. """
        #TODO: if bus doesn't have a logger
        self.bus.logger.debug('clearing buffer - expect no result')
        self.readall()  # clear the buffer
        self.write(query, *args, **kwargs)
        return self.readall()

controllers = dict()

def prologix_ethernet(ip):
    """
    Factory function for a Prologix GPIB-Ethernet controller.

    To instantiate, specify the IP address of the controller:

    >>> plx = prologix.prologix_ethernet('128.223.xxx.xxx')

    """
    if ip not in controllers:
        controllers[ip] = PrologixEthernet(ip)
    return controllers[ip]

def prologix_USB(port='/dev/ttyUSBgpib', log=False):
    """
    Factory for a Prologix GPIB-USB controller.

    To instantiate, specify the virtual serial port where the
    controller is plugged in:

    >>> plx = prologix.prologix_USB('/dev/ttyUSBgpib')

    On Windows, you could use something like

    >>> plx = prologix.prologix_USB('COM1')

    """
    if port not in controllers:
        controllers[port] = PrologixUSB(port)
    return controllers[port]

class instrument(object):
    """
    Represents an instrument attached to
    a Prologix controller.

    Pass the controller instance and GPIB address
    to the constructor. This creates a GPIB instrument
    at address 12:

    >>> plx = prologix_USB()
    >>> inst = instrument(plx, 12)

    A somewhat nicer way to do the second step would be to use the
    :meth:`instrument` factory method of the Prologix controller:

    >>> inst = plx.instrument(12)

    Once we have our instrument object ``inst``, we can use the
    :meth:`ask` and :meth:`write` methods to send GPIB queries and
    commands.

    """

    delay = 0.1
    """Seconds to pause after each write."""

    def __init__(self, controller, addr,
                 delay=0.1, auto=True):
        """
        Constructor method for instrument objects.

        required arguments:
            controller -- the prologix controller instance
                to which this instrument is attached.
            addr -- the address of the instrument
                on controller's GPIB bus.

        keyword arguments:
            delay -- seconds to wait after each write.
            auto -- read-after-write setting.

        """
        self.addr = addr
        self.auto = auto
        self.delay = delay
        self.controller = controller

    def _get_priority(self):
        """
        configure the controller to address this instrument

        """
        # configure instrument-specific settings
        if self.auto != self.controller._auto:
            self.controller.auto = self.auto
        # switch the controller address to the
        # address of this instrument
        if self.addr != self.controller._addr:
            self.controller.addr = self.addr

    def ask(self, command):
        """
        Send a query the instrument, then read its response.

        Equivalent to :meth:`write` then :meth:`read`.

        For example, get the 'ID' string from an EG&G model
        5110 lock-in:

        >>> inst.ask('ID')
        '5110'

        Is the same as:

        >>> inst.write('ID?')
        >>> inst.read()
        '5110'

        """
        # clear stray bytes from the buffer.
        # hopefully, there will be none.
        # if there are, print a warning
#        clrd = self.controller.bus.inWaiting()
#        if clrd > 0:
#            print clrd, 'bytes cleared'
#        self.read()  # clear the buffer
        self.write(command)
        return self.read()

    def read(self): # behaves like readall
        """
        Read a response from an instrument.

        """
        self._get_priority()
        if not self.auto:
            # explicitly tell instrument to talk.
            self.controller.write('++read eoi', delay=self.delay)
        return self.controller.readall()

    def write(self, command):
        """
        Write a command to the instrument.

        """
        self._get_priority()
        self.controller.write(command, delay=self.delay)

