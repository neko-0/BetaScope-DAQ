from ..base import Scope
import pyvisa as visa
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
        self.nthread = 4
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

    def enable_channel(self, channel, status, comm=0):
        self.query(f":CHANnel{channel}:COMMonmode {comm};*OPC?")
        self.query(f":CHANnel{channel}:DISPlay {status};*OPC?")

    def get_waveform(self, channel, format="text", *args, **kwargs):
        methods = {"text": self.get_text_waveform}
        try:
            return methods[format](channel, *args, **kwargs)
        except KeyError as _error:
            raise KeyError(f"does not support {format=}.") from _error

    def initialize(self, ip_address, trigger_settings={}):
        if self.connect(ip_address):
            trigger_settings.setdefault("channel", 3)
            trigger_settings.setdefault("slope", "POS")
            trigger_settings.setdefault("threshold", 0.01)
            self.set_trigger(**trigger_settings)
            self.prepare_acquisition()
            if self.threadpool is None:
                self.threadpool = concurrent.futures.ThreadPoolExecutor(self.nthread)
            return True
        else:
            return False

    def reset(self):
        """
        NOT a true reset! just clearing
        """
        self.write("*CLS")

    def wait_trigger(self):
        self.instrument.clear()
        complete_status = self.query("*CLS;*OPC?")
        assert complete_status == "1"
        complete_status = self.query(":DIGitize;*OPC?")
        return complete_status

    def connect(self, ip_address, prefix="TCPIP0", suffix="inst0::INSTR"):
        self.ip_address = ip_address
        address = f"{prefix}::{self.ip_address}::{suffix}"
        self.instrument = self.resource_manager.open_resource(address, chunk_size=1024)
        self.instrument.clear()
        self.write("*CLS")
        self.write("*IDN?")
        idn = self.read()

        if "KEYSIGHT" in idn:
            log.info("Connected to Keysight Infinium Scope.")
        else:
            log.critical(f"Unable to connect with IP={self.ip_address}")
            return False

        self.instrument.timeout = self.timeout
        self.read_termination = "\n"
        self.write_termination = "\n"

        return True

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

    def set_trigger(
        self,
        channel=3,
        slope="POS",
        threshold=0.01,
        sweep_mode="TRIG",
        trig_type="EDGE",
    ):
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

            trig_type : str, default = "EDGE"
                trigger type

        Return
            no return
        """
        self.write(f":TRIG:EDGE:SOUR CHAN{channel}")
        self.write(f":TRIG:MODE {trig_type}")  # setting edge trigger type

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
        self.write("*CLS")
        self.write(":STOP")
        if self.nsegments == 1:
           self.write(":ACQ:MODE RTIMe") # Real time mode
        else:
           self.write(":ACQ:MODE SEGM")  # Segmentation mode
           self.write(f"ACQ:SEGM:COUN {self.nsegments}")
           self.write(":WAV:SEGM:ALL ON")
        self.write(":ACQ:BAND MAX")
        self.write(":ACQ:INT OFF")
        self.write(":ACQ:AVER OFF")
        self.write(":ACQ:POIN:AUTO ON")
        self.write(":ACQ:COMP 100")
        self.write(":WAV:FORM ASC")
        self.write(":WAV:STR ON")
        self.write("*SRE 7")
        self.write("*SRE 5")
        self.write("*SRE 0")
        self.write(":RUN")

        self.write(":SYST:GUI OFF")

        log.info(f"Number of segments = {self.nsegments}")

    def save_waveform_local(self, outFileName, i_event):
        """
        saving the waveform to the local disk C:\\Users\\Administrator\\Desktop\\. The format will be .bin
        :param fileName: output file name
        :param i_event: event index
        :return: None
        """
        out = f"{outFileName}{i_event,0:05d}"
        self.write(f":DISK:SAVE:WAV ALL,'{out}',BIN,ON")

    def raw_text_waveform(self, channel):
        """
        Get waveform in plain text format from a channel remotely
        """
        self.query(f":WAV:SOUR CHAN{channel};*OPC?")  # set channel source
        output = {}
        output["npts"] = int(self.query(":WAV:POIN?"))
        output["xorigin"] = self.query(":WAV:XOR?;*OPC?").split(";")[0]
        output["xincrement"] = self.query(":WAV:XINC?;*OPC?").split(";")[0]
        output["waveform"] = self.query(":WAV:DATA?").rstrip(",")
        if self.nsegments == 1:
           output["ttag"] = None
           output["relx"] = None
           output["absx"] = None
        else:
           output["ttag"] = self.query(":WAV:SEGM:XLIS? TTAG").rstrip(",")
           output["relx"] = self.query(":WAV:SEGM:XLIS? RELX").rstrip(",")
           output["absx"] = self.query(":WAV:SEGM:XLIS? ABSX").rstrip(",")
        self.query("*OPC?")
        return output

    def parse_text_waveform(self, data, reco_segment=True):
        """
        Generator that parsing the waveform from raw_text_waveform().
        return time and vertical/voltage traces.
        """
        if self.nsegments == 1:
            reco_segment = False

        if reco_segment:
            xorigin = list(map(float, data["absx"].split(",")))
            t_trace_start = xorigin[0]
        else:
            xorigin = float(data["xorigin"])
            t_trace_start = xorigin
        xincrement = float(data["xincrement"])
        npts = int(data["npts"])
        total_pts = npts * self.nsegments
        start_pt = 0
        log.debug(f"number of potns : {npts}")
        log.debug(f"total points (x n-segments) {total_pts}")

        # the data from 'get_ascii_waveform' is a string seperated by comma
        waveform = data["waveform"].split(",")
        waveform = np.asarray(list(map(float, waveform)))

        # the size of the waveform will be npts * nsegments
        assert len(waveform) == total_pts

        for i in range(self.nsegments):
            t_trace_end = t_trace_start + npts * xincrement + xincrement
            t_output = np.arange(t_trace_start, t_trace_end, xincrement)[:npts]
            v_output = waveform[start_pt : start_pt + npts]
            start_pt += npts
            if reco_segment and i + 1 < self.nsegments:
                t_trace_start = xorigin[i + 1]
            else:
                t_trace_start = t_trace_end
            yield t_output, v_output

    def get_text_waveform(self, channels):
        """
        get waveform in ascii format and send to remote PC

        Args:
            channles : list
                list of channels
        """

        if not isinstance(channels, list):
            raise ValueError(f"channles need to be list, received {type(channels)}")

        requsted_waveforms = {}
        output = {}
        # getting the first channel
        lookup = f"ch{channels[0]}"
        future_wav = self.threadpool.submit(self.raw_text_waveform, channels[0])
        requsted_waveforms[lookup] = future_wav
        for channel in channels[1:]:
            # get the previous one
            wav_result = requsted_waveforms.pop(lookup).result()
            # send the next request
            future = self.threadpool.submit(self.raw_text_waveform, channel)
            # start parting and update next lookup name
            wav = self.parse_text_waveform(wav_result)
            output[lookup] = list(wav)

            lookup = f"ch{channel}"
            requsted_waveforms[lookup] = future
        # final check
        if lookup in requsted_waveforms:
            wav_result = requsted_waveforms.pop(lookup).result()
            wav = self.parse_text_waveform(wav_result)
            output[lookup] = list(wav)

        return output


class KeysightScope:
    """
    class for constructing object with different interfaces.
    """

    _interface = {}
    _interface["TCPIP"] = KeysightScope_TCPIP()

    def __new__(cls, interface="TCPIP"):
        return KeysightScope._interface[interface]
