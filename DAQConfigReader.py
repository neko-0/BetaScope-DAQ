'''
DAQ Configuration reader class
'''

import configparser
import os
from general.Color_Printing import ColorFormat

class DAQConfig:
    def __init__(self):
        '''
        initializing DAQ configuration parameters
        '''

        self.ScopeName = ""

        self.VoltageList = []
        self.NumEvent = -1
        self.TriggerVoltage = ""
        self.RunNumber = ""
        self.DAQDataDir = ""

        self.FileNameList = []
        self.FileNameSuffix = ""

        self.ScopeIP = ""
        self.EnableChannelList = []
        self.TriggerChannel = ""
        self.DUTChannelList = ""
        self.TriggerSetting = []

        self.PSChannelList = []
        self.PSDUTChannel = ""
        self.PSTriggerChannel = ""
        self.PSSoftwareComplicance = ""

        self.DAQMasterDir = ""

        self.ThresholdScan_VoltageList = []
        self.ThresholdScan_FileList = []
        self.ThresholdScan_ScopeChannel = ""
        self.ThresholdScan_PSChannel = ""
        self.ThresholdScan_StartValue = ""
        self.ThresholdScan_EndValue = ""
        self.ThresholdScan_Step = "" #in volt
        self.ThresholdScan_Timeout = "" #in second
        self.ThresholdScan_MaxTime = ""
        self.ThresholdScan_MaxEvent = ""

        self.tenney_chamber = False
        self.temperature_list = []
        self.show_chammber_status = True
        self.dut_max_voltage_list_from_chamber = []
        self.dut_max_current_list_from_chamber = []

    def ReadDAQConfig(self, configFileName):
        configFile = configparser.ConfigParser()
        try:
            configFile.read( configFileName )
            print("DAQ configuration file is read")
        except:
            print("Cannot find DAQ configuration file. Exiting")
            os.exit()

        self.ScopeName = str(configFile["Oscilloscope"]["SCOPE_NAME"])

        self.VoltageList = [ int(x) for x in configFile["Voltage_Scan"]["VOLTAGE_LIST"].split(",") ]
        self.NumEvent = int(configFile["Voltage_Scan"]["nEvent"])
        self.TriggerVoltage = int(configFile["Trigger_Setting"]["TRIGGER_VOLTAGE"])
        self.RunNumber = str(configFile["File_Name"]["RUN_NUMBER"])
        self.FileNameSuffix = "trig%sV"%(self.TriggerVoltage)

        self.WAIT_TIME = int(configFile["Voltage_Scan"]["WAIT_TIME"])
        self.CYCLE = int(configFile["Voltage_Scan"]["CYCLE"])
        self.REVERSE_BIAS_SCAN = int(configFile["Voltage_Scan"]["REVERSE_BIAS_SCAN"])

        for volt in self.VoltageList:
            #self.FileNameList.append( str("Sr_Run"+str(self.RunNumber)+str(volt)+"V_"+self.FileNameSuffix ) )
            self.FileNameList.append( "Sr_Run%s_%sV_%s"%(self.RunNumber, volt, self.FileNameSuffix ) )
        ColorFormat.printColor("File name list is created:", "y")
        ColorFormat.printColor(self.FileNameList, "y")

        self.ScopeIP = str(configFile["Oscilloscope"]["SCOPE_IP_ADDRESS"])
        self.EnableChannelList = [ int(x) for x in configFile["Oscilloscope"]["ENABLE_CHANNEL"].split(",") ]
        self.DUTChannelList = [ int(x) for x in configFile["Oscilloscope"]["DUT_CHANNEL"].split(",") ]
        self.TriggerChannel = int(configFile["Oscilloscope"]["TRIGGER_CHANNEL"])
        self.TriggerSetting = [int(configFile["Oscilloscope"]["TRIGGER_SETTING_CH"]), str(configFile["Oscilloscope"]["TRIGGER_SETTING_EDGE"]), float(configFile["Oscilloscope"]["TRIGGER_SETTING_TH"]), str(configFile["Oscilloscope"]["TRIGGER_SETTING_MODE"])]
        self.PSChannelList =  [ int(x) for x in configFile["CAEN_PowerSupply"]["ENABLE_CHANNEL"].split(",") ]
        self.PSDUTChannel =  int(configFile["CAEN_PowerSupply"]["DUT_CHANNEL"])
        self.PSTriggerChannel = int(configFile["CAEN_PowerSupply"]["TRIGGER_CHANNEL"])
        self.PSSoftwareComplicance = float(configFile["CAEN_PowerSupply"]["SOFTWARE_COMPLIANCE"])

        self.DAQMasterDir = str(configFile["General_Settting"]["MASTER_PATH"])
        self.DAQDataDir = str(configFile["File_Name"]["PARENT_DIR"])

        self.ThresholdScan_VoltageList = [ int(x) for x in configFile["Edge_Threshold_Scan"]["VOLTAGE_LIST"].split(",") ]
        self.ThresholdScan_MaxEvent = int(configFile["Edge_Threshold_Scan"]["nEvent"])
        self.ThresholdScan_StartValue = float(configFile["Edge_Threshold_Scan"]["Threshold_start"])
        self.ThresholdScan_EndValue = float(configFile["Edge_Threshold_Scan"]["Threshold_end"])
        self.ThresholdScan_Step = float(configFile["Edge_Threshold_Scan"]["Threshold_step"])
        self.ThresholdScan_MaxTime = float(configFile["Edge_Threshold_Scan"]["MAX_TIME"])
        self.ThresholdScan_ScopeChannel = configFile["Edge_Threshold_Scan"]["Channel"]
        self.ThresholdScan_PSChannel = configFile["Edge_Threshold_Scan"]["Power_Channel"]
        self.ThresholdScan_Timeout = float(configFile["Edge_Threshold_Scan"]["Timeout"])
        self.ThresholdScan_FileNameList = []
        for volt in self.ThresholdScan_VoltageList:
            self.ThresholdScan_FileNameList.append( str("Sr_Run"+str(self.RunNumber)+"_"+str(volt)+"V_Ch"+str(self.ThresholdScan_ScopeChannel)))
        ColorFormat.printColor(self.ThresholdScan_FileNameList, "y")

        self.tenney_chamber = bool(configFile["Tenney_Chamber"]["USE_CHAMBER"]=="True")
        self.TEMP_RESET = bool(configFile["Tenney_Chamber"]["TEMP_RESET"]=="True")
        self.tenney_chamber_mode1 = [False, -273]
        if "set_to" in configFile["Tenney_Chamber"]["USE_CHAMBER"]:
            self.tenney_chamber_mode1 = [True, int(configFile["Tenney_Chamber"]["USE_CHAMBER"].split("set_to")[1]) ]
        self.show_chamber_status = bool(configFile["Tenney_Chamber"]["SHOW_STATUS"])
        self.tenney_chamber_wait_time = int(configFile["Tenney_Chamber"]["WAIT_TIME"])
        self.temperature_list = [ int(x) for x in configFile["Tenney_Chamber"]["TEMPERATURE_LIST"].split(",") ]
        self.trigger_voltage_list_from_chamber = [ int(x) for x in configFile["Tenney_Chamber"]["TRIGGER_VOLTAGE_LIST"].split(",") ]
        self.dut_max_voltage_list_from_chamber = [ int(x) for x in configFile["Tenney_Chamber"]["DUT_MAX_VOLTAGE_LIST"].split(",") ]
        self.dut_max_current_list_from_chamber = [ int(x) for x in configFile["Tenney_Chamber"]["DUT_MAX_CURRENT_LIST"].split(",") ]
        self.dut_min_voltage_from_chamber = int( configFile["Tenney_Chamber"]["DUT_MIM_VOLTAGE"] )
        if self.tenney_chamber:
            ColorFormat.printColor("list of temperature:", "y")
            ColorFormat.printColor(self.temperature_list, "c")
            ColorFormat.printColor("Trigger voltage will be replace by the following list of voltage at corresponding temperature:", "y")
            ColorFormat.printColor(self.trigger_voltage_list_from_chamber, "c")
            ColorFormat.printColor("DUT voltage will be set the these maximum voltage and ramp down to 50V with step 20V(Yes you CAN'T change the step size!):", "y")
            ColorFormat.printColor(self.dut_max_voltage_list_from_chamber, "c")
            ColorFormat.printColor("Maximum current list:", "y")
            ColorFormat.printColor(self.dut_max_current_list_from_chamber, "c")
