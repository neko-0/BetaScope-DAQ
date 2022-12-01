import h5py
import glob
import ROOT
import numpy
import argparse


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
def scope_h5_to_root(directory, prefix, channels, nfile=-1):
    if nfile < 0:
        nfile = len(glob.glob(f"{directory}/{prefix}_ch{channels[0]}*.h5"))
    h5_open = h5py.File
    tfile = ROOT.TFile(f"{prefix}.root", "RECREATE")
    ttree = ROOT.TTree("wfm", "from Keysight H5")
    v_traces = {}
    t_traces = {}
    num_wave = None
    num_pts = None
    num_segment = None
    for i in range(nfile):
        opened_f = {
            ch: h5_open(f"{directory}/{prefix}_ch{ch}{i:06d}", "r") for ch in channels
        }
        if i == 0:
            # initializing branches
            ch = channels[0]
            ch_lookup = f"Waveforms/Channel {ch}"
            num_wave = opened_f[ch]["Waveforms"].attrs["NumWaveforms"]
            num_pts = opened_f[ch][ch_lookup].attrs["NumPoints"]
            num_segment = opened_f[ch][ch_lookup].attrs["NumSegments"]
            for ch in channels:
                v_traces[ch] = np.zeros(num_pts, dtype=np.double)
                t_traces[ch] = np.zeros(num_pts, dtype=np.double)
                ttree.Branch(f"w{ch}", v_traces[ch])
                ttree.Branch(f"t{ch}", t_traces[ch])
        for seg in num_segment:
            for ch in channels:
                ch_path = f"Waveforms/Channel {ch}"
                seg_path = f"{ch_path}/Channel {ch} Seg{seg}Data"
                # probably optimize repeat YInc,YOrg,XOrg,XInc lookup
                YOrg = opened_f[ch_path].attrs["YOrg"]
                YInc = opened_f[ch_path].attrs["YInc"]
                XOrg = opened_f[ch_path].attrs["XOrg"]
                XInc = opened_f[ch_path].attrs["XInc"]
                v_traces[ch][:] = opened_f[seg_path][:] * YInc + YOrg
                t_traces[ch][:] = np.arange(XOrg, XOrg + num_pts * XInc, XInc)
            ttree.Fill()
        for f in opened_f.items():
            f.close()
    tfile.Write()
    tfile.Close()


# ==============================================================================

if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--mode", help="parsing mode", dest="mode")
    argparser.add_argument("--prefix", help="file prefix", dest="prefix")
    argparser.add_argument("--channels", help="channels", dest="channels")

    argv = argparser.parse_args()
    if argv.mode == "scope":
        ch = [int(i) for i in argv.channels.split(",")]
        scope_h5_to_root(argv.directory, argv.prefix, ch)
    else:
        files = glob.glob(f"{argv.directory}/*hdf5")
        print(files)
        for fname in files:
            hdf5_to_root(fname)
