#/bin/bash

for f in raw/*root*;do
    nohup sh -c "python ~/DAQForProduction/utility/unpack_seg.py -f $f -c 2,3 -n 1002 -s 20" &
done
