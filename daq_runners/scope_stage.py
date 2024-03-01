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
import numpy as np
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def dry_test():
    pass


def stage_stepper(x_start, x_end, x_step, y_start, y_end, y_step):
    x_incr = (x_end - x_start) / x_step
    y_incr = (y_end - y_start) / y_step
    for x in np.arange(x_start, x_end + x_incr, x_incr):
        for y in np.arange(y_start, y_end + y_incr, y_incr):
            yield x, y


def scope_stage(config_file):

    # read in JSON configuration file
    with open(config_file, "r") as f:
        config = json.load(f)

    # construct scope instance
    scope = betascopedaq.KeysightScope()
    nsegments = config["nsegments"]
    scope.nsegments = nsegments

    nevents = config["nevents"]

    if not scope.initialize(config["ip_address"], config["trigger_setting"]):
        raise RuntimeError("Cannot connect to scope!")

    # connect to stage. Need a default fallback if no stage?
    stage = None
    stage_steps = None
    if not config["stage"]["manual"]:
        axes = {"x": config["stage"]["x_axis"], "y": config["stage"]["y_axis"]}
        stage = betascopedaq.Stage(axes)
        stage.setup_api(config["stage"]["api"])
        stage.connect()
        if not stage.connected:
            raise RuntimeError("Cannot connect to stage!")
        pos = stage.getPosition()
        logger.info(f"Current stage position {pos}")

        stage_steps = stage_stepper(
            config["stage"]["x_start"],
            config["stage"]["x_end"],
            config["stage"]["x_step"],
            config["stage"]["y_start"],
            config["stage"]["y_end"],
            config["stage"]["y_step"],
        )

    for channel in [1, 2, 3, 4]:
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
    output_name = config["output_name"] or int(time.time())

    timestamp = time.time()  # just initialize it with staring time
    wait_timeout = 10

    # setting pos to starting points
    stage.to2d(config["stage"]["x_start"], config["stage"]["x_end"], True)

    # running waveform acquisition
    for i, (xpos, ypos) in enumerate(stage_steps):
        stage.to2d(xpos, ypos, True)
        with h5py.File(f"{output_path}/{output_name}_{i}.hdf5", "a") as output_file:
            pbar = tqdm.tqdm(
                total=int(nevents * nsegments), unit="evt", dynamic_ncols=True
            )
            i_event = 0
            while i_event < nevents:
                trig_status = None
                wait_time = time.time()
                while trig_status != "1":
                    trig_status = scope.wait_trigger()
                    timestamp = time.time()
                    if (timestamp - wait_time) > wait_timeout:
                        print(f"waiting too long ({wait_timeout}s) {trig_status}")
                        wait_time = timestamp
                try:
                    waveforms = scope.get_waveform(config["enable_channels"])
                except IOError:
                    print("error in getting waveform")
                    scope.reset()
                    continue

                # storing the waveforms
                evt_grp = output_file.create_group(f"evt{i_event}")
                evt_grp.attrs["xpos"] = xpos
                evt_grp.attrs["ypos"] = ypos
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

                pbar.update(nsegments)
                i_event += 1

    # reset pos to starting points
    stage.to2d(config["stage"]["x_start"], config["stage"]["x_end"], True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Example of DAQ with Keysight Scope")
    parser.add_argument("--config", dest="config", type=str, help="configuration file.")

    args = parser.parse_args()

    scope_stage(args.config)
