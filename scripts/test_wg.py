# -*- coding: utf-8 -*-
"""
Created on Mon Jul 17 10:29:04 2017

@author: kyleh
"""

channel = 1

wg1.res.write("*CLS")

wg1.setupBurst(channel)
wg1.res.write("*OPC")

# wg1.res.write(':SOUR{:d}:BURS:MODE TRIG'.format(channel))
# wg1.res.write(':SOUR{:d}:BURS:NCYC 1'.format(channel))
# wg1.res.write(':SOUR{:d}:BURS:TRIG:SOUR EXT'.format(channel))
# wg1.res.write(':SOUR{:d}:BURS:TRIG:SLOP POS'.format(channel))
# wg1.res.write(':SOUR{:d}:BURS:STAT ON;*OPC'.format(channel))

opc = 0
while opc != 1:
    status = int(wg1.res.query("*ESR?"))
    print(status)
    opc = status & 1
