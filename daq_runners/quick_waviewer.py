import h5py
import numpy as np
import plotext as plt


def quick_waviewer(fname):

    channels = [2, 3]
    n_avg = 500
    filter_ch = 3
    filter_threshold = 0.11

    with h5py.File(fname, "r") as wavfile:
        nevents = len(wavfile.keys())
        avg_counter = 0
        wav_dict = {i: [] for i in channels}
        wav_cache = {i: [] for i in channels}
        for i in range(0, nevents):
            if filter_ch:
                try:
                    tmp_data = wavfile[f"evt{i}/seg0/ch{filter_ch}/voltage"][:]
                except KeyError:
                    continue
                if abs(tmp_data).max() < filter_threshold:
                    continue
            for ch in channels:
                try:
                    wav_cache[ch].append(wavfile[f"evt{i}/seg0/ch{ch}/voltage"][:])
                except KeyError:
                    continue
            if i == 0:
                continue
            if i % n_avg == 0 or i == nevents - 1:
                for ch in channels:
                    avg_data = np.sum(wav_cache[ch], axis=0) / n_avg
                    wav_dict[ch].append(avg_data)
                wav_cache = {i: [] for i in channels}

        plt.subplots(1, len(channels))
        for i, ch in enumerate(channels, start=1):
            plt.subplot(1, i)
            for iwav, data in enumerate(wav_dict[ch]):
                t_trace = np.array(range(len(data)))
                mask = np.where((t_trace > 2900) & (t_trace < 3800), True, False)
                plt.plot(t_trace[mask], data[mask], label=f"{ch}-{iwav}")
        plt.show()
        plt.clear_figure()


if __name__ == "__main__":
    # fname = "/media/mnt/COVID-19/DJ_LGAD/2022Sept30_DJ/BIAS_600V/th20/1664576324.hdf5"
    fname = (
        "/media/mnt/COVID-19/DJ_LGAD/2022Sept30_DJ2/BIAS_500V_Neg30C/1664587185.hdf5"
    )
    quick_waviewer(fname)
