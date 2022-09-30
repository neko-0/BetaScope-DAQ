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
import plotext as plt

DISPLAY_FIRST_SEG = True


def keysight_daq_runner(config_file, display_wav):

    # read in JSON configuration file
    with open(config_file, "r") as f:
        config = json.load(f)

    # construct scope instance
    scope = betascopedaq.KeysightScope()
    nsegments = config["nsegments"]
    scope.nsegments = nsegments

    if not scope.initialize(config["ip_address"], config["trigger_setting"]):
        raise IOError("cannot connect to scope!")

    for channel in [1,2,3,4]:
        scope.enable_channel(channel, "OFF")

    for channel in config["enable_channels"]:
        scope.enable_channel(channel, "ON")

    # for commands that are not implemented, you can directly send to the scope
    scope.write(f":ACQ:BAND {config['bandwidth']}")
    scope.write(f":TIMebase:RANGe {config['time_ranges']}")
    scope.write(f":ACQuire:SRATe {config['sampling_rate']}")
    # prepare output files
    output_path = pathlib.Path(f"{config['output_path']}")
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = time.time() # just initialize it with staring time

    # running waveform acquisition
    with h5py.File(f"{output_path}/{int(time.time())}.hdf5", "a") as output_file:
        nevents = config["nevents"]
        pbar = tqdm.tqdm(total=int(nevents * nsegments), unit="evt", dynamic_ncols=True)
        for i_event in range(nevents):
            trig_status = None
            while trig_status != "1":
                trig_status = scope.wait_trigger()
                timestamp = time.time()
            waveforms = scope.get_waveform(config["enable_channels"])

            display_ch = {}
            # storing the waveforms
            evt_grp = output_file.create_group(f"evt{i_event}")
            for channel, wav_seg in waveforms.items():
                for iseg, wav in enumerate(wav_seg):
                    seg_index = f"seg{iseg}"
                    if seg_index in evt_grp:
                        seg_grp = evt_grp[seg_index]
                    else:
                        seg_grp = evt_grp.create_group(seg_index)
                    t_trace, v_trace = wav
                    seg_grp.create_dataset(f"{channel}/time", data=t_trace)
                    seg_grp.create_dataset(f"{channel}/voltage", data=v_trace)
                    seg_grp.create_dataset(f"{channel}/timestamp", data=timestamp)
                    if display_wav:
                        if channel not in display_ch:
                            display_ch[channel] = {
                                "time": t_trace.tolist(),
                                "voltage": v_trace.tolist(),
                            }
                        elif not DISPLAY_FIRST_SEG:
                            display_ch[channel]["time"] += t_trace.tolist()
                            display_ch[channel]["voltage"] += v_trace.tolist()
            if display_wav:
                plt.subplots(1, len(display_ch))
                for i, ch in enumerate(display_ch, start=1):
                    plt.subplot(1, i)
                    plt.plot(
                        display_ch[ch]["time"], display_ch[ch]["voltage"], label=ch
                    )
                plt.show()
                plt.clear_figure()
            pbar.update(nsegments)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Example of DAQ with Keysight Scope")
    parser.add_argument("--config", dest="config", type=str, help="configuration file.")
    parser.add_argument(
        "--display-wav",
        dest="display_wav",
        action="store_true",
        help="text waveform display.",
    )

    args = parser.parse_args()

    keysight_daq_runner(args.config, args.display_wav)
