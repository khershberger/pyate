### Parameter Subsystem
class for each parameter:
 - set
 - verify
 - get

each parameter gets registered with core parameter control system (Class)
Construct iterator with parameter sweep values


### Main Module

- Load settings files
- Load module
     - query instruments required
- Construct parameter sweep
     - query instruments required
- Initialize instruments required from test-set settings file
- Initialize parameters weep
- Initialize module measurement
- Initialize data file
- Craete plot window
- Start sweep
- Make measurement
- Add row to data file
- Update plot window
- Close data file
- Tear-down measurement
- Tear-down parameter sweep

#### Classes:
- MeasurementSystem
    - generateDefaultSetup
    - getCorrectionAtParameter
    - getConfigurationPath
    - loadConfigFileGeneral
    - loadCOnfigFileMeasurement(path)
        - loadConfigFileTestset
        - loadConfigFileCalibration
    - createInstruments
- ParameterSweep
    - loadConfig
    - addSweep
    - listInstruments
    - createIterator
- Measurement
     - loadConfig
     - listInstruments
     - setupMeasurement
     - performMeasurement
     - teardownMeasurement
- DataSystem
     - createDataSet
     - newDataSubset
     - megerDataSubset
     - closeDataset
- PlotSystem

#### Setup files:
- testset
    - instruments
- calibration
    
- measurementsetup
    - testset
    - general settings
    - plugins
    - sweeps
    - pluginsettings