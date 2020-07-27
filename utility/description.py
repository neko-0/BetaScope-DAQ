"""
for generating description files
"""
from .Password import Password
from .file_dir import FileDir
import datetime


def CreateDescription(RunNumber):
    fileName = "Sr_Run_" + str(RunNumber) + "_Description.ini"
    fileExist = FileDir.check_file(fileName)
    date = datetime.datetime.now()
    user = Password.check_login()[0]
    if not fileExist:
        with open(fileName, "w") as f:
            f.write("[Run_Description] \n")
            f.write("#feel free to add anything that you think is needed \n")
            f.write("User = {username} \n".format(username=user))
            f.write("Date = %s \n" % str(date))
            f.write("Run_Number = \n")

            f.write("DUT_Manufacture = \n")
            f.write("DUT_Senor_Name = \n")
            f.write("DUT_UDI = \n")
            f.write("DUT_geometry = \n")
            f.write("DUT_Wafer_Number = \n")
            f.write("DUT_Wafer_Position = \n")
            f.write("DUT_Fluence_Type = \n")
            f.write("DUT_Fluence = \n")
            f.write("DUT_Readout_Board = \n")
            f.write("DUT_Readout_Board_Number = \n")

            f.write("Scope_Name = keysight \n")
            f.write("DUT_Scope_Channel = 2 \n")
            f.write("Trigger_Scope_Channel = 3 \n")

            f.write("Power_Supply_Name = CAEN \n")
            f.write("DUT_PS_Channel = 2 \n")
            f.write("Trigger_PS_Channel = 3 \n")

            f.write("Trigger_Sensor_Name = HPK2_S8664_chip15 \n")
            f.write("Trigger_Readout = \n")
            f.write("Trigger_Voltage = \n")

            f.write("Chamber_Name = Tenny\n")
            f.write("Temperature = \n")

            f.write("Purpose = \n")

            f.write("Addition_Notes = \n")
