import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)


from .caen_ps.CAEN_PS import SimpleCaenPowerSupply
from .keithley.core import Keithley


class PowerSupplyProducer:
    def __init__(self, configFile):
        # configParser = DAQConfig()
        # self._config = configParser.ReadDAQConfig( configFileName )
        self.config_file = configFile
        self.PowerSupply = ""

        self.ConfirmVoltage = ""
        self.SetVoltage = ""
        self.CurrentReader = ""
        self.VoltageReader = ""
        self.Close = ""

        if "caen" in self.config_file.ps_setting.name:
            log.info("Caen power supply is produced")
            self.PowerSupply = SimpleCaenPowerSupply()
            self.PowerSupply.Set_Compliance(
                self.config_file.ps_setting.software_compliance / 2.0,
                self.config_file.ps_setting.software_compliance / 5.0,
            )
            for ch in self.config_file.ps_setting.enable_channels:
                self.PowerSupply.channel_switch(ch, "ON")
                voltage_now = self.PowerSupply.voltage_monitor_value(ch, 0)
                self.PowerSupply.set_voltage(ch, voltage_now)
            # self.PowerSupply.set_voltage( self._config.PSTriggerChannel, self._config.TriggerVoltage )

            def Produce_ConfirmVoltage():
                def ConfirmVoltage(PS_Channel, TargetVoltage):
                    return self.PowerSupply.confirm_voltage(PS_Channel, TargetVoltage)

                return ConfirmVoltage

            self.ConfirmVoltage = Produce_ConfirmVoltage()

            def Produce_SetVoltage():
                def SetVoltage(PS_Channel, TargetVoltage, maxI=1.2):
                    self.PowerSupply.set_voltage(PS_Channel, TargetVoltage, maxI)

                return SetVoltage

            self.SetVoltage = Produce_SetVoltage()

            def Produce_CurrentReader():
                def CurrentReader(PS_Channel):
                    return self.PowerSupply.current_monitor_value(PS_Channel, 0)

                return CurrentReader

            self.CurrentReader = Produce_CurrentReader()

            def Produce_VoltageReader():
                def VoltageReader(PS_Channel):
                    return self.PowerSupply.voltage_monitor_value(PS_Channel, 0)

                return VoltageReader

            self.VoltageReader = Produce_VoltageReader()

            def Produce_Close():
                def Close():
                    return self.PowerSupply.close("ALL")

                return Close

            self.Close = Produce_Close()

        elif "keithley" in self.config_file.ps_setting.name:
            log.info("Keithley power supply is being produced")

            self.PowerSupply = Keithley()

            def Produce_ConfirmVoltage():
                def ConfirmVoltage(channel, target_volts):
                    return self.PowerSupply.confirm_voltage(target_volts)

                return ConfirmVoltage

            self.ConfirmVoltage = Produce_ConfirmVoltage()

            def Produce_SetVoltage():
                def SetVoltage(PS_Channel, TargetVoltage, maxI=1.2):
                    self.PowerSupply.set_voltage(TargetVoltage)

                return SetVoltage

            self.SetVoltage = Produce_SetVoltage()

            def Produce_CurrentReader():
                def CurrentReader(PS_Channel):
                    return self.PowerSupply.current_monitor_value()

                return CurrentReader

            self.CurrentReader = Produce_CurrentReader()

            def Produce_VoltageReader():
                def VoltageReader(PS_Channel):
                    return self.PowerSupply.voltage_monitor_value()

                return VoltageReader

            self.VoltageReader = Produce_VoltageReader()

            def Produce_Close():
                def Close():
                    return self.PowerSupply.close()

                return Close

            self.Close = Produce_Close()
