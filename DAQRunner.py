from BetaDAQ import *
from general.general import *
import subprocess
import os

editor = GetEditor("gedit")

if __name__ == "__main__":

    print(" \n BetaScope DAQ is created \n")

    daq_pid = os.getpid()
    with open("user_data/daq_pid.log", "w") as log:
        log.write("pid = {}".format(daq_pid) )

    mode = ["beta", "ts"]

    print("\n *** Open Configuration file *** \n")
    subprocess.call([editor, "BetaDAQ_Config.ini"])

    DAQ = BetaDAQ("BetaDAQ_Config.ini")

    runningMode = raw_input("\nWhich Measurement?[beta(Beta Measurement), ts(Threshold Scan)]: ")
    if "beta" in runningMode:
        DAQ.BetaMeas()
    elif "ts" in runningMode:
        DAQ.ThreshodVsPeriod()
    else:
        print("Invalid running Mode (please enter 'beta' or 'ts')")

    print("DAQ is closed")
