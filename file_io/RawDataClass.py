"""
for raw waveform data storage
"""


class RawDataClass(object):
    def __init__(self, tdir, fname, numCh, mode="split"):
        """
        param tdir := output directory
        param fname := file name
        param mode := saving mode
        """
        supported_mode = ["single", "split"]

        self.tdir = tdir
        self.fname = fname
        self.numCh = numCh
        self.fcounter = 0
        if mode in supported_mode:
            self.mode = mode
        else:
            print("un-supported mode. Use default split")
            self.mode = "split"

        self.fname_format = "{file_name}--C{Ch}--{counter}"

    def write_raw_data(self, ch, data):
        with open(
            self.tdir
            + self.fname_format.format(file_name=self.fname, Ch=ch, counter=self.fcount)
            + ".trc",
            "wb+",
        ) as f:
            f.write(data)

    def incre(self):
        self.fcounter += 1
