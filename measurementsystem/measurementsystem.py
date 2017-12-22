'''
Created on Dec 22, 2017

@author: kyleh
'''

import configparser
import os

class MeasurementSystem():
    def __init__(self):
        _configGlobal = None
        _configMeasurement = None
    
    def getConfigurationDefaultPath(self):
        """
        Attempts to determine user's home directory, and creates a sub-directory for PyATE
        
        Inspiration & code snippets came from:
        https://stackoverflow.com/a/10644400
        """
        
        projectname='pyate'
        
        if os.name != 'posix':
            from win32com.shell import shellcon, shell
            homedir = '{}'.format(shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0))
            projdir = '{0}\\{1}'.format(homedir, projectname)
        else:
            homedir = '{}'.format(os.path.expanduser('~'))
            projdir = '{0}/.{1}'.format(homedir, projectname)

        if not os.path.isdir(projdir):
            os.mkdir(projdir)
            
        return projdir

    def loadConfigFileGlobal(self):
        _configGlobal = configparser.ConfigParser()
        _configGlobal.read('pyate.ini')

    def loadCOnfigFileMeasurement(self, filename):
        _configMeasurement = configparser.ConfigParser()
        _configGlobal.read(filename)
         
    def loadConfigFileTestset(self):
    def loadConfigFileCalibration(self):
    
    def getDefaultConfiguration(self):
        pass
    
    def getCorrectionAtParameter(self):
        pass
    

    def createInstruments(self):