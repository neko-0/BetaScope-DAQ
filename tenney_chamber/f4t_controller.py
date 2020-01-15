import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)

import socket
import time
import multiprocessing as mp
from pymodbus.client.sync import ModbusTcpClient


class F4T_Controller:
    def __init__(self, ip_address="192.168.1.13", port=5025):

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip_address, port))
            scpi_command = "*IDN?".encode()
            self.sock.sendall(scpi_command)
            self.name = self.sock.recv(1024).decode().split("\n")[0]
            self.is_opened = True
        except Exception as e:
            self.sock = None
            self.name = None
            self.is_opened = False
            log.critical("fail apon connection. Catch {}".format(e))

        self.ipAddr = ip_address
        log.info(
            "You are connected to: ({device}) through {ipAddr}::SOCKET ".format(
                device=self.name, ipAddr=self.ipAddr
            )
        )

        try:
            self._modbus = ModbusTcpClient(self.ipAddr)
            self._modbus.connect()
            self._modbus_connected = True
        except:
            self._modbus = None
            self._modbus_connected = False
            pass

        self._control_loop_register = (
            2730  # this is the 1st loop, next loop is 2730+(n-1)*160
        )
        self._control_loop_mode = {"off": 62, "auto": 10, "manual": 54}

        self._set_default()

    def _set_default(self):
        if self.is_opened and self._modbus_connected:
            self._modbus.write_register(self._control_loop_register, 10)
            self._modbus.write_register(self._control_loop_register + 160, 54)
            self.set_purge_air("ON")

    def turnOFF(self):
        self._modbus.write_register(self._control_loop_register, 62)
        self._modbus.write_register(self._control_loop_register + 160, 62)
        self.set_purge_air("OFF")

    def set_purge_air(self, switch="ON"):
        self.sock.sendall(":OUTP5:STAT {mode}".format(mode=switch).encode())
        self.sock.recv(1024).decode()

    def set_temperature(self, value):
        scpi_command = ":SOURCE:CLOOP1:SPOINT {}".format(value)
        self.sock.sendall(scpi_command.encode())
        log.info("Temperature is set to %s" % value)

    def set_humidity(self, value):
        scpi_command = ":SOURCE:CLOOP2:SPOINT {}".format(value)
        self.sock.sendall(scpi_command.encode())
        log.info("Humidity is set to %s" % value)

    def get_temperature(self):
        scpi_command_get_temp = ":SOURCE:CLOOP1:PVALUE?"
        self.sock.sendall(scpi_command_get_temp.encode())
        try:
            tempValue_str = self.sock.recv(1024).decode()
        # except socket.error as (code, msg):
        except:
            # while code != errno.EINTR:
            #    return -273.0
            return -273.0

        tempValue_str = tempValue_str.split("\n")[0]
        if tempValue_str == "":
            tempValue_str = -273.0

        try:
            tempValue = float(tempValue_str)
            return tempValue
        except:
            info.warning("cannot get numerical value or conversion fail because of: {}".format(tempValue_str))
            return -273.0

    def get_humidity(self):
        scpi_command_get_humi = ":SOURCE:CLOOP2:PVALUE?"
        self.sock.sendall(scpi_command_get_humi.encode())

        try:
            humiValue = self.sock.recv(1024).decode()
        # except socket.error as (code, msg):
        except:
            # while code != errno.EINTR:
            # return -1.0
            return -1.0

        humiValue = humiValue.split("\n")[0]
        return float(humiValue)

    def check_temperature(self, value, err=1.5):
        while abs(self.get_temperature() - float(value)) >= err:
            time.sleep(5)
            continue

    wait_temperature = check_temperature  # alias function call.

    def temperature_ramp_rate(self, action, mode, value=""):
        """
        param action: read or write ramp rate from the temperature loop. Accept parameter like "set", "write", "get", "read"
        param mode: mode can be ramp scale or ramp rate. Accept "scale" or "rate"
        param value: ramp rate. Accept numerical value and "HOURS" or "MINUTES"
        """

        scpi_command = ":SOURCE:CLOOP1:{mode}{val}"
        if "set" in action or "write" in action:
            if "scale" in mode:
                if not value:
                    value = "MINUTES"
                scpi_command = scpi_command.format(mode="RSCAle ", val=value)
                self.sock.sendall(scpi_command.encode())
            if "rate" in mode:
                if not value:
                    value = 10
                scpi_command = scpi_command.format(mode="RTIME ", val=value)
                self.sock.sendall(scpi_command.encode())
        elif "get" in action or "read" in action:
            if "scale" in mode:
                scpi_command = scpi_command.format(mode="RSCAle?", val="")
                self.sock.sendall(scpi_command.encode())
                log.info(self.sock.recv(1024).decode())
            if "rate" in mode:
                scpi_command = scpi_command.format(mode="RTIME?", val="")
                self.sock.sendall(scpi_command.encode())
                log.info(self.sock.recv(1024).decode())
        else:
            log.critical("Invalid parameter!")

    def log_temp_humi_to_file(
        self, output_name="temp_humi.txt", duration=3600 * 10, show_plot=True
    ):
        output_name = "start_time_{}_{}".format(int(time.time()), output_name)
        output = open(output_name, "w")
        output.write("timestamp, temp, humi, \n")
        _start_time = time.time()
        _end_time = _start_time + duration

        temperature_plot = ""
        humidity_plot = ""
        proc_list = []

        if show_plot:
            from stas_plot_tool import generic_plot

            temperature_plot = generic_plot.Generic_Plot("Time", "Temperature")
            humidity_plot = generic_plot.Generic_Plot("Time", "Humidity")

            tempPlot_proc = mp.Process(target=temperature_plot.draw, args=(1,))
            tempPlot_proc.start()
            proc_list.append(tempPlot_proc)

            humiPlot_proc = mp.Process(target=humidity_plot.draw, args=(2,))
            humiPlot_proc.start()
            proc_list.append(humiPlot_proc)

        while True:
            current_time = time.time()
            if current_time >= _end_time:
                break
            else:
                tempValue = self.get_temperature()
                humiValue = self.get_humidity()
                if tempValue <= -273.0:
                    continue
                if humiValue <= -1.0:
                    continue
                output.write("{}, {}, {}\n".format(current_time, tempValue, humiValue))
                # log.info("%s, %s, %s\n"%(current_time, tempValue, humiValue) )
                output.flush()
                if show_plot:
                    temperature_plot.updateValue(current_time, tempValue)
                    humidity_plot.updateValue(current_time, humiValue)
                time.sleep(1)
        output.close()
        if not proc_list:
            pass
        else:
            for item in proc_list:
                item.join()
