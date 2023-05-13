#!/usr/bin/env python3
"""
use for unpacking the segmented output file from keysight scope
"""

import numpy as np
import multiprocessing as mp
import os
from array import array
from tqdm import tqdm
import ROOT

# import logging

# logging.basicConfig()
# logger = logging.getLogger(__name__)


def unpack_seg(ifile_name, ch_list, num_pts, seg_count):
    ifile = ROOT.TFile.Open(ifile_name)
    itree = ifile.Get("wfm")
    ifile_name = ifile_name.replace("//", "/")
    ofile = ROOT.TFile.Open(f"unseg_{ifile_name.split('/')[1]}", "RECREATE")
    otree = ROOT.TTree("wfm", "un-segmented tree from DAQ")
    otree.SetDirectory(ofile)
    channels_v = {}
    channels_t = {}
    temperature = array("d", [0])
    humidity = array("d", [0])
    pi_temperature = array("d", [0])
    pi_humidity = array("d", [0])
    i_timestamp = array("d", [0])
    i_current = array("d", [0])
    ievent = array("i", [0])
    cycle = array("i", [0])
    for ch in ch_list:
        channels_v[ch] = ROOT.std.vector("double")(num_pts)
        channels_t[ch] = ROOT.std.vector("double")(num_pts)
        otree.Branch(f"w{ch}", channels_v[ch])
        otree.Branch(f"t{ch}", channels_t[ch])
    otree.Branch("temperature", temperature, "temperature/D")
    otree.Branch("humidity", humidity, "humidity/D")
    otree.Branch("pi_temperature", temperature, "pi_temperature/D")
    otree.Branch("pi_humidity", humidity, "pi_humidity/D")
    otree.Branch("i_timestamp", i_timestamp, "i_timestamp/D")
    otree.Branch("i_current", i_current, "i_current/D")
    otree.Branch("ievent", ievent, "ievent/I")
    otree.Branch("cycle", cycle, "cycle/I")

    for entry in tqdm(itree):
        try:
            temperature[0] = entry.temperature
            pi_humidity[0] = entry.humidity
        except:
            pass
        try:
            pi_temperature[0] = entry.pi_temperature
            pi_humidity[0] = entry.pi_humidity
        except:
            pass
        i_timestamp[0] = entry.i_timestamp
        i_current[0] = entry.i_current
        ievent[0] = entry.ievent
        cycle[0] = entry.cycle
        for seg in range(seg_count):
            for ch in ch_list:
                t_trace = getattr(entry, f"t{ch}")
                v_trace = getattr(entry, f"w{ch}")
                xorigin = xorigin = t_trace[0]
                dt = t_trace[1] - t_trace[0]
                # construct new time trace
                new_t_trace = np.arange(xorigin, num_pts) * dt + xorigin
                # filling channel branches
                channels_v[ch].swap(v_trace[seg * num_pts : (seg + 1) * num_pts])
                channels_t[ch].swap(ROOT.std.vector("double")(new_t_trace))
            otree.Fill()
            for key in channels_v.keys():
                channels_v[key].clear()
            for key in channels_t.keys():
                channels_t[key].clear()

    otree.Write()
    ofile.Close()
    ifile.Close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", type=str)
    parser.add_argument("-c", type=str)
    parser.add_argument("-n", type=int)
    parser.add_argument("-s", type=int)

    user_args = parser.parse_args()

    chList = [x for x in user_args.c.split(",")]

    files = [f"{user_args.d}/{f}" for f in os.listdir(user_args.d) if "root" in f]

    pool = mp.Pool()
    for file in files:
        pool.apply_async(unpack_seg, args=(file, chList, user_args.n, user_args.s))
        # unpack_seg(file, chList, user_args.n, user_args.s)
    pool.close()
    pool.join()
    # unpack_seg(user_args.f, chList, user_args.n, user_args.s)
