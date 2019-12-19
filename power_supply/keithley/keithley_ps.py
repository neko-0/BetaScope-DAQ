import socket
import pyvisa as visa


class Keithley:
    def __init__(self, ip_address="192.168.1.13", port=5025):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("192.168.1.13", 5025))
        self.termination = "\n"

    def write(self, input):
        # super(socket.socket, self).sendall( input+termination )
        self.sock.sendall(input + self.termination)

    def read(self):
        return self.sock.recv(1024)

    def query(self, input):
        # super(Sock, self).sendall( input )
        self.write(input)
        # return super(socket.socket, self).recv(1024)
        return self.read()


ps = Keithley()
# sock.connect( ("192.168.0.2", 5025) )
# feedback = ps.query("*IDN?")
# print(feedback)
ps.write("*RST")
ps.write("beeper.enable = beeper.ON")
# ps.write("smua.source.delay = 1")
# ps.write("smua.source.output = smua.OUTPUT_ON")
# ps.write("smua.trigger.source.linearv(50,150,11)")
# ps.write("smua.trigger.source.action = smua.ENABLE")
# ps.write("smua.nvbuffer1.clear()")
# ps.write("smua.trigger.initiate()")
ps.write("smua.source.output = smua.OUTPUT_ON")
ps.write("smua.source.levelv = 100")
d = ps.write("print(smua.measure.v())")
print("your {}".format(d))
print("hi {}".format(ps.read()))
ps.write("*RST")
