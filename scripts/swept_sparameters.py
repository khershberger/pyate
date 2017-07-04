"""
Measures S-Parameters over bias sweep
"""

import instrumentdrivers as drv

print('Script Runs!')

drv.core.createInstrument('TCPIP::192.168.26.132::INSTR')