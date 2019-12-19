from core import Keithley

import time

ps = Keithley()

ps.smua.source.levelv = 100

ps.ramp(0, 50, 10, 0.8)
ps.close()
