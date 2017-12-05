# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 17:47:53 2017

@author: kyleh
"""

"""
Measures PVT & control ARB generators

To Setup:

#cd "../../../workspace/pate"
import sys
sys.path.insert(0, "../../workspace-python36/pate")
%load_ext autoreload
%autoreload 2

"""

import instrumentdrivers as drv
import numpy as np

wg1 = drv.InstrumentManager.createInstrument('GPIB::10::INSTR')
wg1.testConnection(attemptReset=True)

n = 10
xx = np.linspace(0,1,n)
testsignal = np.concatenate((np.int32(8191*np.sin(2*np.pi*xx)),
                             np.int32(-8191*np.ones(n)),
                             np.int32(8191*np.ones(n))))


wg1.sendWaveform(testsignal, samplerate=1e6, amplitude=1, offset=0, channel=1)
wg1.setupBurst(1)

wg1.setupPulse(channel=2, mode=None, period=1e-3, width=100e-6, vlow=0, vhigh=3.3)
