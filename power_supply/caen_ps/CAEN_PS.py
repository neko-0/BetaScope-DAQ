import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)

import pyvisa as visa
import time
import sys
import signal
import os

import general.general as general

xx = "02"


class SimpleCaenPowerSupply(object):
    def __init__(self):

        self.__status_bit_meaning = {
            0: ["ON", "On-Off switch"],
            1: ["RUP", "Channel Ramp UP"],
            2: ["RDW", "Channel Ramp DOWN"],
            3: ["OVC", "Current > ISET."],
            4: ["OVV", "Voltage > VSET."],
            5: ["UNV", "Voltage < VSET."],
            6: ["MAXV", "Hitting Max voltage!"],
            7: ["TRIP", "Channel tripped!!!"],
            8: ["OVP", "Output power > Max."],
            9: ["OVT", "Temperature > 105C."],
            10: ["DIS", "Ch disabled (REMOTE Mode and Switch on OFF position)"],
            11: ["KILL", "Ch in KILL via front panel."],
            12: ["ILK", "CH in INTERLOCK via front panel"],
            13: ["NOCAL", "Calibration Error"],
            14: ["N.C", "Reserved bit"],
            15: ["N.C", "Reserved bit"],
        }

        global xx
        rm = visa.ResourceManager("@py")
        resources = rm.list_resources()
        log.info(resources)
        for res in resources:
            if "ttyACM0" in res:
                self.inst = rm.open_resource(res)
                self.inst.clear()
        # self.inst.write_termination("\r\n")
        # self.inst.read_termination("\r\n")

        idn = self.inst.query("$BD:" + xx + ",CMD:MON,PAR:BDNAME")
        remote_status = self.check_remote_status()
        if "DT1471ET" in idn:
            log.info("Connected to CAEN Power Supply.")
        else:
            log.critical("Power supply is not available.")
        log.info("Checking remote status...")
        if "LOCAL" in remote_status:
            log.critical(
                "Remote access is closed, Press ENTER to contitue."
            )
            input()
        else:
            log.info("Remote access is opened.")

        self.complicance = 1.0  # uA
        self.delta_I = 0.5  # uA
        self.I_value = 0.0  # uA
        self.initial_I = 1
        self.timeout = 100000

        self.progress = general.progress(2)

    def simple_query(self, comm, channel=-1, delay=0.5):
        time.sleep(delay)
        command = ""
        output = ""
        if channel == -1:
            command = "$BD:" + xx + ",CMD:MON,PAR:{}".format(comm)
        else:
            command = "$BD:" + xx + ",CMD:MON,CH:{},PAR:{}".format(channel, comm)
        output = self.inst.query(command)
        # print(output)
        output = output.split(",")
        # print(output)
        # if channel == -1:
        output = output[2].split(":")
        # else:
        #    output = output[2].split(":")
        output = output[1]
        return output

    def simple_set(self, channel, par, value):
        command = (
            "$BD:" + xx + ",CMD:SET,CH:{},PAR:{},VAL:{}".format(channel, par, value)
        )
        self.inst.query(command)

    def check_remote_status(self):
        return self.simple_query("BDCTR")

    def channel_switch(self, channel, status):
        self.inst.query("$BD:" + xx + ",CMD:SET,CH:{},PAR:{}".format(channel, status))

    def simple_reset(self, channel):
        self.channel_switch(channel, "OFF")
        VMON = self.simple_query("VMON", channel)
        # print(VMON)
        while float(VMON) > 0.1:
            VMON = self.simple_query("VMON", channel)
            log.info("Voltage : {}".format(VMON))

    def set_voltage(self, channel, value, currentMax=1.2):
        log.info("Set channel {} voltage to {}".format(channel, value))
        # self.simple_set(channel, "VSET", value)
        VMON = self.simple_query("VMON", channel)
        self.simple_set(channel, "VSET", value)
        log.info("VMON: {}".format(VMON))
        # print(self.simple_query("VMON", channel))
        timeout_counter = 1000
        counter = 0
        current_limit = float(self.simple_query("ISET", channel))
        current_incre_step = 2.0
        while abs(float(VMON) - value) > 1.0:
            # time.sleep(5)
            self.progress(
                "Ramping voltage... {}".format(VMON.split()[0]),
                "Set Voltage:{}".format(value),
            )
            VMON = self.simple_query("VMON", channel)
            # time.sleep(3)
            status = self.read_channel_status_bit(channel)
            if self.decodeStatusBit(status, 3):
                current_limit += current_incre_step
                if current_limit < currentMax:
                    pass
                else:
                    current_limit = currentMax
                log.critical(
                    "Tripped! increasing current limit to {}".format(current_limit)
                )
                # self.set_channel_status_bit(channel, "00001")
                time.sleep(30)
                self.channel_switch(channel, "ON")
                self.simple_set(channel, "ISET", current_limit)
                log.info("Restart rampnig")
            if counter == timeout_counter:
                return 0
                log.critical(
                    "Timeout: Maximum counter reached {}".format(timeout_counter)
                )
                break
        log.info(
            "\nFinished, the voltage now is {}\n".format(
                self.simple_query("VMON", channel)
            )
        )
        return 1

    def set_voltage_Q(self, channel, value, currentMax=1.2):
        VMON = self.simple_query("VMON", channel)
        self.simple_set(channel, "VSET", value)
        timeout_counter = 5000
        counter = 0
        current_limit = float(self.simple_query("IMAX", channel))
        current_incre_step = 1.0
        while abs(float(VMON) - value) > 1.0:
            VMON = self.simple_query("VMON", channel)
            counter += 1
            status = self.read_channel_status_bit(channel)
            if self.decodeStatusBit(status, 3):
                current_limit += current_incre_step
                if current_limit < currentMax:
                    pass
                else:
                    current_limit = currentMax
                log.critical(
                    "Tripped! increasing current limit to {}".format(current_limit)
                )
                self.set_channel_status_bit(channel, 1)

            if counter == timeout_counter:
                log.critical(
                    "Timeout: Maximum counter reached {}".format(timeout_counter)
                )
                break

    def voltage_monitor(self, channel, delay):
        local_VMON = 999
        local_VMON = self.simple_query("VMON", channel, delay)
        log.info("Monitoring Voltage: {}".format(local_VMON))
        return local_VMON

    def voltage_monitor_value(self, channel, delay):
        local_VMON = self.simple_query("VMON", channel, delay)
        return float(local_VMON)

    def current_monitor(self, channel, delay):
        local_IMON = self.simple_query("IMON", channel, delay)
        log.info("Monitoring Current: {}".format(local_IMON))
        return local_IMON

    def current_monitor_value(self, channel, delay):
        local_IMON = self.simple_query("IMON", channel, delay)
        return float(local_IMON)

    def confirm_voltage(self, channel, TargetVoltage, delay=5):
        voltage = self.simple_query("VMON", channel, delay)
        if abs(float(voltage) - TargetVoltage) < 1.5:
            return True
        else:
            return False

    def read_channel_status_bit(self, channel):
        stat = self.simple_query("STAT", channel)
        stat = stat.split("\r")[0]
        return stat

    def set_channel_status_bit(self, channel, value):
        self.simple_set(channel, "STAT", value)

    def reset_channel(self, channel):
        log.info("Resetting channel {}. Power off".format(channel))
        VMON = self.simple_query("VMON", channel)
        self.channel_switch(channel, "OFF")
        while abs(float(VMON) - 0.0) > 1.0:
            VMON = self.simple_query("VMON", channel, 2)
            log.info("Monitoring Voltage: {}".format(VMON))
        log.info("Finished. You need to re-power the channel")

    def Get_Voltage_Current_Pair(self, channel):
        """
        param channel := reading channel
        return the voltage and current as a 2D list.
        """
        VMON = self.voltage_monitor_value(channel, 0)
        IMON = self.current_monitor_value(channel, 0)

        return [VMON, IMON]

    def Set_Compliance(self, complicance, rate_of_change):
        self.complicance = complicance  # uA
        self.delta_I = rate_of_change  # uA

    def Check_Compliacne(self, channel, iValue):
        if self.initial_I == 1:
            self.I_value = iValue
            self.initial_I = 0
        else:
            pass
        if iValue <= self.complicance:
            self.I_value = iValue
        else:
            dI = iValue - self.I_value
            if dI >= self.delta_I:
                # print(self.I_value)
                log.warning("Current Warning: Rapid Increase")
                log.info("Shutdown Channel: {}".format(channel))
                self.close(channel)
                return 1
        return 0

    def decodeStatusBit(self, status, bit):
        """
        decoding the channel status bit

        param status := is the raw input bit,
        param bit := the bit you want to check against.
        """
        status_bits = format(int(status), "#016b")
        if bit > 15:
            log.critical("bit > max bit(15)", "y")
        else:
            if status_bits[15 - bit] == "1":
                log.warning("WARNING: %s" % self.__status_bit_meaning[bit][1], "y")
                return 1
            else:
                return 0

    # ===========================================================================
    def checkTripped(self, ch, voltage):
        # check to see if the channel is tripped
        status_bit = self.read_channel_status_bit(ch)
        tripped = self.decodeStatusBit(status_bit, 7)
        if tripped:
            self.channel_switch(ch, "ON")
            self.set_voltage_Q(ch, voltage)

    def close(self, channel):
        log.info("object calls close(). {} channels are turning off".format(channel))
        if channel == "ALL":
            self.channel_switch(0, "OFF")
            self.channel_switch(1, "OFF")
            self.channel_switch(2, "OFF")
            self.channel_switch(3, "OFF")
        elif channel == 0:
            self.channel_switch(0, "OFF")
        elif channel == 1:
            self.channel_switch(1, "OFF")
        elif channel == 2:
            self.channel_switch(2, "OFF")
        elif channel == 3:
            self.channel_switch(3, "OFF")


if __name__ == "__main__":
    log.info("testing")
    ps = SimpleCaenPowerSupply()

"""
test_power = SimpleCaenPowerSupply()
remote_status = test_power.check_remote_status()
test_power.channel_switch(0,"ON")
test_power.set_voltage(0, 100.0)
test_power.set_voltage(0, 30.0)
test_power.reset_channel(0)
test_power.reset_channel(1)
test_power.channel_switch(0,"ON")
if "REMOTE" in remote_status:
    test_power.set_voltage(0, 50.0)


input("Finished, closing power")
test_power.close(0)
"""
