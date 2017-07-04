'''
Created on Jul 4, 2017

@author: kyleh
'''

import instrumentdrivers.core as idcore

class Vsa(idcore.Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'Vsa'

    def setBandwidth(self, video=None, resolution=None):
        if video is not None:
            if video == 'auto':
                self.res.write('BAND:VID:AUTO ON')
            else:
                self.res.write('BAND:VID {:g} HZ'.format(video))

        if resolution is not None:
            if resolution == 'auto':
                self.res.write('BAND:RES:AUTO ON')
            else:
                self.res.write('BAND:RES {:g} HZ'.format(resolution))
                
    def getBandwidth(self):
        return self.res.query('BAND:RES?')
                
    def setFreq(self, start=None, stop=None, center=None, span=None):
        if start is not None:
            self.res.write('FREQ:STARt {:g} GHZ', start/1e9)

        if stop is not None:
            self.res.write('FREQ:STOP {:g} GHZ', stop/1e9)
        
        if center is not None:
            self.res.write('FREQ:CENTer {:g} GHZ', center/1e9)

        if span is not None:
            self.res.write('FREQ:SPAN {:g} HZ', span)


class VsaAgilent(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsaAgilent'
        
            
    def getMode(self):
        mode = self.res.query('INST:SEL?')
        
        modes = {
                'WIMAXOFDMA': 'wimax',
                'SA': 'spectrum',
                'VSA': 'vsa',
                'VSA89601':'vsa89601',
                'WLAN': 'wlan'
                }
        return modes.get(mode, 'Unknown')

class VsaRohde(Vsa):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivername = 'VsaRohde'
                
    def getMode(self):
        mode = self.res.query('INST:SEL?')
        
        modes = {
            'WIM': 'wimax',
            'SAN': 'spectrum',
            'WLAN': 'wlan'
            }
        return modes.get(mode, 'Unknown')