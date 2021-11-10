from ..base import Scope
import pyvisa as visa
import time
import numpy as np
import concurrent.futures
import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)


class KeysightScopeInterfaceBase(Scope):
    def __init__(self):
        self.resource_manager = None
        self.instrument = None
        self.active_channels = []
        self.nsegments = 20
        self.timeout = 100000

    @property
    def n_active_channels(self):
        return len(self.active_channels)


class KeysightScope_TCPIP(KeysightScopeInterfaceBase):
    """
    TCPIP for Keysight Infinium Scope
    """

    def __init__(self, *args, **kwargs):
        super(KeysightScope_TCPIP, self).__init__(*args, **kwargs)
        self.ip_address = None
        self.resource_manager = visa.ResourceManager()
        self._read_termination = None
        self._write_termination = None
        self.nthread = 8
        self.threadpool = None

    @property
    def read_termination(self):
        return self._read_termination

    @read_termination.setter
    def read_termination(self, input):
        self._read_termination = input
        self.instrument.read_termination = input

    @property
    def write_termination(self):
        return self._write_termination

    @write_termination.setter
    def write_termination(self, input):
        self._write_termination = input
        self.instrument.write_termination = input

    def query(self, content):
        return self.instrument.query(content)

    def write(self, content):
        self.instrument.write(content)

    def read(self):
        return self.instrument.read()

    def close(self):
        self.inst.close()

    def enable_channel(self):
        pass

    def get_waveform(self):
        pass

    def initialize(self, ip_address, trigger_settings):
        self.connect(ip_address, *args, **kwargs)
        self.prepare_acquisition()
        if self.threadpool is None:
            self.threadpool = concurrent.futures.ThreadPoolExecutor(self.nthread)

    def reset(self):
        pass

    def wait_trigger(self):
        pass

    def connect(self, ip_address, prefix="TCPIP0", suffix="inst0::INSTR"):
        self.ip_address = ip_address
        address = f"{prefix}::{self.ip_address}::{suffix}"
        self.instrument = self.resource_manager.open_resource(address)
        self.instrument.clear()
        self.write("*CLS")
        self.write("*IDN?")
        idn = self.read()

        if "KEYSIGHT" in idn:
            log.info("Connected to Keysight Infinium Scope.")
        else:
            log.critical(f"Unable to connect with IP={self.ip_address}")

        self.instrument.timeout = self.timeout
        self.read_termination = "\n"
        self.write_termination = "\n"

    def reopen_resource(self):
        log.info(f"{self.__class__.__name__} reopen, do nothing.")
        """
        self.inst.close()
        self.inst = self.rm.open_resource("TCPIP0::" + self.ip_addr + "::inst0::INSTR")
        self.inst.clear()
        idn = self.inst.read()
        print("reponed: {}".format(idn))
        self.acquisition_setting()
        """

    def set_trigger(self, channel, slope, threshold, sweep_mode="TRIG"):
        """
        Method for setting trigger arming.

        Args:
            channel : int
                channel for arming the trigger.

            slope : str
                polarity for arming. i.e 'POS' or 'NEG'

            threshold: float
                threshold of the trigger.

            sweep_mode: str, default = 'TRIG'
                sweeping mode.

        Return
            no return
        """
        self.write(f":TRIG:EDGE:SOUR CHAN{channel}")
        self.write(":TRIG:MODE EDGE")  # setting edge trigger type

        slope_types = ["POS", "NEG"]
        if slope not in slope_types:
            raise ValueError(f"invalid slope {slope}. Use one of {slope_types}.")
        self.write(f":TRIG:EDGE:SLOPe {slope}")

        self.write(f":TRIG:SWEep {sweep_mode}")
        self.write(f":TRIG:LEVel CHAN{channel},{threshold}")

        trig_source = self.query(":TRIG:EDGE:SOUR?;*OPC?").split(";")[0]
        threshold_setting = self.query(f":TRIG:LEV? {trig_source};*OPC?")

        scope_info = [
            "trigger is set. Here are the details:",
            f"Source: {self.query(':TRIG:EDGE:SOUR?;*OPC?')}",
            f"Mode : {self.query(':TRIG:MODE?;*OPC?')}",
            f"Edge : {self.query(':TRIG:EDGE:SLOP?;*OPC?')}",
            f"Sweep : {self.query(':TRIG:SWE?;*OPC?')}",
            f"Trig SRC : {trig_source}",
            f"Threshold : {threshold_setting}",
        ]
        log.info("\n".join(scope_info))

    def create_dir(self, dirc):
        """
        create a local directory on the desktop for saving data
        :param dirc: name of the dirctory
        """
        # self.inst.write(":DISK:CDIR '{}'".format("C:\\Users\\Administrator\\Desktop\\"))
        # err = self.inst.query(":SYST:ERR?;*OPC?")
        # print("CD? {}".format(err))
        self.inst.write(":DISK:MDIR '{}'".format(dirc + "\\"))
        self.inst.write(":DISK:CDIR '{}'".format(dirc + "\\"))

    def change_dir(self, dirc):
        """
        change to the target directory
        :param dirc: target directory name
        """
        self.inst.write(":DISK:CDIR '{}'".format("C:\\Users\\Administrator\\Desktop\\"))
        err = self.inst.query(":SYST:ERR?;*OPC?")
        log.info("CD ERR? {}".format(err))
        fix_path = "C:\\Users\\Administrator\\Desktop\\"
        self.inst.write(":DISK:CDIR '{}'".format(fix_path + dirc + "\\"))

    def prepare_acquisition(self):
        """
        hard coded acquisition setting before data taking
        """
        self.write(":*CLS")
        self.write(":STOP")
        self.write(":ACQ:MODE SEGM")  # Segmentation mode
        # self.write(":ACQ:MODE RTIMe") # Real time mode
        self.write(f"ACQ:SEGM:COUN {self.nsegments}")
        self.write(":ACQ:BAND MAX")
        self.write(":ACQ:INT OFF")
        self.write(":ACQ:AVER OFF")
        self.write(":ACQ:POIN:AUTO ON")
        self.write(":ACQ:COMP 100")
        self.write(":WAV:FORM ASC")
        self.write(":WAV:STR ON")
        self.write(":WAV:SEGM:ALL ON")
        self.write("*SRE 7")
        self.write("*SRE 5")
        self.write("*SRE 0")
        self.write(":RUN")

        self.write(":SYST:GUI OFF")

        log.info(f"Number of segments = {self.nsegments}")

    def waiting_for_next_wave(self):
        self.instrument.clear()
        self.query("*CLS;*OPC?")
        data = self.query(":DIG;*OPC?")

        return data

    def save_waveform_local(self, outFileName, i_event):
        """
        saving the waveform to the local disk C:\\Users\\Administrator\\Desktop\\. The format will be .bin
        :param fileName: output file name
        :param i_event: event index
        :return: None
        """
        out = f"{outFileName}{i_event,0:05d}"
        self.write(f":DISK:SAVE:WAV ALL,'{out}',BIN,ON")

    def raw_ascii_waveform(self, channel):
        """
        Get ascii waveform from a channel remotely
        """
        self.query(f":WAV:SOUR CHAN{channel};*OPC?") # set channel source
        output = {}
        output["npts"] = int(self.query(":WAV:POIN?"))
        output["xorigin"] = self.query(":WAV:XOR?;*OPC?").split(";")[0]
        output["xincrement"] = self.query(":WAV:XINC?;*OPC?").split(";")[0]
        output["waveform"] = self.query(":WAV:DATA?")
        return output

    def parse_ascii_waveform(self, data):
        xorigin = float(data["xorigin"])
        xincrement = float(data["xincrement"])
        npts = int(data["npts"])
        total_pts = npts * self.nsegments
        start_pt = 0
        log.debug(f"number of potns : {npts}")
        log.debug(f"total points (x n-segments) {total_pts}")

        # the data from 'get_ascii_waveform' is a string seperated by comma
        waveform = data["waveform"].split(",")
        waveform = np.asarray(list(map(float, waveform[:-1])))

        for i in range(self.nsegments):
            t_output = np.arange(xorigin, xorigin+npts*xincrement, xincrement)
            v_output = waveform[start_pt:start_pt+npts]
            start_pt += npts
            yield t_output, v_output

    def get_ascii_waveform_remote(self, channels):
        """
        get waveform in ascii format and send to remote PC

        Args:
            channles : list
                list of channels
        """

        if not isinstance(channels, list):
            raise ValueError(f"channles need to be list, received {type(channels)}")

        output = {}
        for channel in channels:
            output[f"ch{channel}"] = []
            raw_waveform = self.raw_ascii_waveform(channel)
            for wav in self.parse_ascii_waveform(raw_waveform):
                output[f"ch{channel}"].append(wav)

        return output

class KeysightScope:
    """
    class for constructing object with different interfaces.
    """

    _interface = {}
    _interface["TCPIP"] = KeysightScope_TCPIP()

    def __new__(cls, interface="TCPIP"):
        return KeysightScope._interface[interface]
