"""
Created on Jul 4, 2017

@author: kyleh
"""

from pyate.instrument import Instrument
import math
import numpy as np


class NetworkAnalyzer(Instrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "NetworkAnalyzer"


@Instrument.register_models(["E5071B"])
class VnaAgilentENA(NetworkAnalyzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_name = "NetworkAnalyzerAgilentENA"

    def setup_analyzer(self, num_ports=2):
        #                      ifbandwidth=1e3,
        #                      freq_start=50e6,
        #                      freq_stop=20e9,
        #                      rfpower=-20,
        #                      num_average=1,
        #                      num_points=201,

        self.num_ports = num_ports
        num_traces = round(math.pow(2, num_ports))

        # Create a list of measurement definitions
        self.traces = {}
        self.traces["definitions"] = []
        self.traces["indices"] = []
        for k1 in range(0, num_ports):
            for k2 in range(0, num_ports):
                self.traces["definitions"].append("S{:d}{:d}".format(k1 + 1, k2 + 1))
                self.traces["indices"].append((k1, k2))

        # Apply these measurements to VNA
        self.write(":CALC:PAR:COUN {:d}".format(num_traces))
        for index, measurement in enumerate(self.traces["definitions"]):
            self.write(":CALC:PAR{:d}:DEF {:s}".format(index + 1, measurement))

    def get_s_parameters(self):
        sdata = {}
        sdata["f"] = self.get_frequency_list()

        num_points = len(sdata["f"])
        sdata["s"] = np.ndarray(shape=(num_points, self.num_ports, self.num_ports), dtype="complex")

        for index, measurement in enumerate(self.traces["definitions"]):
            self.write(":CALC:PAR{:d}:SEL".format(index + 1))
            # defreadback = self.query(':CALC:PAR{:d}:DEF?'.format(index+1))
            # self.logging.debug('{:s}  =  {:s}'.format(measurement, defreadback))
            indices = self.traces["indices"][index]
            sdata["s"][:, indices[0], indices[1]] = self.get_trace_data()

        return sdata

    def set_block_mode(self, datatype, is_big_endian=True):
        if datatype == "ascii":
            self.write(":FORM:DATA ASC")
        else:
            if datatype == "float":
                self.write(":FORM:DATA REAL32")
            elif datatype == "double":
                self.write(":FORM:DATA REAL")

            if is_big_endian:
                self.write(":FORM:BORD NORM")
            else:
                self.write(":FORM:BORD SWAP")

    def get_frequency_list(self):
        #        self.write(':FORM:BORD NORMAL')      # Big Endian format
        #        self.write(':FORM:DATA REAL32')      # Single precision
        self.set_block_mode("float", is_big_endian=True)

        # Ask for independant axis values
        result = self.query_binary_values(":SENS:FREQ:DATA?", datatype="f", is_big_endian=True)
        return result

    def trigger_single(self):
        self.write(":TRIG:SOUR BUS")
        self.write(":TRIG:SING")
        self.query("*OPC?")

    def get_trace_data(self):
        """
        Reads y-axis values for currently selected trace.
        Measurement must already be complete.
        """

        # self.write(':CALC:PAR1:SEL')   # Select Trace 1 on active channel

        self.set_block_mode("float", is_big_endian=True)
        tracedata = self.query_binary_values(":CALC:DATA:SDAT?", datatype="f", is_big_endian=True)

        if (len(tracedata) % 2) != 0:
            self.logger.error("S-Parameter trace read results malformed")

        num_points = round(len(tracedata) / 2)
        tracedata2 = np.reshape(tracedata, (num_points, 2))

        sdata = [np.complex(c[0], c[1]) for c in tracedata2]

        return sdata
