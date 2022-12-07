# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 10:43:58 2017

@author: kyleh
"""

"""
To Setup:

cd "../../../workspace/pate"
%load_ext autoreload
%autoreload 2
"""

import visawrapper
import instrumentdrivers.core as drvcore

visa_address = "TCPIP::192.168.26.132::INSTR"
instr = visawrapper.ResourceManager.open_resource(visa_address)
result = instr.query("*IDN?")
print(result)
instr.close()

vna = drvcore.createInstrument(visa_address)
