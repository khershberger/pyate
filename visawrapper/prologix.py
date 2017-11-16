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
from socket import socket, timeout, AF_INET, SOCK_STREAM, IPPROTO_TCP
from time import sleep
import logging

class PrologixTimeout(Exception):
    pass

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
        self._addr = int(self.ask("++addr"))
        return self._addr
    @addr.setter
    def addr(self, new_addr):
        # update local record
        self._addr = new_addr
        # change to the new address
        self.write('++addr {:d}'.format(new_addr))
        # we update the local variable first because the 'write'
        # command may have a built-in lag. if we intterupt a program
        # during this period, the local attribute will be wrong

    @property
    def auto(self):
        """
        Boolean. Read-after-write setting.

        The Prologix 'read-after-write' setting can
        automatically address instruments to talk after
        writing to them. This is usually convenient, but
        some instruments do poorly with it.

        """
        self._auto = bool(int(self.ask("++auto")))
        return self._auto
    @auto.setter
    def auto(self, val):
        self._auto = bool(val)
        self.write('++auto {:d}'.format(self._auto))

    def version(self):
        """ Check the Prologix firmware version. """
        return self.ask("++ver")

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
        resp = self.ask("++savecfg")
        if resp == 'Unrecognized command':
            raise Exception("""
                Prologix controller does not support ++savecfg
                update firmware or risk wearing out EEPROM
                            """)
        return bool(int(resp))
    @savecfg.setter
    def savecfg(self, val):
        d = bool(val)
        self.write('++savecfg {:d}'.format(d))

    def instrument(self, addr, **kwargs):
        """
        Factory function for :class:`instrument` objects.

        >>> plx.instrument(12)

        is equivalent to

        >>> instrument(plx, 12)

        `addr` -- the GPIB address for an instrument
                  attached to this controller.
        """
        return instrument(self, addr, **kwargs)
    
    def assertDefaultConfiguration(self):
        # Disable configuration saving by default
        self.savecfg = False

        # Configure as controller
        self.write('++mode 1')

        # Disable 'Read-after-Write'
        self.auto = True
        
    def ping(self):
        return self.ask('++ver') 

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

        self.ip = ip
        
        # Open a socket to the controller
        self.openSocket()

        # Set defaults
        self.assertDefaultConfiguration()

    @property
    def ip(self):
        return self._ip
    @ip.setter
    def ip(self, ipAddress):
        self._ip = ipAddress

    def openSocket(self):
        self.logger.info('Establishing socket connection')
        self.iolog.info('*** Establishing socket connection ***')
        self.bus = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        self.bus.settimeout(5)
        self.bus.connect((self._ip, 1234))

    def write(self, command, lag=0.0, attempts=0):
        formattedCommand = '{:s}\n'.format(command).encode()
        
        if attempts < 2:
            try:
                self.iolog.info(formattedCommand)
                self.bus.send(formattedCommand)
                sleep(lag)
            except ConnectionResetError as e:
                self.logger.info('Connection reset.  Re-establishing')
                self.iolog.info('*** Connection reset.  Re-establishing ***')
                self.openSocket()
                self.write(command, lag, attempts=attempts+1)
            except ConnectionAbortedError as e:
                self.logger.info('Connection aborted.  Re-establishing')
                self.openSocket()
                self.write(command, lag, attempts=attempts+1)
        else:
            raise ConnectionError('Cannot re-establish connection')

    def readall(self, attempts=0):
        if attempts < 2:
            try:
                self.write('++read eoi')
                resp = self.bus.recv(128) # 128 should be enough, right?
                self.iolog.info(resp)
            except ConnectionResetError as e:
                self.logger.info('Connection reset.  Re-establishing')
                self.iolog.info('*** Connection reset.  Re-establishing ***')
                self.openSocket()
                self.readall(attempts=attempts+1)
            except timeout as e:
                raise PrologixTimeout('Timeout during readall()')
        else:
            raise ConnectionError('Cannot re-establish connection')
                
        return resp.decode().rstrip()

    def ask(self, query, *args, **kwargs):
        """ Write to the bus, then read response. """
        # no need to clear buffer
        self.write(query, *args, **kwargs)
        return self.readall()


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

    def write(self, command, lag=0.1):
        formattedCommand = '{:s}\r'.format(command)
        self.iolog.info(formattedCommand)
        self.bus.write(formattedCommand)
        sleep(lag)

    def readall(self):
        resp = self.bus.readall()
        self.iolog.info(resp)
        return resp.rstrip()

    def ask(self, query, *args, **kwargs):
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
            self.controller.write('++read eoi', lag=self.delay)
        return self.controller.readall()

    def write(self, command):
        """
        Write a command to the instrument.

        """
        self._get_priority()
        self.controller.write(command, lag=self.delay)

