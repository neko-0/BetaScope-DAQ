"""
Keithley TSP? command wrapper
"""
import logging

logging.basicConfig()
log = logging.getLogger(__name__)

import socket
import time
import numpy as np


class SockConnection(object):
    def __init__(self, ip_address="192.168.1.13", port=5025):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("192.168.1.13", 5025))
        self.termination = "\n"
        self.sock.settimeout(5)

    def write(self, input):
        # super(socket.socket, self).sendall( input+termination )
        self.sock.sendall(input + self.termination)

    def read(self):
        try:
            data = self.sock.recv(1024)
        except Exception as e:
            print(e)
            data = self.read()
        data = data.split("\n")[0]
        return data

    def query(self, input):
        # super(Sock, self).sendall( input )
        self.write(input)
        # return super(socket.socket, self).recv(1024)
        return self.read()

    def close(self):
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *argv):
        self.close()


class Connector(object):
    @staticmethod
    def query(input, ip_address="192.168.1.13"):
        with SockConnection(ip_address) as inst:
            return inst.query(input)

    @staticmethod
    def write(input, ip_address="192.168.1.13"):
        with SockConnection(ip_address) as inst:
            return inst.write(input)


class AttributeDescriptor(object):
    def __init__(self, name, parent_class, ip):
        self.name = name
        self.parent_class = parent_class
        self.ip = ip

    def __get__(self, instance, owner):
        # print(instance.__class__.__qualname__)
        command = "print({}.{}.{})".format(
            self.parent_class, instance.__class__.__name__, self.name
        )
        log.info("getting => {}".format(command))
        return Connector.query(command, self.ip)

    def __set__(self, instance, value):
        command = "{}.{}.{} = {}".format(
            self.parent_class, instance.__class__.__name__, self.name, value
        )
        Connector.write(command, self.ip)


class OptionDescriptor(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        return "{}.{}".format(instance.__class__.__name__, self.name)


class FunctionDescriptor(object):
    def __init__(self, name, parent_class, ip):
        self.name = name
        self.parent_class = parent_class
        self.ip = ip

    def __get__(self, instance, owner):
        # print(instance.__class__.__qualname__)
        if self.parent_class:
            command = "print({}.{}.{}())".format(
                self.parent_class, instance.__class__.__name__, self.name
            )
        else:
            command = "print({}.{}())".format(instance.__class__.__name__, self.name)
        log.info("getting => {}".format(command))
        return Connector.query(command, self.ip)


class MetaClass(object):
    def __init__(self, name, ip):
        self.__class__.__name__ = name
        self.ip = ip

    def create_attr(self, name):
        return AttributeDescriptor(name, self.__class__.__name__, self.ip)

    def create_func(self, name):
        return FunctionDescriptor(name, self.__class__.__name__, self.ip)

    def create_cfunc(self, name):
        return FunctionDescriptor(name, "", self.ip)

    def create_opt(self, name):
        return OptionDescriptor(name)


class Base(object):
    def __init__(self, name, ip):
        self.meta_class = MetaClass(name, ip)

    def __getattribute__(self, name):
        my_attr = object.__getattribute__(self, name)
        if (
            isinstance(my_attr, AttributeDescriptor)
            or isinstance(my_attr, FunctionDescriptor)
            or isinstance(my_attr, OptionDescriptor)
        ):
            return my_attr.__get__(self, my_attr)
        else:
            return my_attr

    def __setattr__(self, name, value):
        if value is None:
            pass
        else:
            if not name in self.__dict__:
                self.__dict__[name] = value
            else:
                if isinstance(self.__dict__[name], AttributeDescriptor):
                    self.__dict__[name].__set__(self, value)
                else:
                    self.__dict__[name] = value

    def set_func(self, name):
        self.__setattr__("_" + name, self.meta_class.create_func(name))

        def request():
            return self.__getattribute__("_" + name)

        return request

    def set_cfunc(self, name):
        self.__setattr__("_" + name, self.meta_class.create_cfunc(name))

        def request():
            return self.__getattribute__("_" + name)

        return request

    def set_attr(self, name):
        self.__setattr__(name, self.meta_class.create_attr(name))

    def set_opt(self, name):
        self.__setattr__(name, self.meta_class.create_opt(name))


class Smua(Base):
    class Source(Base):
        def __init__(self, name, ip):
            super(Smua.Source, self).__init__(name, ip)

            self.__class__.__name__ = "source"

            self.levelv = self.set_attr("levelv")
            self.output = self.set_attr("output")
            self.delay = self.set_attr("delay")

    class Measure(Base):
        def __init__(self, name, ip):
            self.__class__.__name__ = "measure"
            super(Smua.Measure, self).__init__(name, ip)

            self.iv = self.set_func("iv")
            self.i = self.set_func("i")
            self.v = self.set_func("v")

            self.autorangei = self.set_attr("autorangei")

    class Nvbuffer1(Base):
        def __init__(self, name, ip):
            self.__class__.__name__ = "nvbuffer1"
            super(Smua.Nvbuffer1, self).__init__(name, ip)
            self.clear = self.set_func("clear")

    def __init__(self, ip):
        self.__class__.__name__ = "smua"
        super(Smua, self).__init__(self.__class__.__name__, ip)
        self.ip = ip
        self.source = self.Source(self.__class__.__name__, ip)
        self.measure = self.Measure(self.__class__.__name__, ip)
        self.nvbuffer1 = self.Nvbuffer1(self.__class__.__name__, ip)
        self.OUTPUT_ON = self.set_opt("OUTPUT_ON")
        self.OUTPUT_OFF = self.set_opt("OUTPUT_OFF")
        self.AUTORANGE_ON = self.set_opt("AUTORANGE_ON")
        self.reset = self.set_cfunc("reset")


class Display(Base):
    class Trigger(Base):
        def __init__(self, name, ip):
            self.__class__.__name__ = "trigger"
            super(Display.Trigger, self).__init__(name, ip)
            self.clear = self.set_func("clear")

    def __init__(self, ip):
        self.__class__.__name__ = "display"
        super(Display, self).__init__(self.__class__.__name__, ip)
        self.ip = ip
        self.trigger = self.Trigger(self.__class__.__name__, ip)
        self.clear = self.set_cfunc("clear")


# ===============================================================================
# ===============================================================================


class Keithley(object):
    def __init__(self, ip="192.168.1.13"):
        Connector.write("*RST", ip)
        self.smua = Smua(ip)
        self.display = Display(ip)
        self.smua.source.output = self.smua.OUTPUT_ON
        self.smua.source.delay = 1
        self.smua.measure.autorangei = self.smua.AUTORANGE_ON

    def close(self, force=False):
        if force:
            Connector.write("*RST")
        else:
            self.smua.source.delay = 0
            current_volt = int(float(self.get_v().split("\n")[0]))
            print("current voltage {} start ramping down".format(current_volt))
            self.ramp(current_volt, 0, step=1, delay=0.1, fast=True)

    def get_v(self):
        return self.smua.source.levelv

    def ramp(self, start, end, step=5, delay=1, fast=False):
        if start < end:
            volts = np.arange(start, end, step)
        else:
            volts = np.arange(start, end, -1 * step)
        volts = np.insert(volts, 0, start)
        volts = np.append(volts, end)
        log.info(volts)
        if fast:
            self.smua.nvbuffer1.clear()
            for volt in volts:
                self.smua.source.levelv = volt
                time.sleep(delay)
            return 0
        for volt in volts:
            self.smua.source.levelv = volt
            time.sleep(delay)
            current = self.smua.measure.i()
            voltage = self.smua.measure.v()
            self.smua.nvbuffer1.clear()
            # self.display.trigger.clear()
            print("{} {}".format(current, voltage))
