import h5py
import glob
import ROOT


def hdf5_to_root(fname):
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


if __name__ == "__main__":

    files = glob.glob("/media/mnt/COVID-19/DJ_LGAD/2022Oct4_DJ2/*/*hdf5")
    print(files)
    for fname in files:
        hdf5_to_root(fname)
