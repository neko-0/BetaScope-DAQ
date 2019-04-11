from LecroyTRCReader import *


def dataExtractor( fileName, channel, seq_mode = True):
    binaryRawData = LoadTRCFile(fileName)
    horizInterval = trcReader(binaryRawData, "HORIZ_INTERVAL", channel, "seq", True)
    totalEvent = trcReader(binaryRawData, "SUBARRAY_COUNT", channel, "seq", True)
    #VoffSet = trcReader(binaryRawData, "VERTICAL_OFFSET", channel, "seq", True)
    #vGain = trcReader(binaryRawData, "VERTICAL_GAIN", channel, "seq", True)
    vGain = 1.0
    waveData = trcReader(binaryRawData, "WAV_DATA", channel, "seq", True)

    voltageList = []
    timeList = []
    #print(len(waveData))
    #print("# of pnt {}".format(len(waveData)/totalEvent))
    numPts = len(waveData)/totalEvent
    #print(horizInterval)
    #aw_input(numPts)
    for i in range(int(totalEvent)):
        voltageTrace = []
        timeTrace = []
        for k in range(int(numPts)):
            timeTrace.append(k*horizInterval)
            voltageTrace.append(vGain*waveData[i*numPts+k])#-VoffSet)
        voltageList.append(voltageTrace)
        timeList.append(timeTrace)
    return [timeList,voltageList]

# Example ==========
def Example():
    import ROOT
    rootFile = ROOT.TFile("sample.root", "RECREATE")
    rootTree = ROOT.TTree("wfm", "wave traces of SSRL TB /ver 2019.2.15")
    w = ROOT.std.vector("double")()
    t = ROOT.std.vector("double")()
    rootTree.Branch("w2", w)
    rootTree.Branch("t2", t)
    #print(len(parsedData[0]))
    for f in range(100):
        parsedData = dataExtractor("test_%d.tdr"%f, 4)
        for i in range(len(parsedData[0])):
            for k in range(len(parsedData[0][i])):
                #print(parsedData[0][i][k])
                #w.push_back(11)
                #raw_input()
                t.push_back( parsedData[0][i][k] )
                w.push_back( parsedData[1][i][k] )
            rootTree.Fill()
            w.clear()
            t.clear()
            if i%500==0:print("At {}".format(i))
    rootFile.Write()
    rootFile.Close()
    raw_input("Finished")

if __name__ == "__main__":
    Example()
