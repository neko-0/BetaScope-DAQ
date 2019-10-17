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
