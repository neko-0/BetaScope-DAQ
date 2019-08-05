from DAQConfigReader import *
from DAQProducer import *
from Data_Path_Setup import *
from file_io.ROOTClass import *
from general.general import *
#import general
import socket
import gc
import datetime
import time
import subprocess
import shutil
import numpy as np
from tenney_chamber import f4t_controller
import multiprocessing as mp
from general.Color_Printing import ColorFormat
from utility.PI_TempSensor import PI_TempSensor

class BetaDAQ:
    def __init__(self, configFileName ):
        ColorFormat.printColor("Using Beta daq Class ", "c")
        self.configFile = DAQConfig()
        self.configFile.ReadDAQConfig( configFileName )

    def BetaMeas(self ):
        ColorFormat.printColor("Using Beta Measurement scripts", "y")
        MASTER_PATH = self.configFile.DAQMasterDir
        PARENT_DIR = self.configFile.DAQDataDir
        Setup_Data_Folder( self.configFile.DAQMasterDir, self.configFile.DAQDataDir, self.configFile.RunNumber )
        CURRENT_FILE = Setup_Imon_File( self.configFile.RunNumber )
        CURRENT_FILE = Check_Imon_File( CURRENT_FILE )

        current_file = open(CURRENT_FILE, "w")

        descriptionFile = raw_input("\n Create description file?[y/n]: ")
        if "y" in descriptionFile:
            editor = GetEditor("gedit")
            CreateDescription( self.configFile.RunNumber )
            subprocess.call([editor, "Sr_Run_" + str(self.configFile.RunNumber) + "_Description.ini"])
        else:
            pass
        shutil.copy("Sr_Run_" + str(self.configFile.RunNumber) + "_Description.ini",  "/media/mnt/BigHD/DAQlog/")

        tenney_chamber = self.configFile.tenney_chamber
        tenney_chamber_mode1 = self.configFile.tenney_chamber_mode1

        f4t = ""
        temperature_list = [0]
        trigger_voltage_list = [0]
        if tenney_chamber:
            f4t = f4t_controller.F4T_Controller()
            temperature_list = self.configFile.temperature_list
            trigger_voltage_list = self.configFile.trigger_voltage_list_from_chamber
        elif tenney_chamber_mode1[0]:
            f4t = f4t_controller.F4T_Controller()
        else:
            pass
        #if self.configFile.show_chamber_status:
            #proc = mp.Process(target=f4t.log_temp_humi_to_file())
            #proc.start()

        for tempIndex in range(len(temperature_list)):

            if tenney_chamber:
                self.configFile.TriggerVoltage = trigger_voltage_list[tempIndex]
                f4t.set_temperature( temperature_list[tempIndex] )
                f4t.check_temperature( temperature_list[tempIndex] )
                _current_time = time.time()
                #time_sender = progess_bar(2)
                while(time.time() <= self.configFile.tenney_chamber_wait_time):
                    duration = time.time()-_current_time
                    if duration%10==0:
                        #time_sender("Chamber is waiting: ", "% (/%)"%(duration, self.configFile.tenney_chamber_wait_time))
                        print(duration)
            elif tenney_chamber_mode1[0]:
                f4t.set_temperature( tenney_chamber_mode1[1] )
                f4t.check_temperature( tenney_chamber_mode1[1] )
            else:
                pass

            piSensor = PI_TempSensor()

            Scope = ScopeProducer( self.configFile )
            PowerSupply = PowerSupplyProducer( self.configFile )

            PowerSupply.SetVoltage(self.configFile.PSTriggerChannel, self.configFile.TriggerVoltage, 1.5 )
            if tenney_chamber:

                stepSize = 10
                numIncre = (self.configFile.dut_max_voltage_list_from_chamber[tempIndex]-self.configFile.dut_min_voltage_from_chamber)/stepSize
                self.configFile.VoltageList = []
                self.configFile.FileNameList = []
                for aa in range(numIncre):
                    newVolt = self.configFile.dut_max_voltage_list_from_chamber[tempIndex]-aa*stepSize
                    if newVolt > self.configFile.dut_min_voltage_from_chamber:
                        self.configFile.VoltageList.append(newVolt)
                        self.configFile.FileNameList.append( "Sr_Run%s_%sV_trig%sV"%(self.configFile.RunNumber, newVolt, self.configFile.TriggerVoltage )  )
                    else:
                        self.configFile.VoltageList.append(self.configFile.dut_min_voltage_from_chamber)
                        self.configFile.FileNameList.append( "Sr_Run%s_%sV_trig%sV"%(self.configFile.RunNumber, newVolt, self.configFile.TriggerVoltage)  )
                        break
                self.configFile.FileNameList.reverse()
                self.configFile.VoltageList.reverse()
                ColorFormat.printColor("DUT voltage is replaced with \n %s"%(self.configFile.VoltageList), "y")
                ColorFormat.printColor("file list is replaced with \n %s"%(self.configFile.FileNameList), "y")


            for i in range(len(self.configFile.FileNameList)):
                failSetVoltage = PowerSupply.SetVoltage( self.configFile.PSDUTChannel, self.configFile.VoltageList[i], self.configFile.dut_max_current_list_from_chamber[tempIndex] )
                if failSetVoltage == 1: continue
                V_Check = PowerSupply.ConfirmVoltage( self.configFile.PSDUTChannel, self.configFile.VoltageList[i] )
                if V_Check:
                    dataFileName = self.configFile.FileNameList[i]+".root"
                    if tenney_chamber:
                        dataFileName = dataFileName.split(".root")[0]+"_temp%s.root"%(temperature_list[tempIndex])
                    elif tenney_chamber_mode1[0]:
                        dataFileName = dataFileName.split(".root")[0]+"_temp%s.root"%(tenney_chamber_mode1[1])
                    else:
                        pass
                    outROOTFile = ROOTFileOutput(dataFileName, self.configFile.EnableChannelList )

                    if tenney_chamber or tenney_chamber_mode1[0]:
                        outROOTFile.create_branch("temperature", "D")
                        outROOTFile.create_branch("humidity", "D")

                    outROOTFile.create_branch("pi_temperature", "D")
                    outROOTFile.create_branch("pi_humidity", "D")

                    for chNum in self.configFile.EnableChannelList:
                        outROOTFile.create_branch("verScale%s"%chNum, "D" )
                        outROOTFile.create_branch("horScale%s"%chNum, "D" )
                        verScale = float(Scope._query("C%s:VDIV?"%chNum).split("VDIV ")[1].split(" ")[0])
                        horScale = float(Scope._query("TDIV?").split("TDIV ")[1].split(" ")[0])
                        print("Ver scale ch%s: %s"%(chNum,verScale))
                        print("Hor scale ch%s: %s"%(chNum,horScale))
                        outROOTFile.additional_branch["verScale%s"%chNum][0] = verScale
                        outROOTFile.additional_branch["horScale%s"%chNum][0] = horScale

                    outROOTFile.create_branch("bias", "D")
                    outROOTFile.additional_branch["bias"][0] = self.configFile.VoltageList[i]

                    outROOTFile.create_branch("ievent", "I")
                    print("Ready for data taking")

                    import pyvisa as visa
                    rm = visa.ResourceManager("@py")
                    xid = rm.visalib.sessions[Scope.Scope.inst.session].interface.lastxid

                    current_100cycle = 0.0
                    start_time = time.time()
                    event = 0
                    fail_counter = 0
                    while event < self.configFile.NumEvent:
                        try:
                            event += 1
                            outROOTFile.additional_branch["ievent"][0] = event

                            if tenney_chamber or tenney_chamber_mode1[0] :
                                outROOTFile.additional_branch["temperature"][0] = f4t.get_temperature()
                                outROOTFile.additional_branch["humidity"][0] = f4t.get_humidity()

                            piData = piSensor.getData()
                            outROOTFile.additional_branch["pi_temperature"][0] = piData["temperature"]
                            outROOTFile.additional_branch["pi_humidity"][0] = piData["humidity"]

                            Scope.WaitForTrigger()
                            #print("pass wait")
                            outROOTFile.i_timestamp[0] = time.time()
                            if event==0 or event%100==0:
                                current_100cycle = PowerSupply.CurrentReader( self.configFile.PSDUTChannel )
                            outROOTFile.i_current[0] = current_100cycle
                            waveData = ""
                            try:
                                waveData = Scope.GetWaveform( self.configFile.EnableChannelList )
                            except:
                                event -= 1
                                fail_counter += 1
                                print("fail getting data. {}".format(fail_counter))
                                if fail_counter == 1000:
                                    break
                                else:
                                    continue

                            if len(waveData) == 0:
                                event -= 1
                                print("empyt waveData...Please report this issue")
                                continue
                            elif len(waveData[0]) != len(self.configFile.EnableChannelList ):
                                event -= 1
                                print("waveData and channel mismatch, Please report this issue")
                                continue
                            else:
                                pass

                            for ch in range(len(self.configFile.EnableChannelList)):
                                for j in range( len(waveData[0][ch]) ):
                                    outROOTFile.w[ch].push_back( float(waveData[1][ch][j]) )
                                    outROOTFile.t[ch].push_back( waveData[0][ch][j] )
                            outROOTFile.Fill()
                            waveData = []
                            waveData = ""
                            gc.collect()
                            if(event%100==0):
                                date = datetime.datetime.now()
                                print("[{}] Saved event on local disk : {}".format(str(date), event))
                        except socket.error, e:
                            ColorFormat.printColor("Catch exception: {daq_error}, This might be that you are resizing the terminal".format(daq_error=e), "y")
                            ColorFormat.printColor("Continue data taking.", "y")
                        except Exception as E:
                            ColorFormat.printColor("Catch unknown exception: {daq_error}, This might be that you are resizing the terminal".format(daq_error=E), "y")
                            ColorFormat.printColor("Continue data taking.", "y")

                            print(rm.visalib.sessions[Scope.Scope.inst.session].interface.lastxid)
                            rm.visalib.sessions[Scope.Scope.inst.session].interface.lastxid -= 2
                            #rm.visalib.sessions[PowerSupply.PowerSupply.inst.session].interface.lastxid -= 1
                            print(rm.visalib.sessions[Scope.Scope.inst.session].interface.lastxid)
                            #raw_input()


                    outROOTFile.Close()
                    currentAfter = PowerSupply.CurrentReader( self.configFile.PSDUTChannel )
                    current_file.write("{}:{}:{}\n".format(self.configFile.VoltageList[i], "After", currentAfter))
                    end_time = time.time()
                    print("Rate = {}/s".format(self.configFile.NumEvent/(end_time-start_time)))
                else:
                    print("Voltage dose not matche!")

            PowerSupply.Close()
        current_file.close()
        if tenney_chamber:
            f4t.set_temperature(0)

    def ThreshodVsPeriod(self):
        print("Using Threshold vs Period Scan scripts")
        progress = general.progress(1)
        Scope = ScopeProducer( self.configFile )
        PowerSupply = PowerSupplyProducer( self.configFile )
        MASTER_PATH = self.configFile.DAQMasterDir
        PARENT_DIR = self.configFile.DAQDataDir
        Setup_Data_Folder( self.configFile.DAQMasterDir, self.configFile.DAQDataDir, self.configFile.RunNumber )

        for i in range(len(self.configFile.ThresholdScan_VoltageList)):
            PowerSupply.SetVoltage( self.configFile.ThresholdScan_PSChannel, self.configFile.ThresholdScan_VoltageList[i] )
            V_Check = PowerSupply.ConfirmVoltage( self.configFile.ThresholdScan_PSChannel, self.configFile.ThresholdScan_VoltageList[i] )
            if V_Check:
                outFileName = self.configFile.ThresholdScan_FileNameList[i] + ".text"
                outFile = open(outFileName, "w")
                outFile.write("Threshold[V],Period[s],STD,NumEvent\n")
                print("Ready...")

                ini_threshold = self.configFile.ThresholdScan_StartValue
                while ini_threshold <= self.configFile.ThresholdScan_EndValue:
                    if ini_threshold < 0:
                        Scope.SetTrigger( self.configFile.ThresholdScan_ScopeChannel, ini_threshold, "NEG", "STOP")
                        Scope.Scope.inst.write("BUZZ ON;")
                        sleep(2)
                    else:
                        Scope.SetTrigger( self.configFile.ThresholdScan_ScopeChannel, ini_threshold, "POS", "STOP")
                        Scope.Scope.inst.write("BUZZ ON;")
                        sleep(2)
                    count = 1
                    t_0 = time.time()
                    startT = t_0
                    triggerCounter = []
                    endT = ""
                    timeout = self.configFile.ThresholdScan_Timeout
                    while count <= self.configFile.ThresholdScan_MaxEvent:
                        next = Scope.WaitForTrigger( timeout, "Th Scan")
                        deltaT = time.time()-t_0
                        if deltaT >= timeout-0.1:
                            endT = time.time()
                            break
                        if time.time()-startT > self.configFile.ThresholdScan_MaxTime:
                            print("\nExceed data taking max time {}".format(startT))
                            endT = time.time()
                            break
                        if "1" in next:
                            t_0 = time.time()
                            waveform_data = Scope.GetWaveform(int(self.configFile.ThresholdScan_ScopeChannel), "binary raw")
                            trigger_Tdiff = trcReader(waveform_data[0], "Trigger_Tdiff", self.configFile.ThresholdScan_ScopeChannel, "sequence_mode")
                            for k in range(len(trigger_Tdiff)-1):
                                triggerCounter.append( trigger_Tdiff[i+1][0]-trigger_Tdiff[i][0] )
                            count+=1
                        else:
                            pass
                        if count%100==0:
                            tmp = np.array(triggerCounter)
                            avg = np.mean(tmp)
                            progress("Period Mean: {}   Finisehd".format(avg), count, self.configFile.ThresholdScan_MaxEvent )
                    triggerCounter = np.array(triggerCounter)
                    period = ""
                    if count > self.configFile.ThresholdScan_MaxEvent:
                        period = np.mean(triggerCounter)
                        std = np.std(triggerCounter)
                    else:
                        period = np.mean(triggerCounter)
                        std = np.std(triggerCounter)
                    outFile.write("{},{},{},{}\n".format(ini_threshold,period,std,len(triggerCounter)))
                    print("Results: {},{},{},{}\n".format(ini_threshold,period,std,len(triggerCounter)))
                    outFile.flush()
                    ini_threshold += self.configFile.ThresholdScan_Step
                    print("Next threshold : {}".format(ini_threshold))
                outFile.close()
                print("Moving to next voltage...")
        PowerSupply.Close()
        print("Finished!")
