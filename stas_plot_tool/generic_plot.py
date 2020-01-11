import ROOT
import multiprocessing as mp
from array import array
import time


class Generic_Plot:
    def __init__(self, xTitle, yTitle):
        self._start_time = mp.Value("d", time.time())
        self.xTitle = xTitle
        self.yTitle = yTitle
        self.x = mp.Array("d", 10000)
        self.x[0] = time.time() - self._start_time.value
        self.y = mp.Array("d", 10000)
        self.y[0] = 0.0
        self.maxSize = 10000
        self.counter = mp.Value("i", 1)

    def updateValue(self, x, y):
        self.clear()
        self.x[self.counter.value] = x - self._start_time.value
        self.y[self.counter.value] = y
        self.counter.value += 1

    def clear(self):
        if self.counter.value >= self.maxSize:
            print("reach max number event, clean up.")
            self.x = mp.Array("d", range(10000))
            self.x[0] = time.time() - self._start_time.value
            self.y = mp.Array("d", range(10000))
            self.y[0] = 0.0
            self.counter.value = 1

    def draw(self, num):
        canvas = ROOT.TCanvas("c%s" % num)
        canvas.cd()
        while True:
            xdata = array("d", self.x)[: self.counter.value]
            ydata = array("d", self.y)[: self.counter.value]
            plot = ROOT.TGraph(len(xdata), xdata, ydata)
            plot.GetXaxis().SetTitle(self.xTitle)
            plot.GetYaxis().SetTitle(self.yTitle)
            # plot.GetYaxis().SetRangeUser(-100,100)
            # self.canvas.cd()
            plot.Draw("lap")
            canvas.Update()
            time.sleep(3)

    """
    def run(self):
        proc = mp.Process(target=self._draw)
        proc.start()
    """
