"""
Example runner script using Keysight Scope
"""

import pathlib
import time
import json
import h5py
import argparse
import betascopedaq
import tqdm


def keysight_daq_runner(config_file):

    # read in JSON configuration file
    with open(config_file, "r") as f:
        config = json.load(f)

    # construct scope instance
    scope = betascopedaq.KeysightScope()

    if not scope.initialize(config["ip_address"], config["trigger_setting"]):
        raise IOError("cannot connect to scope!")

    for channel in config["enable_channels"]:
        scope.enable_channel(channel, "ON")

    # prepare output files
    output_path = pathlib.Path(f"{config['output_path']}")
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = h5py.File(f"{output_path}/wav_{int(time.time())}.hdf5", "w")

    # running waveform acquisition
    with h5py.File(f"{output_path}/{int(time.time())}.hdf5", "a") as output_file:
        nevents = range(config["nevents"])
        evt_counter = 0
        for i_event in tqdm.tqdm(nevents):
            trig_status = None
            while trig_status != "1":
                trig_status = scope.wait_trigger()
            waveforms = scope.get_waveform(config["enable_channels"])

            for channel, wav_seg in waveforms.items():
                for wav in wav_seg:
                    t_trace, v_trace = wav
                    size = len(t_trace)
                    grp = output_file.create_group(f"evt{evt_counter}")
                    grp.create_dataset(f"ch{channel}/time", data=t_trace)
                    grp.create_dataset(f"ch{channel}/voltage", data=v_trace)
                    evt_counter += 1


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Example of DAQ with Keysight Scope")
    parser.add_argument("--config", dest="config", type=str, help="configuration file.")
    args = parser.parse_args()

    keysight_daq_runner(args.config)
