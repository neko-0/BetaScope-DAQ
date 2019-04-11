from BetaDAQ import *
from general import *
import subprocess

editor = GetEditor("vim")

if __name__ == "__main__":
    print(" \n BetaScope DAQ is created \n")

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
