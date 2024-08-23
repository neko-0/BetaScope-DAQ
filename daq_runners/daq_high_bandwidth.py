import numpy as np
import tkinter as tk
import json
import logging
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

_LIBGPIB_SO = "/usr/local/lib/libgpib.so"
try:
    from gpib_ctypes.gpib import _load_lib

    _load_lib(_LIBGPIB_SO)
except FileNotFoundError:
    logger.critical(f"cannot find {_LIBGPIB_SO}")
    logger.critical("try to use envir setting LIBGPIB_SO")
    import os

    _load_lib(os.environ["LIBGPIB_SO"])

from betascopedaq.oscilloscope import LecroyScope
from betascopedaq.generator import Agilent81110A
from betascopedaq import ROOTFileOutput


def _run_with_config(config, entries):

    _update_config(config, entries)

    daq_high_bandwidth(config)


def _update_config(config, entries):

    for key in config:
        if isinstance(config[key], dict):
            _update_config(config[key], entries)
        else:
            if isinstance(config[key], int):
                config[key] = int(entries[key].get())
            elif isinstance(config[key], bool):
                config[key] = bool(entries[key].get())
            elif isinstance(config[key], list):
                type_caster = type(config[key][0])
                config[key] = [type_caster(x) for x in entries[key].get().split()]
            elif isinstance(config[key], float):
                config[key] = float(entries[key].get())
            else:
                config[key] = entries[key].get()

    output = Path("cache/config_high_bandwidth.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(config, f, indent=4)


def daq_gui(config):
    with open(config, "r") as f:
        config = json.load(f)

    gui_it = tk.Tk()
    gui_it.geometry("1000x1000")
    gui_it.title("High Bandwidth DAQ")

    # text = tk.Text(gui_it, state="normal", height=20, width=60, undo=True)
    # text.place(x=10, y=50)
    # text.insert("1.0", str(config))

    labels = {}
    entries = {}
    _row = 0

    def _create_label(key, data, labels, entries, font=("calibre", 20, "bold")):
        nonlocal _row
        labels[key] = tk.Label(gui_it, text=key, font=font, justify="right", anchor="e")
        # labels[key].pack()
        if isinstance(data, dict):
            labels[key].config(font=("calibre", 20))
            labels[key].grid(row=_row, column=1)
            for j, (sub_key, sub_data) in enumerate(data.items()):
                _row += 1
                # labels[key][sub_key] = {}
                # entries[key][sub_key] = {}
                _create_label(sub_key, sub_data, labels, entries, font=("calibre", 15))
        else:
            labels[key].grid(row=_row, column=0, sticky="e")
            labels[key].config(fg="blue")
            entries[key] = tk.Entry(
                gui_it, bg="white", width=50, borderwidth=2, font=("calibre", 15)
            )
            entries[key].grid(row=_row, column=1)
            entries[key].insert(0, data)
            _row += 1

    for i, (key, data) in enumerate(config.items()):
        _create_label(key, data, labels, entries)

    run_button = tk.Button(
        gui_it,
        text="Start",
        width=50,
        borderwidth=2,
        font=("calibre", 15),
        command=lambda: _run_with_config(config, entries),
    )
    run_button.config(bg="green", fg="red")
    run_button.grid(row=_row, column=1)

    gui_it.mainloop()


# ====================================================================================================
# ====================================================================================================


def daq_high_bandwidth(config):

    if not isinstance(config, dict):
        with open(config, "r") as f:
            config = json.load(f)

    # construct scope instance
    scope = LecroyScope(config["scope"]["ip_address"])
    scope.initialize()

    scope.set_trigger(**config["scope"]["trigger_setting"])

    if config["delay_scan"]["enable"]:
        delay_start = config["delay_scan"]["start"]
        delay_end = config["delay_scan"]["end"]
        delay_step = config["delay_scan"]["step_size"]
        delay_ranges = np.arange(delay_start, delay_end, delay_step)
        wav_gen = Agilent81110A(board=config["delay_scan"]["board"])
    else:
        delay_ranges = [0]  # single 0 zero delay
        wav_gen = None

    wav_gen = Agilent81110A(board=10)

    output_name = f"{config['output']['directory']}/{config['output']['name']}"

    ofile = ROOTFileOutput(output_name, config["active_channels"])
    ofile.create_branch("delay", "D")
    ofile.create_branch("t_interval", "D")

    for delay in tqdm(delay_ranges):
        if wav_gen:
            wav_gen.write(f":PULSe:DELay2 {delay}NS")
        ofile.additional_branch["delay"][0] = delay
        naverage = config["output"]["naverage"] or 1.0
        tot_evnts = config["output"]["nevents"] * naverage
        for evt in tqdm(range(tot_evnts), leave=False):
            if naverage > 1.0:
                data = None
                for avg_count in range(naverage):
                    try:
                        scope.wait_trigger()
                    except:
                        avg_count -= 1
                        continue
                    if data is None:
                        data = scope.get_waveform(
                            config["scope"]["active_channels"], ch_prefix="Z"
                        )
                        # casting the list to numpy array for each channels
                        for ch in range(len(data[1])):
                            data[1][ch] = np.array(data[1][ch])
                    else:
                        new_data = scope.get_waveform(
                            config["scope"]["active_channels"], ch_prefix="Z"
                        )
                        for ch, (t_d, w_d) in enumerate(zip(*new_data)):
                            data[ch][1] += np.array(w_d) * 0.5
            else:
                try:
                    scope.wait_trigger()
                except:
                    evt -= 1
                    continue
                data = scope.get_waveform(
                    config["scope"]["active_channels"], ch_prefix="Z"
                )

            for ch, (t_d, w_d) in enumerate(zip(*data)):
                t_push_back = ofile.t[ch].push_back
                w_push_back = ofile.w[ch].push_back
                for i, (_t, _w) in enumerate(zip(t_d, w_d)):
                    # t_push_back(_t)
                    t_push_back(i)
                    w_push_back(_w)
                # assume all of the time interval are the same across channels.
                ofile.additional_branch["t_interval"][0] = t_d[1] - t_d[0]
            ofile.Fill()

    ofile.Close()


if __name__ == "__main__":
    # daq_high_bandwidth("config_high_bandwidth.json")

    daq_gui("config_high_bandwidth.json")
