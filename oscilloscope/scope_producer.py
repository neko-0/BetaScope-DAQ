"""
class for producing scope and scope methods.
"""
import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)

from .lecroy_wavepro.Lecroy import LecroyScope
from .keysight_infiniium_s.keysight_infiniium_s import KeysightScope


class ScopeProducer:
    def __init__(self, config_file):
        # self._config = DAQConfig()
        # self._config.ReadDAQConfig( configFileName )
        self.config_file = config_file
        self.name = self.config_file.scope_setting.name
        log.info("Scope ({}) retrieved from config.".format(self.name))
        log.info("Creating instance")
        if "lecroy" in self.name.lower():
            self.scope = LecroyScope(self.config_file.scope_setting.ip)
            self.scope.InitSetup(
                self.config_file.trigger_setting.scope_ch,
                self.config_file.trigger_setting.threshold_type,
                self.config_file.trigger_setting.scope_threshold,
                self.config_file.trigger_setting.threshold_type,
            )
        elif "keysight" in self.name.lower():
            self.scope = KeysightScope(self.config_file.scope_setting.ip)
            self.scope.InitSetup(
                self.config_file.trigger_setting.scope_ch,
                self.config_file.trigger_setting.threshold_type,
                self.config_file.trigger_setting.scope_threshold,
                self.config_file.trigger_setting.threshold_type,
            )
        else:
            log.critical("cannot find definition of scope {}".format(self.name))
            self.scope = None

        if self.scope:
            log.info("Setting scope method alias.")
            self.GetWaveform = self.scope.GetWaveform
            self.SetTrigger = self.scope.SetTrigger
            self.WaitTrigger = self.scope.WaitTrigger
            self.Enable_Channel = self.scope.Enable_Channel

            log.info("Enabling scope channels...")
            for ch in self.config_file.scope_setting.enable_channels:
                self.Enable_Channel(ch, "ON")

    def _query(self, cmd):
        return self.scope.inst.query(cmd)
