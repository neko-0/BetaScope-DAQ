import os
import ROOT
from array import array
from general.Color_Printing import ColorFormat

class ROOTFileOutput():
    def __init__(self, fileName, branch_list, opt=None):
        #check to see if file exist
        same_file_counter = 1
        while True:
            if os.path.isfile(fileName):
                print("file already existed, incrementing file index to {counter}".format(counter=same_file_counter))
                same_file_counter +=1
                fileName = fileName.split(".root")[0] + ".root.{i}".format(i=same_file_counter)
                if os.path.isfile(fileName):
                    continue
                else:
                    break
            else:
                break

        #start creating output file
        self.tfile = ROOT.TFile( fileName, "RECREATE", "8")
        self.ttree = ROOT.TTree( "wfm", "recorded waveform(remote mode)")
        self.w = []
        self.t = []
        self.i_timestamp = array( "d", [0] )
        self.i_current = array( "d", [0] )
        self.threshold_level = array("d", [0])
        self.additional_branch = dict()
        if opt is None:
            pass
        elif "Threshold_scan" in opt:
            self.ttree.Branch( "threshold_level", self.threshold_level, "threshold_level/D" )
        else:
            pass
        self.ttree.Branch( "i_timestamp", self.i_timestamp, "i_timestamp/D" )
        self.ttree.Branch( "i_current", self.i_current, "i_current/D" )
        for i in range(len(branch_list)):
            self.w.append( ROOT.std.vector("double")() )
            self.t.append( ROOT.std.vector("double")() )
            self.ttree.Branch( "w{}".format(branch_list[i]), self.w[i] )
            self.ttree.Branch( "t{}".format(branch_list[i]), self.t[i] )

    def Fill(self):
        self.ttree.Fill()
        for b in self.w:
            b.clear()
        for b in self.t:
            b.clear()

    def create_branch(self, name, type):
        if type == "D":
            self.additional_branch[str(name)] = array("d", [0])
        elif type == "I":
            self.additional_branch[str(name)] = array("i", [0])
        else:
            ColorFormat.printColor(" >> Invalid data type for {branch}".format(branch=name), "g")
            ColorFormat.printColor(" >> Using default (type Double)", "g")

        self.ttree.Branch(str(name), self.additional_branch[name], "%s/%s"%(name, type) )
        ColorFormat.printColor(" >> additional branch (%s) is created"%name, "g")

    def Close(self):
        ColorFormat.printColor(" >> Writing file", "g")
        self.tfile.Write()
        self.tfile.Close()
        ColorFormat.printColor(" >> file is finished", "g")
