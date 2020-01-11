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
        self.scope = ""
        self.name = None

        if "lecroy" in self.config_file.scope_setting.name:
            log.info("Lecroy scope is being produced.")
            self.name = self.config_file.scope_setting.name

            self.scope = LecroyScope(self.config_file.scope_setting.ip)
            self.scope.set_read_byte(
                1048
            )  # don't konw why read_raw() needs input. It wasn't like this before 2019/9/10

            log.info("Setting up scope trigger and power supply.")
            self.scope.Arm_trigger(
                self.config_file.trigger_setting.scope_ch,
                self.config_file.trigger_setting.threshold_type,
                self.config_file.trigger_setting.scope_threshold,
                self.config_file.trigger_setting.threshold_type,
            )

            log.info("Enabling scope channels...")
            for ch in self.config_file.scope_setting.enable_channels:
                self.scope.Set_Channel_Display(ch, "ON")

            log.info("Producing scope methods...")

            def Produce_GetWaveform():
                def GetWaveform(ChannelList, mode="binary", seq_mode=True):
                    data = self.scope.Get_Waveform(ChannelList, mode, seq_mode)
                    return data

                return GetWaveform

            self.GetWaveform = Produce_GetWaveform()

            def Produce_WaitTrigger():
                def WaitTrigger(timeout=0.0, trigger_scan=None):
                    status = self.scope.Wait_For_Next_Trigger(timeout, trigger_scan)
                    return status

                return WaitTrigger

            self.WaitForTrigger = Produce_WaitTrigger()

            def Produce_SetTrigger():
                def SetTrigger(Channel, Threshold, Polarity, Mode):
                    self.scope.Arm_trigger(Channel, Polarity, Threshold, Mode)

                return SetTrigger

            self.SetTrigger = Produce_SetTrigger()

        if "keysight" in self.config_file.scope_setting.name:
            log.info("Keysight scope is being produced.")
            self.name = self.config_file.scope_setting.name

            self.scope = KeysightScope(self.config_file.scope_setting.ip)
            self.scope.arm_trigger(
                self.config_file.trigger_setting.scope_ch,
                self.config_file.trigger_setting.threshold_type,
                self.config_file.trigger_setting.scope_threshold,
                self.config_file.trigger_setting.threshold_type,
            )
            self.scope.acquisition_setting()

            def Produce_SetTrigger():
                def SetTrigger(Channel, Threshold, Polarity, Mode):
                    self.scope.arm_trigger(Channel, Polarity, Threshold, Mode)
                    self.scope.acquisition_setting()

                return SetTrigger

            self.SetTrigger = Produce_SetTrigger()

            def Produce_WaitTrigger():
                def WaitTrigger(timeout=0.0):
                    status = self.scope.waiting_for_next_wave()
                    return status

                return WaitTrigger

            self.WaitForTrigger = Produce_WaitTrigger()

            def Produce_GetWaveform():
                def GetWaveform(ChannelList, mode="ascii", seq_mode=True):
                    data = self.scope.get_ascii_waveform_remote(ChannelList)
                    return data

                return GetWaveform

            self.GetWaveform = Produce_GetWaveform()

    def _query(self, cmd):
        return self.scope.inst.query(cmd)
