import pyvisa as visa
import time
from pyvisa import constants

class KeysightScope(object):
    '''
    Class for Keysight Infinium Scope
    '''

    active_channels = []

    def __init__(self, ip_address):
        '''
        initial a scope object with ethernet connection.
        '''
        if not ip_address:
            print("No ip address")
            return

        self.ip_address = ip_address
        self.ip_addr = ip_address
        self.rm = visa.ResourceManager("@py")
        self.inst = self.rm.open_resource("TCPIP0::" + ip_address + "::inst0::INSTR", chunk_size=100000000)
        #self.inst = self.rm.open_resource("USB0::10893::36935::MY57220130::0::INSTR")
        self.inst.read_termination = '\n'
        self.inst.write_termination = '\n'
        self.inst.clear()
        self.inst.write("*CLR")
        self.inst.write("*IDN?")
        idn = self.inst.read()

        #self.rm.visalib.set_buffer( self.inst.session, constants.VI_IO_IN_BUF, 20)
        #self.rm.visalib.set_buffer( self.inst.session, constants.VI_IO_OUT_BUF, 20)

        #self.inst.chunk_size = 2000 * 1024

        if "KEYSIGHT" in idn:
            print("\nConnected to Keysight Infinium Scope.\n")
            time.sleep(0.01)
        else:
            print("\nUnable to connect to Keysight Infinium Scope.\n")
            return

        self.inst.timeout = 3000

    def close(self):
        self.inst.close()

    def reopen_resource(self):
        print("reopen do nothing.")
        '''
        self.inst.close()
        self.inst = self.rm.open_resource("TCPIP0::" + self.ip_addr + "::inst0::INSTR")
        self.inst.clear()
        idn = self.inst.read()
        print("reponed: {}".format(idn))
        self.acquisition_setting()
        '''

    def arm_trigger(self, channel_number, slope, threshold, sweep_mode="TRIG"):
        '''
        setting the arm trigger. only using edge trigger at this moment
        :param channel_number: channel as trigger source
        :param slope: rising(POS) or falling(NEG) edge
        :param threshold: voltage level for the edge trigger. unit [V]
        :return: None
        '''
        self.inst.write(":TRIG:EDGE:SOUR CHAN{}".format(channel_number))
        self.inst.write(":TRIG:MODE EDGE")
        if slope=="POS":
            self.inst.write(":TRIG:EDGE:SLOPe POS")
        elif slope=="NEG":
            self.inst.write(":TRIG:EDGE:SLOPe NEG")
        self.inst.write(":TRIG:SWEep {}".format(sweep_mode))
        self.inst.write(":TRIG:LEVel CHAN{},{}".format(channel_number, threshold))

        print("\ntrigger is set. Here are the details:\n")
        print("Source : {}".format(self.inst.query(":TRIG:EDGE:SOUR?;*OPC?")))
        print("Mode : {}".format(self.inst.query(":TRIG:MODE?;*OPC?")))
        print("Edge : {}".format(self.inst.query(":TRIG:EDGE:SLOP?;*OPC?")))
        print("Sweep : {}".format(self.inst.query(":TRIG:SWE?;*OPC?")))
        trig_source = self.inst.query(":TRIG:EDGE:SOUR?;*OPC?").split(";")[0]

        threshold_setting = self.inst.query(":TRIG:LEV? {};*OPC?".format(trig_source))
        print("Threshold : {}".format(threshold_setting))

    def create_dir(self, dirc):
        '''
        create a local directory on the desktop for saving data
        :param dirc: name of the dirctory
        '''
        #self.inst.write(":DISK:CDIR '{}'".format("C:\\Users\\Administrator\\Desktop\\"))
        #err = self.inst.query(":SYST:ERR?;*OPC?")
        #print("CD? {}".format(err))
        self.inst.write(":DISK:MDIR '{}'".format(dirc+"\\"))
        self.inst.write(":DISK:CDIR '{}'".format(dirc+"\\"))

    def change_dir(self, dirc):
        '''
        change to the target directory
        :param dirc: target directory name
        '''
        self.inst.write(":DISK:CDIR '{}'".format("C:\\Users\\Administrator\\Desktop\\"))
        err = self.inst.query(":SYST:ERR?;*OPC?")
        print("CD ERR? {}".format(err))
        fix_path = "C:\\Users\\Administrator\\Desktop\\"
        self.inst.write(":DISK:CDIR '{}'".format(fix_path+dirc+"\\"))

    def acquisition_setting(self):
        '''
        hard coded acquisition setting before data taking
        '''
        self.inst.write(":*CLS")
        self.inst.write(":STOP")
        self.inst.write(":WAV:FORM ASCii")
        self.inst.write(":WAV:STR ON")
        self.inst.write(":ACQ:MODE RTIMe")#RTIMe
        self.inst.write(":ACQ:BAND MAX")
        self.inst.write(":ACQ:INT OFF")
        self.inst.write(":ACQ:AVER OFF")
        self.inst.write(":ACQ:POIN:AUTO ON")
        self.inst.write(":ACQ:COMP 100")
        self.inst.write(":WAV:SEGM:ALL ON")
        self.inst.write("*SRE 7")
        self.inst.write("*SRE 5")
        self.inst.write("*SRE 0")
        self.inst.write(":RUN")

        #self.inst.write(":SYST:GUI OFF")

    def waiting_for_next_wave(self):
        #self.inst.write("*TRG")
        #self.inst.write("*CLS")
        #self.inst.write(":SING")
        #self.inst.query(":DIG;*OPC?")
        '''
        ader = int(self.inst.query(":ADER?"))
        while(ader!=1):
            ader = int(self.inst.query(":ADER?"))
        return ader
        '''
        #self.inst.query("*CLR;*OPC?")
        #self.inst.write(":SING")
        #self.inst.clear()
        self.inst.write("*CLS")
        self.inst.write(":DIG")
        data  = self.inst.query("*OPC?")
        print("Wait {}".format(data))
        #self.inst.write(":STOP")
        return data
        #return self.inst.query("*OPC?")
        #self.inst.write(":DIG")
        #self.inst.write(":STOP")

    def save_waveform_local(self, outFileName, i_event):
        '''
        saving the waveform to the local disk C:\\Users\\Administrator\\Desktop\\. The format will be .bin
        :param fileName: output file name
        :param i_event: event index
        :return: None
        '''
        out = outFileName + "{0:05d}".format(i_event)
        self.inst.write(":DISK:SAVE:WAV ALL,'{}',BIN,ON".format(out))

    def get_ascii_waveform_remote(self, channelList):
        '''
        get waveform in ascii format and send to remote PC
        :param channel: waveform channel
        return [time_list, voltage_list]
        '''
        #self.inst.write(":WAV:FORM ASCii")
        #self.inst.write(":WAV:STR OFF")
        #self.inst.write("WMEM{}:SAVE CHAN{}".format(channel, channel) )
        #self.inst.query("*OPC?")
        if isinstance(channelList, list):
            output = []
            for channel in channelList:
                self.inst.write(":WAV:SOUR CHAN{}".format(channel))
                #self.inst.write(":WAV:SOUR WMEM{}".format(channel))
                d = self.inst.query("*OPC?").split(";")[0]
                print("WAV SOUR ch{} {}".format(channel, d))
                #self.inst.query(":DIG CHAN{};*OPC?".format(channel))
                #self.inst.write(":CHAN{}:DISP ON".format(channel))
                #v_data = self.inst.query(":WAV:DATA? 1,6000;*OPC?").split(";")[0]
                self.inst.write(":WAV:DATA?")
                print("sending opc")
                self.inst.write(";*OPC?")
                v_data = self.inst.read().split(";")[0]
                #self.inst.write(":WMEM{}:CLE".format(channel))
                #print(self.inst.query("*OPC?"))
                #print(":WAV:DATA? {}".format(v_data))
                v_data = [float(x) for x in v_data.split(",")[:-1]]
                t_data = []
                output.append( [v_data, t_data])

            xorigin = self.inst.query(":WAV:XOR?;*OPC?").split(";")[0]
            xincrement = self.inst.query(":WAV:XINC?;*OPC?").split(";")[0]
            for chan in output:
                for i in range(len(chan[0])):
                    chan[1].append(float(xorigin)+i*float(xincrement))
            return output
        else:
            self.get_ascii_waveform_remote([channelList])
