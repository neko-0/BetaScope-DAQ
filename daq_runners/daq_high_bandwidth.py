from pathlib import Path
from tqdm import tqdm
import numpy as np
import betascopedaq as betaDAQ
import argparse
import json

def daq_high_bandwidth(config):

    with open(config, "r") as f:
        config = json.load(f)
    
    # construct scope instance
    scope = betaDAQ.LecroyScope(config["ip_address"])
    scope.initialize()

    scope.set_trigger(**config["trigger_setting"])

    
    ofile = betaDAQ.ROOTFileOutput("user_data/high_bandwidth.root", config["active_channels"])
    
    for evt in tqdm(range(config["nevents"])):
        try:
            scope.wait_trigger()
            pass
        except Exception as _:
            evt -= 1
            continue
        
        data = scope.get_waveform(config["active_channels"])
        t_data, w_data = data
        for ch, (t_d, w_d) in enumerate(zip(t_data, w_data)):
            t_push_back = ofile.t[ch].push_back
            w_push_back = ofile.w[ch].push_back
            for _t, _w in zip(t_d, w_d):
                t_push_back(_t)
                w_push_back(_w)
        ofile.Fill()

            
    ofile.Close()


daq_high_bandwidth("config_high_bandwidth.json")