'''
class for agelient e3646a power supply
'''

import pyvisa as visa

class E3646A_PS(object):

    def __init__(self, addr="GPIB0::1::INSTR"):
        rm = visa.ResourceManager("@py")
        try:
            self.inst = rm.open_resource(addr)
            self.is_opened = True
            self.inst.timeout = 10000
            self.inst.read_termination = "\n"
        except Exception as e:
            print("catch {e}".format(e=e) )
            self.is_opened = False
            self.inst = ""

        if self.is_opened:
            self.device_name = self.inst.query("*IDN?").split(self.inst.read_termination)[0]
            print("connected to {device} through {addr}".format(device=self.device_name, addr=addr) )


    def read_voltageCurrent(self, ch): #only ch1 and ch2

        if not self.inst:
            voltage = 10e11
            current = 10e11
            return (voltage, current)

        self.inst.write("INST:NSEL {ch}".format(ch=ch) )
        try:
            voltage = float(self.inst.query("MEAS:VOLT?").split("\n")[0] )
            current = float(self.inst.query("MEAS:CURR?").split("\n")[0] )
        except Exception as e:
            print("{device} has problem when query, set default values".format(device=self.device_name) )
            voltage = 10e11
            current = 10e11
        return (voltage, current)
