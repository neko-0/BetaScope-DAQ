import socket
import pyvisa as visa


class Sock:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("192.168.0.2", 5025))
        self.termination = "\n"

    def send_all(self, input):
        # super(socket.socket, self).sendall( input+termination )
        self.sock.sendall(input + self.termination)

    def query(self, input):
        # super(Sock, self).sendall( input )
        self.send_all(input)
        # return super(socket.socket, self).recv(1024)
        return self.sock.recv(1024)


sock = Sock()
# sock.connect( ("192.168.0.2", 5025) )
feedback = sock.query("*IDN?")
print(feedback)
