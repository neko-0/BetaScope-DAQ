import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)


import pyvisa as visa
import time

from ..core import Scope


class KeysightScope(Scope):
    """
    Class for Keysight Infinium Scope
    """

    active_channels = []

    def __init__(self, ip_address):
        """
        initial a scope object with ethernet connection.
        """
        if not ip_address:
            log.critical("No ip address")
            return

        self.ip_address = ip_address
        self.ip_addr = ip_address
        self.rm = visa.ResourceManager("")
        self.inst = self.rm.open_resource(
            "TCPIP0::" + ip_address + "::inst0::INSTR",
            read_termination="\n",
            write_termination="\n",
            chunk_size=1024,
        )
        # self.inst = self.rm.open_resource("USB0::10893::36935::MY57220130::0::INSTR")
        # self.inst.read_termination = '"\n"'
        # self.inst.write_termination = '\n'
        self.inst.clear()
        self.inst.write("*CLR")
        self.inst.write("*IDN?")
        idn = self.inst.read()

        self.default_seg_count = 20

        # self.rm.visalib.set_buffer( self.inst.session, constants.VI_IO_IN_BUF, 20)
        # self.rm.visalib.set_buffer( self.inst.session, constants.VI_IO_OUT_BUF, 20)

        # self.inst.chunk_size = 2000 * 1024

        if "KEYSIGHT" in idn:
            log.info("Connected to Keysight Infinium Scope.")
            time.sleep(0.01)
        else:
            log.critical("Unable to connect to Keysight Infinium Scope.")
            return

        self.inst.timeout = 100000

    def close(self):
        self.inst.close()

    def reopen_resource(self):
        log.info("{} reopen, do nothing.".format(self.__class__.__name__))
        """
        self.inst.close()
        self.inst = self.rm.open_resource("TCPIP0::" + self.ip_addr + "::inst0::INSTR")
        self.inst.clear()
        idn = self.inst.read()
        print("reponed: {}".format(idn))
        self.acquisition_setting()
        """

    def arm_trigger(self, channel_number, slope, threshold, sweep_mode="TRIG"):
        """
        setting the arm trigger. only using edge trigger at this moment
        :param channel_number: channel as trigger source
        :param slope: rising(POS) or falling(NEG) edge
        :param threshold: voltage level for the edge trigger. unit [V]
        :return: None
        """
        self.inst.write(":TRIG:EDGE:SOUR CHAN{}".format(channel_number))
        self.inst.write(":TRIG:MODE EDGE")
        if slope == "POS":
            self.inst.write(":TRIG:EDGE:SLOPe POS")
        elif slope == "NEG":
            self.inst.write(":TRIG:EDGE:SLOPe NEG")
        self.inst.write(":TRIG:SWEep {}".format(sweep_mode))
        self.inst.write(":TRIG:LEVel CHAN{},{}".format(channel_number, threshold))

        trig_source = self.inst.query(":TRIG:EDGE:SOUR?;*OPC?").split(";")[0]
        threshold_setting = self.inst.query(":TRIG:LEV? {};*OPC?".format(trig_source))

        log.info(
            "trigger is set. Here are the details: \n"
            + "Source : {}\n".format(self.inst.query(":TRIG:EDGE:SOUR?;*OPC?"))
            + "Mode : {}\n".format(self.inst.query(":TRIG:MODE?;*OPC?"))
            + "Edge : {}\n".format(self.inst.query(":TRIG:EDGE:SLOP?;*OPC?"))
            + "Sweep : {}\n".format(self.inst.query(":TRIG:SWE?;*OPC?"))
            + "Trig SRC : {}\n".format(trig_source)
            + "Threshold : {}\n".format(threshold_setting)
        )

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

    def acquisition_setting(self):
        """
        hard coded acquisition setting before data taking
        """
        self.inst.write(":*CLS")
        self.inst.write(":STOP")
        self.inst.write(":ACQ:MODE SEGM")  # RTIMe
        # self.inst.write(":ACQ:MODE RTIMe")#RTIMe
        self.inst.write("ACQ:SEGM:COUN {}".format(self.default_seg_count))
        self.inst.write(":ACQ:BAND MAX")
        self.inst.write(":ACQ:INT OFF")
        self.inst.write(":ACQ:AVER OFF")
        self.inst.write(":ACQ:POIN:AUTO ON")
        self.inst.write(":ACQ:COMP 100")
        self.inst.write(":WAV:FORM ASC")
        self.inst.write(":WAV:STR ON")
        self.inst.write(":WAV:SEGM:ALL ON")
        self.inst.write("*SRE 7")
        self.inst.write("*SRE 5")
        self.inst.write("*SRE 0")
        self.inst.write(":RUN")

        self.inst.write(":SYST:GUI OFF")

        self.seg_count = (
            self.default_seg_count
        )  # int(self.inst.query(":WAV:SEGM:COUN?"))
        log.info("seg count = {}".format(self.seg_count))

    def waiting_for_next_wave(self):
        # self.inst.write("*TRG")
        # self.inst.write("*CLS")
        # self.inst.write(":SING")
        # self.inst.query(":DIG;*OPC?")
        """
        ader = int(self.inst.query(":ADER?"))
        while(ader!=1):
            ader = int(self.inst.query(":ADER?"))
        return ader
        """
        # self.inst.query("*CLR;*OPC?")
        # self.inst.write(":SING")
        # self.inst.clear()
        # self.inst.write("*CLS")
        # self.inst.query("*OPC?")

        """
        self.inst.write(":WMEM1:CLE")
        self.inst.query("*OPC?")
        self.inst.write(":WMEM2:CLE")
        self.inst.query("*OPC?")
        self.inst.write(":WMEM3:CLE")
        self.inst.query("*OPC?")
        """

        # self.inst.write(":DIG")
        self.inst.clear()
        self.inst.query("*CLS;*OPC?")
        data = self.inst.query(":DIG;*OPC?")
        # self.inst.write(":STOP")
        """
        self.inst.write(":WMEM1:SAVE CHAN1")
        self.inst.query("*OPC?")
        self.inst.write(":WMEM2:SAVE CHAN2")
        self.inst.query("*OPC?")
        self.inst.write(":WMEM3:SAVE CHAN3")
        self.inst.query("*OPC?")
        """
        # print("Wait {}".format(data))
        # self.inst.write(":STOP")
        return data
        # return self.inst.query("*OPC?")
        # self.inst.write(":DIG")
        # self.inst.write(":STOP")

    def save_waveform_local(self, outFileName, i_event):
        """
        saving the waveform to the local disk C:\\Users\\Administrator\\Desktop\\. The format will be .bin
        :param fileName: output file name
        :param i_event: event index
        :return: None
        """
        out = outFileName + "{0:05d}".format(i_event)
        self.inst.write(":DISK:SAVE:WAV ALL,'{}',BIN,ON".format(out))

    def get_ascii_waveform_remote(self, channelList):
        """
        get waveform in ascii format and send to remote PC
        :param channel: waveform channel
        return [time_list, voltage_list]
        """
        # self.inst.write(":WAV:FORM ASCii")
        # self.inst.write(":WAV:STR OFF")
        # self.inst.write("WMEM{}:SAVE CHAN{}".format(channel, channel) )
        # self.inst.query("*OPC?")
        if isinstance(channelList, list):
            t_output = []
            v_output = []
            split_level = 1
            for channel in channelList:
                start_pt = 1
                read_pnt = 0
                self.inst.query(":WAV:SOUR CHAN{};*OPC?".format(channel))
                npts = int(self.inst.query(":WAV:POIN?")) / split_level
                read_pnt = npts
                v_data = []
                if self.seg_count < 1:
                    my_v_data = self.inst.query(
                        ":WAV:DATA? {},{};*OPC?".format(start_pt, read_pnt)
                    ).split(";")[0]
                    my_v_data = [float(x) for x in my_v_data.split(",")[:-1]]
                    v_data += my_v_data
                else:
                    for seg in range(self.seg_count * split_level):
                        for my_split in range(split_level):
                            if my_split != split_level - 2:
                                read_pnt = npts
                            else:
                                read_pnt = npts + 3
                            my_v_data = self.inst.query(
                                ":WAV:DATA? {},{};*OPC?".format(start_pt, read_pnt)
                            ).split(";")[0]
                            my_v_data = [float(x) for x in my_v_data.split(",")[:-1]]
                            v_data += my_v_data

                            if my_split != split_level - 2:
                                start_pt += npts
                            else:
                                start_pt = +npts + 3

                # print(":WAV:DATA? {} {}".format(channel, len(v_data)))
                t_data = []
                t_output.append(t_data)
                v_output.append(v_data)

            xorigin = self.inst.query(":WAV:XOR?;*OPC?".format(channel)).split(";")[0]
            xincrement = self.inst.query(":WAV:XINC?;*OPC?".format(channel)).split(";")[
                0
            ]
            # print self.inst.query(":WAV:XOR?;*OPC?".format(channel)), self.inst.query(":WAV:XINC?;*OPC?".format(channel)), xincrement
            last_t = float(xorigin)
            for ch, chan in enumerate(v_output):
                for i in range(len(chan)):
                    # t_output[ch].append(last_t+i*float(xincrement))
                    t_output[ch].append(last_t + float(xincrement))
                    last_t += float(xincrement)

            # print(len(output))
            return [t_output, v_output]
        else:
            return self.get_ascii_waveform_remote([channelList])

    # ===========================================================================
    # ===========================================================================
    @classmethod
    def MakeScope(cls, ip_address):
        return cls(ip_address)

    # ===========================================================================
    # ===========================================================================
    def InitSetup(self, *argv):
        log.info("Initialzing setup")
        self.arm_trigger(*argv)
        self.acquisition_setting()

    # ===========================================================================
    # ===========================================================================
    def GetWaveform(self, channel_list, mode="ascii", seq_mod=True):
        return self.get_ascii_waveform_remote(channel_list)

    # ===========================================================================
    # ===========================================================================
    def SetTrigger(self, channel, threshold, polarity, mode):
        self.arm_trigger(channel, polarity, threshold, mode)
        self.acquisition_setting()

    # ===========================================================================
    # ===========================================================================
    def WaitTrigger(self, timeout=0.0, trigger_scan=None):
        return self.waiting_for_next_wave()

    # ===========================================================================
    # ===========================================================================
    def Enable_Channel(self, ch, option):
        pass
