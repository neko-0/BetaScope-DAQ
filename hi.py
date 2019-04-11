from DAQProducer import *
from DAQConfigReader import *
import time
#from statsPlot import *
import trcDataExtractor as trc
import numpy as np

time.sleep(3)
config = DAQConfig()
config.ReadDAQConfig("BetaDAQ_Config.ini")
scope = ScopeProducer(config)

#hi = StatsPlot()
#hi.processing()
ave = []
for i in range(10):
    _start = time.time()
    ofile = open("test.tdr","wb")
    t1 = time.time()
    scope.WaitForTrigger()
    #scope.Scope.inst.query("ARM;WAIT;*OPC?")
    #scope.Scope.inst.write("ARM;WAIT")
    #data = scope.GetWaveform([4])
    t2 = time.time()
    print(t2-t1)
    #t1 = time.time()
    scope.Scope.inst.write("C2:WF?")
    data = scope.Scope.inst.read_raw()
    t2 = time.time()
    print("here {}".format(t2-t1))
    t1=time.time()
    ofile.write(data)
    ofile.close()
    data = trc.dataExtractor("test.tdr", 2)
    #hi.updateData(data)
    t2 = time.time()
    print(t2-t1)
    _end = time.time()
    print("Rate: {}".format(80.0/(_end-_start)))
    ave.append(80.0/(_end-_start))
    print(data)

print("AVE: {}".format(sum(ave)/len(ave)))
