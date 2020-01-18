#!/bin/bash
#!/usr/bin/env python3

count=0
max=15
for f in raw/*root*;do
    nohup sh -c "~/DAQForProduction/utility/unpack_seg.py -f $f -c 2,3 -n 2002 -s 20" &
    count=$((count+1))
    stop=$((count%max))
    if [ "$stop" -eq "0" ]
    then
	sleep 5m
	echo "New batch"
    fi
done
