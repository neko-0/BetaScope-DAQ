import multiprocessing as mp
import trcDataExtractor as TRC
from array import array
import ROOT


class StatsPlot:
    def __init__(self):
        self._updatePlotQueue = mp.Queue()
        self._terminateQueue = mp.Queue()
        self._waveDataQueue = mp.Queue()
        self._terminateQueue.put(False)

    def updateData(self, waveData):
        # while( not self._terminateQueue.get() ):
        self._waveDataQueue.put(waveData)
        self._updatePlotQueue.put(True)

    def _updateWaveformPlot(self):
        waveCanvas = ROOT.TCanvas("waveCanvas")
        waveCanvas.cd()
        while not self._terminateQueue.get():
            print("hello")
            while self._updatePlotQueue.get():
                w = array("d")
                t = array("d")
                waveData = self._waveDataQueue.get()
                for i in range(len(waveData[0])):
                    for k in range(len(waveData[0][i])):
                        w.append(waveData[0][i][k])
                        t.append(waveData[1][i][k])
                wavePlot = ROOT.TGraph(len(w), w, t)
                wavePlot.Draw("lap")
                waveCanvas.Update()
            self._updatePlotQueue.put(False)

    def processing(self):
        plotProcess = mp.Process(target=self._updateWaveformPlot)
        plotProcess.start()
