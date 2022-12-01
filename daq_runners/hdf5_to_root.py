import h5py
import glob
import ROOT
import numpy as np
import argparse
import logging
from tqdm import tqdm

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def default_hdf5_to_root(fname):
    channels = [2, 3]
    tfile = ROOT.TFile(f"{fname}.root", "RECREATE")
    ttree = ROOT.TTree("wfm", "from simple keysight daq runner")
    wav_ch = {}
    time_ch = {}
    for ch in channels:
        wav_ch[ch] = ROOT.std.vector("double")()
        time_ch[ch] = ROOT.std.vector("double")()
        ttree.Branch(f"w{ch}", wav_ch[ch])
        ttree.Branch(f"t{ch}", time_ch[ch])

    with h5py.File(fname, "r") as wavfile:
        nevents = len(wavfile.keys())
        avg_counter = 0
        for i in range(nevents):
            if i % 100 == 0:
                print(i)
            for ch in channels:
                try:
                    w_data = wavfile[f"evt{i}/seg0/ch{ch}/voltage"][:]
                    t_data = wavfile[f"evt{i}/seg0/ch{ch}/time"][:]
                except KeyError:
                    continue
                wav_ch[ch].clear()
                time_ch[ch].clear()
                for _w, _t in zip(w_data, t_data):
                    wav_ch[ch].push_back(_w)
                    time_ch[ch].push_back(_t)
            ttree.Fill()

    tfile.Write()
    tfile.Close()


# ==============================================================================
class ScopeH5:
    def __init__(self, directory, prefix, channels, findex):
        self.directory = directory
        self.prefix = prefix
        self.channels = channels
        self.findex = findex
        self._opened_f = {}

    def __getitem__(self, key):
        return self._opened_f[key]

    def __enter__(self):
        self._opened_f = {
            ch: h5py.File(
                f"{self.directory}/{self.prefix}_ch{ch}{self.findex:05d}.h5", "r"
            )
            for ch in self.channels
        }
        return self._opened_f

    def __exit__(self, *exc_info):
        for f in self._opened_f.values():
            f.close()


def scope_h5_to_root(directory, prefix, channels, start_findex=0, nfile=-1):
    if nfile < 0:
        nfile = len(glob.glob(f"{directory}/{prefix}_ch{channels[0]}*.h5"))
    tfile = ROOT.TFile(f"{prefix}.root", "RECREATE")
    ttree = ROOT.TTree("wfm", "from Keysight H5")

    # initializing branches
    v_traces = {}
    t_traces = {}
    with ScopeH5(directory, prefix, channels, start_findex) as scope_data:
        ch = channels[0]
        ch_lookup = f"Waveforms/Channel {ch}"
        num_wave = scope_data[ch]["Waveforms"].attrs["NumWaveforms"]
        num_pts = scope_data[ch][ch_lookup].attrs["NumPoints"]
        num_segment = scope_data[ch][ch_lookup].attrs["NumSegments"]
        for ch in channels:
            v_traces[ch] = np.zeros(num_pts, dtype=np.double)
            t_traces[ch] = np.zeros(num_pts, dtype=np.double)
            ttree.Branch(f"w{ch}", v_traces[ch], f"w{ch}[{num_pts}]/D")
            ttree.Branch(f"t{ch}", t_traces[ch], f"t{ch}[{num_pts}]/D")

    for i in tqdm(range(start_findex, nfile), unit="files"):
        try:
            scope_data = ScopeH5(directory, prefix, channels, i)
        except FileNotFoundError:
            logger.warning(f"cannot retrieve all channel data for findex {i}")
            continue
        with scope_data:
            YOrg = {}
            YInc = {}
            XOrg = {}
            XInc = {}
            for ch in channels:
                ch_path = f"Waveforms/Channel {ch}"
                YOrg[ch] = scope_data[ch][ch_path].attrs["YOrg"]
                YInc[ch] = scope_data[ch][ch_path].attrs["YInc"]
                XOrg[ch] = scope_data[ch][ch_path].attrs["XOrg"]
                XInc[ch] = scope_data[ch][ch_path].attrs["XInc"]
            for seg in tqdm(range(1, num_segment), leave=False, unit="segment"):
                for ch in channels:
                    ch_path = f"Waveforms/Channel {ch}"
                    seg_path = f"{ch_path}/Channel {ch} Seg{seg}Data"
                    v_traces[ch][:] = scope_data[ch][seg_path][:] * YInc[ch] + YOrg[ch]
                    t_traces[ch][:] = np.arange(
                        XOrg[ch], XOrg[ch] + num_pts * XInc[ch], XInc[ch]
                    )
                ttree.Fill()
    tfile.Write()
    tfile.Close()


# ==============================================================================

if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--mode", help="parsing mode", dest="mode")
    argparser.add_argument("--directory", help="file direcotry", dest="directory")
    argparser.add_argument("--prefix", help="file prefix", dest="prefix")
    argparser.add_argument("--channels", help="channels", dest="channels")
    argparser.add_argument(
        "--start", help="start findex", type=int, default=0, dest="start"
    )

    argv = argparser.parse_args()
    if argv.mode == "scope":
        ch = [int(i) for i in argv.channels.split(",")]
        scope_h5_to_root(argv.directory, argv.prefix, ch, argv.start)
    else:
        files = glob.glob(f"{argv.directory}/*hdf5")
        print(files)
        for fname in files:
            hdf5_to_root(fname)
