import h5py
import glob
import ROOT
import numpy as np
import argparse
import logging
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import json

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
    def __init__(self, directory, prefix, channels, findex, format=0):
        self.directory = directory
        self.prefix = prefix
        self.channels = channels
        self.findex = findex
        self._opened_f = {}
        self.format = format

    def __getitem__(self, key):
        return self._opened_f[key]

    def __enter__(self):
        self._opened_f = {
            ch: h5py.File(self.compose_fname(ch), "r") for ch in self.channels
        }
        return self

    def __exit__(self, *exc_info):
        for f in self._opened_f.values():
            f.close()

    def compose_fname(self, ch):
        if self.format == 0:
            return f"{self.directory}/{self.prefix}_ch{ch}{self.findex:05d}.h5"
        elif self.format == 1:
            return f"{self.directory}/{self.prefix}{self.findex:05d}_ch{ch}.h5"
        elif self.format == 2:
            return f"{self.directory}/{self.prefix}{self.findex:05d}.h5"
        elif self.format == 3:
            return f"{self.directory}/{self.prefix}_ch{ch}.h5"

    def compose_wildcard(self, ch):
        if self.format == 0:
            return f"{self.directory}/{self.prefix}_ch{ch}*.h5"
        elif self.format == 1:
            return f"{self.directory}/{self.prefix}*_ch{ch}.h5"
        elif self.format in {2, 3}:
            return f"{self.directory}/{self.prefix}*.h5"


def scope_h5_to_root(
    directory,
    prefix,
    channels,
    start_findex=0,
    nfile=-1,
    suffix=0,
    format=0,
    output=".",
    const_branches=None,
):
    output_f = Path(f"{output}/{prefix}_{suffix}.root")
    output_f.parent.mkdir(parents=True, exist_ok=True)
    tfile = ROOT.TFile(str(output_f.resolve()), "RECREATE", "", 5)
    ttree = ROOT.TTree("wfm", "from Keysight H5")
    # initializing branches
    v_traces = {}
    t_traces = {}
    const_b = {}
    with ScopeH5(directory, prefix, channels, start_findex, format) as scope_data:
        ch = channels[0]
        ch_lookup = f"Waveforms/Channel {ch}"
        # num_wave = scope_data[ch]["Waveforms"].attrs["NumWaveforms"]
        num_pts = scope_data[ch][ch_lookup].attrs["NumPoints"]
        num_segment = scope_data[ch][ch_lookup].attrs["NumSegments"]
        logger.info(f"Number of waveform points = {num_pts}")
        logger.info(f"Number of segements = {num_segment}")
        for ch in channels:
            v_traces[ch] = np.empty(num_pts, dtype=np.double)
            t_traces[ch] = np.empty(num_pts, dtype=np.double)
            ttree.Branch(f"w{ch}", v_traces[ch], f"w{ch}[{num_pts}]/D")
            ttree.Branch(f"t{ch}", t_traces[ch], f"t{ch}[{num_pts}]/D")
        if const_branches:
            for name, bvalues in const_branches.items():
                const_b[name] = np.array(bvalues[2], dtype=bvalues[0])
                ttree.Branch(name, const_b[name], f"{name}/{bvalues[1]}")

    for i in tqdm(range(start_findex, nfile + start_findex), unit="files"):
        try:
            scope_data = ScopeH5(directory, prefix, channels, i, format)
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
                try:
                    tmp_t = np.arange(XOrg[ch], XOrg[ch] + num_pts * XInc[ch], XInc[ch])
                    np.copyto(t_traces[ch], tmp_t, "no")
                except ValueError:
                    logger.warning(
                        f"trace size is different? got {len(tmp_t)}, expect {num_pts}"
                    )
                    t_traces[ch][:] = tmp_t[: len(t_traces[ch])]
                    continue
            # if segment mode is enable
            if num_segment > 0:
                for seg in tqdm(range(1, num_segment), leave=False, unit="segment"):
                    for ch in channels:
                        ch_path = f"Waveforms/Channel {ch}"
                        seg_path = f"{ch_path}/Channel {ch} Seg{seg}Data"
                        np.copyto(
                            v_traces[ch],
                            scope_data[ch][seg_path][:] * YInc[ch] + YOrg[ch],
                            "no",
                        )
                    ttree.Fill()
            else:
                for ch in channels:
                    ch_path = f"Waveforms/Channel {ch}"
                    seg_path = f"{ch_path}/Channel {ch}Data"
                    np.copyto(
                        v_traces[ch],
                        scope_data[ch][seg_path][:] * YInc[ch] + YOrg[ch],
                        "no",
                    )
                    ttree.Fill()
    tfile.Write()
    tfile.Close()


def run_scope_h5_to_root(
    directory,
    prefix,
    channels,
    start_findex=0,
    nfile=-1,
    merge=False,
    format=0,
    use_mp=False,
    output=".",
    const_branches=None,
):
    if nfile < 0:
        with ScopeH5(directory, prefix, channels, start_findex, format) as scope_data:
            lookup = scope_data.compose_wildcard(channels[0])
        nfile = len(glob.glob(f"{lookup}"))

    common_args = (directory, prefix, channels)
    if merge:
        scope_h5_to_root(
            *common_args,
            start_findex,
            nfile,
            format=format,
            output=output,
            const_branches=const_branches,
        )
        return

    if use_mp:
        ROOT.EnableThreadSafety()
        with ProcessPoolExecutor(5) as pool:
            futures = []
            for i in range(nfile):
                common_args = (directory, prefix, channels, start_findex + i)
                kwargs_pack = {
                    "nfile": 1,
                    "suffix": i,
                    "format": format,
                    "output": output,
                    "const_branches": const_branches,
                }
                futures.append(
                    pool.submit(scope_h5_to_root, *common_args, **kwargs_pack)
                )
            for future in as_completed(futures):
                _ = future.result()
        return

    for i in range(nfile):
        scope_h5_to_root(
            *common_args,
            start_findex + i,
            nfile=1,
            suffix=i,
            format=format,
            output=output,
            const_branches=const_branches,
        )


# ==============================================================================

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--mode",
        dest="mode",
        default=None,
        help="parsing mode. the default mode is used for the simple DAQ runner. Mode 'scope' abnd 'scope-batch' are used for scope H5 format.",
    )
    argparser.add_argument(
        "--directory",
        dest="directory",
        help="directory to the H5 files.",
    )
    argparser.add_argument(
        "--prefix",
        dest="prefix",
        help="file prefix, e.g. prefix00001.h5",
    )
    argparser.add_argument(
        "--channels",
        dest="channels",
        help="channels for parsing. use common to separate.",
    )
    argparser.add_argument(
        "--format",
        type=int,
        default=0,
        dest="format",
        help="format of the wildcard lookup.",
    )
    argparser.add_argument(
        "--use-mp",
        dest="use_mp",
        action="store_true",
        help="enbaling multiprocessing.",
    )
    argparser.add_argument(
        "--start",
        type=int,
        default=0,
        dest="start",
        help="starting index of the H5 files, e.g. prefix00001.h5",
    )
    argparser.add_argument(
        "--merge",
        dest="merge",
        action="store_true",
        help="Converted all H5 files into single ROOT file.",
    )
    argparser.add_argument(
        "--output",
        dest="output",
        default=".",
        help="output directory for the ROOT files.",
    )
    argparser.add_argument(
        "--joblist",
        dest="joblist",
        help="JSON file for batch parsing. The JSON format: keys as jobname, values are the arguments used for the parser.",
    )
    argparser.add_argument(
        "--jobname",
        dest="jobname",
        help="parsing the jobname listed in the joblist JSON file.",
    )
    argparser.add_argument(
        "--const", dest="const_branches", type=json.loads, default=None
    )

    argv = argparser.parse_args()
    if argv.mode == "scope":
        ch = [int(i) for i in argv.channels.split(",")]
        run_scope_h5_to_root(
            argv.directory,
            argv.prefix,
            ch,
            argv.start,
            merge=argv.merge,
            format=argv.format,
            use_mp=argv.use_mp,
            output=argv.output,
            const_branches=argv.const_branches,
        )
    if argv.mode == "scope-batch":
        with open(argv.joblist) as f:
            jobs = json.load(f)
        for job in jobs[argv.jobname]:
            try:
                run_scope_h5_to_root(**job)
            except Exception as _err:
                logger.warning(f"cannot run {job} due to {_err}")
                continue
    else:
        files = glob.glob(f"{argv.directory}/*hdf5")
        print(files)
        for fname in files:
            default_hdf5_to_root(fname)
