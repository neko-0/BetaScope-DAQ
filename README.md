# DAQForProduction

## Installation

Simply running pip install.

```
python -m pip install -e .
```

## Running the DAQ

Required ROOT to be linked with python.

If you are using the UFSDLab computer, simply type the following command in the terminal:

```
user@UFSDLab:~$ root_py3
user@UFSDLab:~$ DAQ
```

### Instruments with GPIB

You will need linux-gpib. After installing linux-gpib, load the kernel module with

```
sudo modprobe ni_usb_gpib
sudo gpib_config -f /etc/gpib.conf
```

### Converting Lecroy scope data to ROOT format

#### On UFSD lab computer (xrayuser account)

When you login and open the terminal, source the python environment

```
source pyDAQ/bin/activate
```

Then, use the `trc_to_root` script from the `daq_runners` directory, for example

```
python BetaScope-DAQ/daq_runners/trc_to_root.py --directory <src_path> --ofilename <output> --channels "1,2,3", --nevents 100
```

The output file would be in `<src_path>/<output>.root`