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
        self.name = self.config_file.ps_setting.name
        log.info("power supply ({}) retrieved from config.".format(self.name))

        if "caen" in self.name.lower():
            self.PowerSupply = SimpleCaenPowerSupply()
            self.PowerSupply.InitSetup(
                self.config_file.ps_setting.software_compliance / 2.0,
                self.config_file.ps_setting.software_compliance / 5.0,
            )
        elif "keithley" in self.name.lower():
            self.PowerSupply = Keithley()
            self.PowerSupply.InitSetup()
        else:
            log.critical("Cannot find power supply {}".format(self.name))

        log.info("setting method alias")
        self.Enable_Channel = self.PowerSupply.Enbale_Channel
        self.SetVoltage = self.PowerSupply.SetVoltage
        self.ConfirmVoltage = self.PowerSupply.ConfirmVoltage
        self.VoltageReader = self.PowerSupply.VoltageReader
        self.CurrentReader = self.PowerSupply.CurrentReader
        self.Close = self.PowerSupply.Close

        log.info(" setup initialing")
        for ch in self.config_file.ps_setting.enable_channels:
            self.Enable_Channel(ch, "ON")
