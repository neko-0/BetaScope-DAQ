from tqdm import tqdm
import numpy as np
import json
import betascopedaq as betaDAQ
from betascopedaq.generator import Agilent81110A


def daq_high_bandwidth(config):

    with open(config, "r") as f:
        config = json.load(f)

    # construct scope instance
    scope = betaDAQ.LecroyScope(config["ip_address"])
    scope.initialize()

    scope.set_trigger(**config["trigger_setting"])

    if config["delay_scan"]["enable"]:
        delay_start = config["delay_scan"]["start"]
        delay_end = config["delay_scale"]["end"]
        delay_step = config["delay_scale"]["step_size"]
        delay_ranges = np.arange(delay_start, delay_end, delay_step)
        wav_gen = Agilent81110A(board=10)
    else:
        delay_ranges = [0]
        wav_gen = None

    wav_gen = Agilent81110A(board=10)

    output_name = f"{config['output']['directory']}/{config['output']['name']}"

    ofile = betaDAQ.ROOTFileOutput(output_name, config["active_channels"])
    ofile.create_branch("delay", "D")

    for delay in tqdm(delay_ranges):
        if wav_gen:
            wav_gen.write(f":PULSe:DELay2 {delay}NS")
        ofile.additional_branch["delay"] = delay
        for evt in tqdm(range(config["nevents"]), leave=False):
            try:
                scope.wait_trigger()
            except:
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


if __name__ == "__main__":
    daq_high_bandwidth("config_high_bandwidth.json")
