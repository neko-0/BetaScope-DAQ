#!/bin/bash

sudo modprobe ni_usb_gpib
sudo gpib_config -f /etc/gpib.conf
