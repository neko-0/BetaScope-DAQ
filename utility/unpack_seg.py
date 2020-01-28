#!/usr/bin/env python2
"""
use for unpacking the segmented output file from keysight scope
"""

import ROOT
from array import array


def unpack_seg(ifile_name, ch_list, num_pts, seg_count):

    ifile = ROOT.TFile.Open(ifile_name)
    itree = ifile.Get("wfm")

    ofile = ROOT.TFile.Open("unseg_" + ifile_name.split("/")[1], "RECREATE")
    otree = ROOT.TTree("wfm", "un-segmented tree from DAQ")
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
        channels_v[ch] = ROOT.std.vector("double")()
        channels_t[ch] = ROOT.std.vector("double")()
        otree.Branch("w{}".format(ch), channels_v[ch])
        otree.Branch("t{}".format(ch), channels_t[ch])
    otree.Branch("temperature", temperature, "temperature/D")
    otree.Branch("humidity", humidity, "humidity/D")
    otree.Branch("pi_temperature", temperature, "pi_temperature/D")
    otree.Branch("pi_humidity", humidity, "pi_humidity/D")
    otree.Branch("i_timestamp", i_timestamp, "i_timestamp/D")
    otree.Branch("i_current", i_current, "i_current/D")
    otree.Branch("ievent", ievent, "ievent/I")
    otree.Branch("cycle", cycle, "cycle/I")

    for ientry, entry in enumerate(itree):
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
        if ientry % 100 == 0:
            print(ientry)
        for seg in range(seg_count):
            xorigin = None
            dt = None
            for pt in range(num_pts):
                for ch in ch_list:
                    if xorigin == None:
                        xorigin = getattr(entry, "t{}".format(ch))[0]
                    if dt == None:
                        dt = (
                            getattr(entry, "t{}".format(ch))[1]
                            - getattr(entry, "t{}".format(ch))[0]
                        )
                    channels_v[ch].push_back(
                        getattr(entry, "w{}".format(ch))[pt + seg * num_pts]
                    )
                    channels_t[ch].push_back(xorigin)
                xorigin += dt
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
    parser.add_argument("-f", type=str)
    parser.add_argument("-c", type=str)
    parser.add_argument("-n", type=int)
    parser.add_argument("-s", type=int)

    user_args = parser.parse_args()

    chList = [x for x in user_args.c.split(",")]

    unpack_seg(user_args.f, chList, user_args.n, user_args.s)
