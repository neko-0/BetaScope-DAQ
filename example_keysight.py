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
    nsegments = config["nsegments"]
    scope.nsegments = nsegments

    if not scope.initialize(config["ip_address"], config["trigger_setting"]):
        raise IOError("cannot connect to scope!")

    for channel in config["enable_channels"]:
        scope.enable_channel(channel, "ON")

    # for commands that are not implemented, you can directly send to the scope
    scope.write(f":TIMebase:RANGe {config['time_ranges']}")
    # scope.write(f":ACQuire:SRATe:ANALog {config['sampling_rate']}")

    # prepare output files
    output_path = pathlib.Path(f"{config['output_path']}")
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = h5py.File(f"{output_path}/wav_{int(time.time())}.hdf5", "w")

    # running waveform acquisition
    with h5py.File(f"{output_path}/{int(time.time())}.hdf5", "a") as output_file:
        nevents = config["nevents"]
        pbar = tqdm.tqdm(total=int(nevents * nsegments), unit="evt", dynamic_ncols=True)
        evt_counter = 0
        for i_event in range(nevents):
            trig_status = None
            while trig_status != "1":
                trig_status = scope.wait_trigger()
            waveforms = scope.get_waveform(config["enable_channels"])

            # storing the waveforms
            for channel, wav_seg in waveforms.items():
                for wav in wav_seg:
                    t_trace, v_trace = wav
                    size = len(t_trace)
                    grp = output_file.create_group(f"evt{evt_counter}")
                    grp.create_dataset(f"{channel}/time", data=t_trace)
                    grp.create_dataset(f"{channel}/voltage", data=v_trace)
                    evt_counter += 1
            pbar.update(nsegments)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Example of DAQ with Keysight Scope")
    parser.add_argument("--config", dest="config", type=str, help="configuration file.")
    args = parser.parse_args()

    keysight_daq_runner(args.config)
