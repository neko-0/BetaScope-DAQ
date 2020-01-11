from pathlib import Path
import os


class FileDir(object):
    def __init__(self):
        pass

    @staticmethod
    def setup_data_folder(master_dir, sub_dir, runNum):
        """
        Setup folders for dumping data

        param master_dir := top level directory
        param sub_dir := sub-directory within the master_dir
        param runNum := run number

        return none
        """
        sub_dir = "Sr_Run" + str(runNum) + "_" + sub_dir + "/"

        if Path(master_dir).exists():
            os.chdir(master_dir)
        else:
            os.mkdir(master_dir)
            os.chdir(master_dir)

        check_Dir = Path("./" + sub_dir)
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

    # ===============================================================================
    @staticmethod
    def setup_current_mon_file(runNum):
        """
        Setup the current monitoring file name

        param runNum := run number

        return current_file := updated current monitoring file
        """
        return "Sr_Run" + str(runNum) + "_current.txt"

    # ===============================================================================
    @staticmethod
    def check_current_mon_file(current_file):
        """
        Check to see if there is existing current monitoring file, if yes, update the index/number

        param current_file := name of the current monitoring file

        return current_file := updated current file name, str type
        """
        fcount = 2
        while True:
            myfile = Path("./" + current_file)
            if not myfile.exists():
                return current_file
            else:
                current_file = current_file.split(".")[0] + ".txt.{}".format(fcount)
                fcount += 1

    @staticmethod
    def check_file(currentFile):
        myfile = Path("./" + currentFile)
        if not myfile.exists():
            return False
        else:
            return True
