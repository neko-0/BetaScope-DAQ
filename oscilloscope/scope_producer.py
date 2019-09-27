'''
class for producing scope and scope methods.
'''
from lecroy_wavepro.Lecroy import LecroyScope
from keysight_infiniium_s.keysight_infiniium_s import KeysightScope


class ScopeProducer:
    def __init__(self, configFile ):
        #self._config = DAQConfig()
        #self._config.ReadDAQConfig( configFileName )
        self._config = configFile
        self.Scope = ""
        self.name = None

        if "lecroy" in self._config.ScopeName:
            self.name = "lecroy"
            print("Lecroy scope is produced.")
            self.Scope = LecroyScope( self._config.ScopeIP )
            self.Scope.set_read_byte(1048) #don't konw why read_raw() needs input. It wasn't like this before 2019/9/10
            print("Setting up scope trigger and power supply.")
            self.Scope.Arm_trigger( self._config.TriggerSetting[0], self._config.TriggerSetting[1], self._config.TriggerSetting[2], self._config.TriggerSetting[3] )
            print("Enabling scope channels...")
            for ch in self._config.EnableChannelList:
                self.Scope.Set_Channel_Display(ch, "ON")

            print("Producing scope methods...")

            def Produce_GetWaveform():
                def GetWaveform( ChannelList, mode="binary", seq_mode=True):
                    data = self.Scope.Get_Waveform(ChannelList, mode, seq_mode)
                    return data
                return GetWaveform
            self.GetWaveform = Produce_GetWaveform()

            def Produce_WaitTrigger():
                def WaitTrigger(timeout=0.0, trigger_scan=None):
                    status = self.Scope.Wait_For_Next_Trigger(timeout,trigger_scan)
                    return status
                return WaitTrigger
            self.WaitForTrigger = Produce_WaitTrigger()

            def Produce_SetTrigger():
                def SetTrigger(Channel, Threshold, Polarity, Mode):
                    self.Scope.Arm_trigger(Channel, Polarity, Threshold, Mode)
                return SetTrigger
            self.SetTrigger = Produce_SetTrigger()

        if "keysight" in self._config.ScopeName:
            self.name = "keysight"
            print("keysight scope is produced.")
            self.Scope = KeysightScope( self._config.ScopeIP )
            self.Scope.arm_trigger(self._config.TriggerSetting[0], self._config.TriggerSetting[1], self._config.TriggerSetting[2], self._config.TriggerSetting[3])
            self.Scope.acquisition_setting()


            def Produce_SetTrigger():
                def SetTrigger(Channel, Threshold, Polarity, Mode):
                    self.Scope.arm_trigger(Channel, Polarity, Threshold, Mode)
                    self.Scope.acquisition_setting()
                return SetTrigger
            self.SetTrigger = Produce_SetTrigger()

            def Produce_WaitTrigger():
                def WaitTrigger(timeout=0.0):
                    status = self.Scope.waiting_for_next_wave()
                    return status
                return WaitTrigger
            self.WaitForTrigger = Produce_WaitTrigger()

            def Produce_GetWaveform():
                def GetWaveform( ChannelList, mode="ascii", seq_mode=True):
                    data = self.Scope.get_ascii_waveform_remote(ChannelList)
                    return data
                return GetWaveform
            self.GetWaveform = Produce_GetWaveform()


    def _query(self, cmd):
        return self.Scope.inst.query(cmd)
