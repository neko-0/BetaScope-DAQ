import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)

import pyvisa as visa
import numpy as np
import time
import functools
import logging
from .LecroyTRCReader import trcReader
from ..base import Scope

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LecroyScope(Scope):
    """
    Class for Lecroy Wavepro 725zi Oscilloscope
    """

    active_channels = []

    def __init__(self, ip_address):
        """
        initial a scope object with ethernet connection.
        """
        self._model = "LECROY"
        self.ip_addr = ip_address
        self.board = 0

    # ***************************************************************************
    # Private

    # ===========================================================================
    def set_read_byte(self, value):
        self.inst.read_raw = functools.partial(self.inst.read_raw, value)

    # ===========================================================================
    def _Set_Screen_Display(self, channel, switch):
        self.inst.write(f"C{channel}:TRA {switch}")

    def reopen_resource(self):
        self.inst.close()
        self.inst = self.rm.open_resource(f"TCPIP0::{self.ip_addr}::inst0::INSTR")
        self.inst.clear()
        self.set_read_byte(2048)
        self.inst.write("Comm_ForMaT DEF9,WORD,BIN")
        self.inst.write("*IDN?;")
        idn = self.inst.read()
        logger.info(f"Re-opened: {idn}")

    # ===========================================================================
    def _Set_Internal_Display(self, channel, switch):
        self.inst.write(f"C{channel}:DISP {switch}")

    # ===========================================================================
    def _Set_Trigger_Mode(self, channel, mode):
        mode_list = ["AUTO", "NORM", "SINGLE", "STOP"]
        if mode in mode_list:
            self.inst.write(f"TRig_MoDe {mode};WAIT;")
            self.inst.write(f"TRSE EDGE,SR,C{channel},HT,OFF;WAIT;")
        else:
            self.inst.write(f"TRig_MoDe {mode_list[0]};WAIT;")

    # ===========================================================================
    def _Set_Trigger_Slope(self, channel, slope):
        slope_list = ["POS", "NEG", "WINDOW"]
        if slope in slope_list:
            self.inst.write(f"C{channel}:TRig_SLope {slope};")
        else:
            # take default [0] if slope is not one of the mode in trig_slope
            self.inst.write(f"C{channel}:TRig_SLope {slope_list[0]};")

    # ===========================================================================
    def _Set_Trigger_Level(self, channel, threshold):
        self.inst.write(f"C{channel}:TRig_LeVel {threshold}V;")

    # ***************************************************************************
    # Public

    # ***************************************************************************
    def initialize(self, *args, **kwargs):
        """
        This method initiate the scope setup.
        """
        logger.info("Using ethernet connection: "),
        self.rm = visa.ResourceManager("@py")
        self.inst = self.rm.open_resource(
            f"TCPIP{self.board}::{self.ip_addr}::inst0::INSTR"
        )
        self.inst.clear()
        # self.inst.read_termination = '\r\n'
        self.inst.write_termination = "\r\n"
        self.inst.write("*IDN?;")
        idn = self.inst.read()
        while True or self.board > 100:
            if "LECROY" in idn:
                logger.info("connection established.")
                time.sleep(0.01)
                break
            logger.warning("retry connection.")
            self.board += 1
            logger.info(f"\n retrying board {self.board}.")
            self.inst = visa.ResourceManager("@py").open_resource(
                f"TCPIP{self.board}::{self.ip_addr}::inst0::INSTR"
            )
            self.inst.write("*IDN?;")
            idn = self.inst.read()

        self.inst.timeout = 100000
        self.inst.write("Comm_ForMaT DEF9,WORD,BIN")
        # self.inst.write("SEQ ON, 5, 40e+12")

    # ***************************************************************************
    def connect(self, *args, **kwargs):
        """
        This method initiate the connection to the scope.
        """
        pass

    # ***************************************************************************
    def close(self):
        self.inst.close()

    # ***************************************************************************
    def query(self, *args, **kwargs):
        return self.inst.query(*args, **kwargs)

    # ***************************************************************************
    def read(self):
        return self.inst.read()

    # ***************************************************************************
    def write(self, *args, **kwargs):
        return self.inst.write(*args, **kwargs)

    # ***************************************************************************
    def reset(self, *args, **kwargs):
        self.reopen_resource()

    # ===========================================================================
    def Set_Channel_Display(self, channel, switch):
        self._Set_Internal_Display(channel, switch)
        self._Set_Screen_Display(channel, switch)

    # ===========================================================================
    def arm_trigger(self, channel_number, slope, threshold, sweep_mode="NORM"):
        """"""
        self._Set_Trigger_Mode(channel_number, sweep_mode)
        self._Set_Trigger_Slope(channel_number, slope)
        self._Set_Trigger_Level(channel_number, threshold)

    # ===========================================================================
    def set_trigger(self, channel, threshold, polarity, mode):
        self.arm_trigger(channel, polarity, threshold, mode)

    # ===========================================================================
    def create_dir(self, dirc):  # dont use it, it is garbage.
        self.inst.write(
            f"DIR DISK,HDD,ACTION,CREATE,C:\\Users\\LeCroyUser\\Desktop\\{dirc}"
        )
        self.inst.write(
            f"DIR DISK,HDD,ACTION,SWITCH,C:\\Users\\LeCroyUser\\Desktop\\{dirc}"
        )

    def local_store_setup(self, on_off="OFF"):
        self.inst.write(f"STST ALL_DISPLAYED,HDD,AUTO,{on_off},FORMAT,BINARY")

    def save_waveform_local(self):
        self.inst.write("STO ALL_DISPLAYED,FILE")

    # ===========================================================================
    def _Get_Wavefrom_ASCII(self, channel):
        looper = 0
        voltage = self.inst.query(f"C{channel}:INSPECT? SIMPLE;")
        voltage = voltage.split()
        voltage = voltage[2 : len(voltage) - 2]
        while voltage == []:
            looper += 1
            logger.warning(f"Empty V, retrying {looper}")
            voltage = self.inst.query(f"C{channel}:INSPECT? SIMPLE;")
            # if voltage == []:
            # print "Empty Event"
            # return [[0],[0]]
            voltage = voltage.split()
            voltage = voltage[2 : len(voltage) - 2]

        t_offset = self.inst.query(f"C{channel}:INSPECT? HORIZ_OFFSET;")
        t_offset = t_offset.split()
        while t_offset == "" or t_offset == []:
            looper += 1
            logger.warning(f"Empty offset, retrying {looper}")
            # print t_offset
            t_offset = self.inst.query(f"C{channel}:INSPECT? HORIZ_OFFSET;")
            t_offset = t_offset.split()
            # if t_offset == "":
            # print "Empty Event"
            # return [[0],[0]]
        t_offset = float(t_offset[3])
        t_bin = self.inst.query(f"C{channel}:INSPECT? HORIZ_INTERVAL;")
        t_bin = t_bin.split()
        while t_bin == "" or t_bin == []:
            looper += 1
            logger.warning(f"Empty bin, retrying {looper}")
            # print t_offset
            t_bin = self.inst.query(f"C{channel}:INSPECT? HORIZ_INTERVAL;")
            t_bin = t_bin.split()
            # if t_bin == "":
            #    print "Empty Event"
            #    return [[0],[0]]
        t_bin = float(t_bin[3])
        # print t_bin
        time = []
        for i in range(len(voltage)):
            time.append(t_offset + i * t_bin)
        # print "Good Event"
        return [time, voltage]

    # ===========================================================================
    def _Get_Waveform_ASCII_All(self, channel_list):
        """
        Get waveform using ascii format. Loop through list of channels.
        depreciated method. see _Get_Waveform_Binary_All
        """
        looper = 0

        waveform_query_string = "WAIT;"
        toffset_query_string = "WAIT;"
        tbin_query_string = "WAIT;"
        for channel in channel_list:
            waveform_query_string += f"C{channel}:INSPECT? SIMPLE;"
            toffset_query_string += f"C{channel}:INSPECT? HORIZ_OFFSET;"
            tbin_query_string += f"C{channel}:INSPECT? HORIZ_INTERVAL;"

        voltage_list = []
        # t1 = time.time()
        voltage = self.inst.query(waveform_query_string)
        # t2 = time.time()
        # print("Query Time: {}".format(t2-t1))
        voltage = voltage.split()
        while voltage == []:
            looper += 1
            logger.warning(f"Empty V, retrying {looper}")
            voltage = self.inst.query(waveform_query_string)
            voltage = voltage.split()

        voltage_size_num_ch_ratio = len(voltage) / len(channel_list)
        for i in range(len(channel_list)):
            # print("voltage = {}".format(len(voltage)))
            voltage_temp = voltage[2 : voltage_size_num_ch_ratio - 1]
            voltage = voltage[voltage_size_num_ch_ratio:]
            voltage_list.append(voltage_temp)
            # print("voltage_temp = {}".format(len(voltage_temp)))
            # print(voltage_temp)

        t_offset_list = []
        # t1 = time.time()
        t_offset = self.inst.query(toffset_query_string)
        # t2 = time.time()
        # print("Query t offset {}".format(t2-t1))
        t_offset = t_offset.split()
        while t_offset == "" or t_offset == []:
            looper += 1
            logger.warning(f"Empty offset, retrying {looper}")
            t_offset = self.inst.query(toffset_query_string)
            t_offset = t_offset.split()

        for i in range(len(channel_list)):
            t_offset_list.append(float(t_offset[3]))
            t_offset = t_offset[4:]

        t_bin_list = []
        t_bin = self.inst.query(tbin_query_string)
        t_bin = t_bin.split()
        while t_bin == "" or t_bin == []:
            looper += 1
            logger.warning(f"Empty bin, retrying {looper}")
            t_bin = self.inst.query(tbin_query_string)
            t_bin = t_bin.split()

        for i in range(len(channel_list)):
            t_bin_list.append(float(t_bin[3]))
            t_bin = t_bin[4:]
        # print t_bin

        time_list = []
        for ch in range(len(voltage_list)):
            time_v = []
            for i in range(len(voltage_list[ch])):
                time_v.append(t_offset_list[ch] + i * t_bin_list[ch])
            time_list.append(time_v)
            # print(len(time_v))

        # print "Good Event"
        return [time_list, voltage_list]

    # ===========================================================================
    def _Get_Waveform_Binary(self, channel, raw=False, seq_mode=False):
        """
        Get waveform with binary format. Loop through list of channels.
        """

        voltage_list = []
        time_list = []
        raw_data = []
        segmentCount = ""
        waveCount = ""

        if isinstance(channel, list):
            for ch in channel:
                self.inst.write(f"C{ch}:WF?")
                binary_stream = self.inst.read_raw()
                if raw:
                    raw_data.append(binary_stream)
                    continue
                voltage_data = trcReader(binary_stream, "WAV_DATA", ch)
                horizontal_offset = trcReader(binary_stream, "HORIZ_OFFSET", ch)
                horizontal_inter = trcReader(binary_stream, "HORIZ_INTERVAL", ch)
                if seq_mode:
                    segmentCount = trcReader(
                        binary_stream, "NOM_SUBARRAY_COUNT", ch, seq_mode
                    )
                    waveCount = trcReader(
                        binary_stream, "WAVE_ARRAY_COUNT", ch, seq_mode
                    )
                # trigger_timestamp = []
                time_data = []
                for i in range(len(voltage_data)):
                    t = horizontal_offset + i * horizontal_inter
                    time_data.append(t)
                voltage_list.append(voltage_data)
                time_list.append(time_data)
            if raw:
                return raw_data
            else:
                if seq_mode:
                    return [time_list, voltage_list, segmentCount, waveCount]
                else:
                    return [time_list, voltage_list]
        elif isinstance(channel, int):
            channel_list = []
            channel_list.append(channel)
            return self._Get_Waveform_Binary(channel_list, raw)
        else:
            raise ValueError(
                "Non-supported channel input. Please feed in list of int of single int."
            )

    # ===========================================================================
    def get_waveform(self, channel, mode="binary", seq_mode=False):
        if "binary" in mode and "raw" in mode:
            try:
                return self._Get_Waveform_Binary(channel, raw=True)
            except ValueError as error:
                logger.warning(error)
        elif "binary" in mode:
            try:
                return np.array(self._Get_Waveform_Binary(channel, False, seq_mode))
            except ValueError as error:
                logger.warning(error)
        elif "ascii" in mode:
            if isinstance(channel, list):
                return self._Get_Wavefrom_ASCII_All(channel)
            else:
                return self._Get_Wavefrom_ASCII(channel)
        else:
            raise ValueError("Non-supported mode or channels")

    # ===========================================================================

    def wait_trigger(self, timeout=0.0, trigger_scan=None):
        # self.inst.write("ARM;")
        # self.inst.write("ARM;")#" WAIT;")
        # self.inst.write("ARM; WAIT;")
        # self.inst.write("ARM;")
        # self.inst.write("WAIT;")
        # self.inst.write("ARM;WAIT;") #this one??
        # self.inst.query("ARM;WAIT;")
        if trigger_scan is None:
            return self.inst.query("ARM;WAIT;*OPC?")
            # .format(str(timeout))) #or this oone??
        else:
            return self.inst.query(f"TRMD SINGLE;WAIT {timeout};FRTR;*OPC?")
        # self.inst.write("ARM;*OPC?")

    # ===========================================================================
    # ===========================================================================
    @classmethod
    def MakeScope(cls, ip_address):
        return cls(ip_address)

    # ===========================================================================
    # ===========================================================================
    def GetWaveform(self, channel_list, mode="binary", seq_mode=True):
        return self.Get_Waveform(channel_list, mode, seq_mode)

    # ===========================================================================
    # ===========================================================================
    def WaitForTrigger(self, timeout=0.0, trigger_scan=None):
        return self.Wait_For_Next_Trigger(timeout, trigger_scan)

    # ===========================================================================
    # ===========================================================================
    def enable_channel(self, ch, option):
        log.info("Setting channel {} {}".format(ch, option))
        self.Set_Channel_Display(ch, option)

    # ===========================================================================
    # ===========================================================================
    def InitSetup(self, *argv):
        log.info("Initialzing setup")
        # don't konw why read_raw() needs input. It wasn't like this before 2019/9/10
        self.set_read_byte(1048)
        self.Arm_trigger(*argv)

    # ===========================================================================
    # ===========================================================================
    def _test(self):
        self.inst.write("C2:TRig_LeVel 50V;")
        self.inst.write("C2:TRig_SLope NEG;TRIG:EDGE:SLOP %s")
