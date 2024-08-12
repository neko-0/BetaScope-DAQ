import betascopedaq as betaDAQ
import ROOT
import argparse
import numpy as np
from pathlib import Path
from tqdm import tqdm


def read_trc(filename, ch):
    with open(filename, "rb") as f:
        v_trace = np.array(betaDAQ.trcReader(f.read(), "WAV_DATA", ch))
    t_trace = np.arange(0, len(v_trace), dtype=np.double)

    return t_trace, v_trace


def trc_to_root(input_directory, ofile, channels, nevents):

    ofilename = Path(f"{input_directory}/{ofile}.root")
    ofilename.parent.mkdir(parents=True, exist_ok=True)

    o_tfile = ROOT.TFile(str(ofilename.resolve()), "RECREATE", "", 5)
    o_ttree = ROOT.TTree("wfm", "Converted from Lecroy TRC files")

    # get npts from one of the file
    t_trace, v_trace = read_trc(
        f"{input_directory}/Z{channels[0]}--pulse--00000.trc", channels[0]
    )
    npts = len(t_trace)

    # setting up output branches
    v_traces = {}
    t_traces = {}
    for ch in channels:
        v_traces[ch] = np.empty(npts, np.double)
        t_traces[ch] = np.empty(npts, np.double)
        o_ttree.Branch(f"w{ch}", v_traces[ch], f"w{ch}[{npts}]/D")
        o_ttree.Branch(f"t{ch}", t_traces[ch], f"t{ch}[{npts}]/D")

    # start parsing
    for event in tqdm(range(nevents)):
        for ch in channels:
            t_trace, v_trace = read_trc(
                f"{input_directory}/Z{ch}--pulse--{event:05d}.trc", ch
            )
            np.copyto(v_traces[ch], v_trace, "no")
            np.copyto(t_traces[ch], t_trace, "no")
        o_ttree.Fill()

    o_tfile.Write()
    o_tfile.Close()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        "--directory", dest="directory", help="Directory to the scope data."
    )
    argparser.add_argument("--ofilename", dest="ofilename", help="Output file name")
    argparser.add_argument(
        "--channels", dest="channels", help="Scope channels with comma separated."
    )
    argparser.add_argument("--nevents", dest="nevents", help="Number of events")

    argv = argparser.parse_args()

    trc_to_root(
        argv.directory, argv.ofilename, argv.channels.split(","), int(argv.nevents)
    )
