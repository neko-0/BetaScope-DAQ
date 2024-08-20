import logging, coloredlogs

logging.basicConfig()
logger = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=logger)

import os

try:
    import ROOT
except ImportError:
    logger.critical("Cannot import ROOT")
from array import array


class ROOTFileOutput(object):
    def __init__(self, fileName, branch_list, opt=None, compression_level="5"):
        # check to see if file exist
        same_file_counter = 1
        self.file_name = fileName
        while True:
            if not os.path.isfile(fileName):
                break

            logger.warning(
                f"file already existed, incrementing file index to {same_file_counter}"
            )
            same_file_counter += 1
            fileName = "".join(
                [fileName.split(".root")[0], f".root.{same_file_counter}"]
            )
            if os.path.isfile(fileName):
                continue
            else:
                break

        # start creating output file
        self.tfile = ROOT.TFile(fileName, "RECREATE", compression_level)
        self.ttree = ROOT.TTree("wfm", "recorded waveform(remote mode)")
        self.w = []
        self.t = []
        self.i_timestamp = array("d", [0])
        self.i_current = array("d", [0])
        self.threshold_level = array("d", [0])
        self.additional_branch = dict()
        if opt is None:
            pass
        elif "Threshold_scan" in opt:
            self.ttree.Branch(
                "threshold_level", self.threshold_level, "threshold_level/D"
            )
        else:
            pass
        self.ttree.Branch("i_timestamp", self.i_timestamp, "i_timestamp/D")
        self.ttree.Branch("i_current", self.i_current, "i_current/D")
        for i in range(len(branch_list)):
            self.w.append(ROOT.std.vector("double")())
            self.t.append(ROOT.std.vector("double")())
            self.ttree.Branch(f"w{branch_list[i]}", self.w[i])
            self.ttree.Branch(f"t{branch_list[i]}", self.t[i])

    def Fill(self):
        self.ttree.Fill()
        for b_w, b_t in zip(self.w, self.t):
            b_w.clear()
            b_t.clear()

    def create_branch(self, name, type):
        if type == "D":
            self.additional_branch[str(name)] = array("d", [0])
        elif type == "I":
            self.additional_branch[str(name)] = array("i", [0])
        else:
            logger.critical(f"Invalid data type for {name}")
            logger.warning("Using default (type Double)")

        self.ttree.Branch(str(name), self.additional_branch[name], f"{name}/{type}")
        logger.info(f"additional branch ({name}) is created")

    def Close(self):
        logger.info("Writing file")
        self.tfile.Write()
        self.tfile.Close()
        logger.info("file is finished")
