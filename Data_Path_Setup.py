from pathlib import Path
import os
import datetime

#===============================================================================
def Setup_Data_Folder(master_dir, sub_dir, runNum ):
        '''
        Setup folders for dumping data

        param master_dir := top level directory
        param sub_dir := sub-directory within the master_dir
        param runNum := run number

        return none
        '''
        sub_dir = "Sr_Run" + str(runNum) + "_" + sub_dir + "/"

        if Path(master_dir).exists():
            os.chdir(master_dir)
        else:
            os.mkdir(master_dir)
            os.chdir(master_dir)

        check_Dir = Path("./"+sub_dir)
        if check_Dir.exists():
            os.chdir(str(check_Dir))
        else:
            os.mkdir(sub_dir)
            os.chdir(sub_dir)

        check_fromDAQ = Path("./fromDAQ")
        if check_fromDAQ.exists():
            os.chdir("fromDAQ")
        else:
            os.mkdir("fromDAQ")
            os.chdir("fromDAQ")

#===============================================================================
def Setup_Imon_File( runNum ):
    '''
    Setup the current monitoring file name

    param runNum := run number

    return current_file := updated current monitoring file
    '''
    return "Sr_Run" + str(runNum) + "_current.txt"


#===============================================================================
def Check_Imon_File( current_file ):
    '''
    Check to see if there is existing current monitoring file, if yes, update the index/number

    param current_file := name of the current monitoring file

    return current_file := updated current file name, str type
    '''
    fcount = 2
    while True:
        myfile = Path("./"+current_file)
        if not myfile.exists():
            return current_file
        else:
            current_file = current_file.split(".")[0] + ".txt.{}".format(fcount)
            fcount += 1

def Check_File( currentFile ):
    myfile = Path("./"+currentFile)
    if not myfile.exists():
        return False
    else:
        return True

def generate_user(username):
    from hashlib import sha256
    import getpass
    with open("{user}_daqPW.dat".format(user=username), "wb") as f:
        pw = getpass.getpass("Please enter your password: \n")
        encrypted_pw = sha256(pw.rstrip()).hexdigest()
        f.write(encrypted_pw)


def CreateDescription( RunNumber ):
    fileName = "Sr_Run_" + str(RunNumber) + "_Description.ini"
    fileExist = Check_File(fileName)
    date = datetime.datetime.now()
    user = ""
    from hashlib import sha256
    import getpass
    import os
    while user=="":
        user = str(raw_input("USER NAME:"))
        user_pw_file = "/home/yuzhan/DAQForProduction/user_data/{username}_daqPW.dat".format(username=user)
        if os.path.exists(user_pw_file):
            with open(user_pw_file, "rb") as f:
                pw = getpass.getpass("Please enter your password: \n")
                decode_pw = sha256(pw.rstrip()).hexdigest()
                stored_pw = f.read()
                if decode_pw == stored_pw:
                    print("Okay")
                else:
                    print("error re-try")
                    user = ""
        else:
            pass
    if not fileExist:
        with open(fileName, "w") as f:
            f.write("[Run_Description] \n")
            f.write("#feel free to add anything that you think is needed \n")
            f.write("User = {username} \n".format(username=user) )
            f.write("Date = %s \n"%str(date) )
            f.write("DUT_Senor_Name = \n")
            f.write("Trigger_Sensor_Name = \n")
            f.write("DUT_Readout_B = \n")
            f.write("Trigger_Reader_B = \n")
            f.write("Trigger_Voltage = \n")
            f.write("Temperature = \n")
            f.write("Fluence = \n")
            f.write("DUT_Scope_Channel = 2 \n")
            f.write("Trigger_Scope_Channel = 3 \n")
            f.write("DUT_PS_Channel = 2 \n")
            f.write("Trigger_PS_Channel = 3 \n")
            f.write("Purpose = \n")
            f.write("Addition_Notes = with tenny chamber;\n")
