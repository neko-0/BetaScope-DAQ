# DAQForProduction

## Installation

```
pip install -e .
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
