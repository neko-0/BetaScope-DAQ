import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="INFO", logger=log)


from daq_setting import DAQConfigReader

from utility.file_dir import FileDir
from utility.description import CreateDescription
from utility.PI_TempSensor import PI_TempSensor

from file_io import ROOTFileOutput

from oscilloscope.scope_producer import ScopeProducer
from power_supply import PowerSupplyProducer
from power_supply import E3646A_PS

from tenney_chamber import F4T_Controller

from general import GetEditor


# import general
import socket
import gc
import datetime
import time
import subprocess
import shutil
import numpy as np


def temperature_compare(f4t, pi_sensor, target_temp, cali_wt, diff=2):
    """
    Check and calibrate temperature between f4t and a sensor that is connected to the pi.

    Args:
        f4t (obj: F4T_Controller) : F4T_Controller class instance.
        pi_sensor (obj : PI_TempSensor) : PI_TempSensor class instance.
        cali_wt (int) : temperature calibration wait time in second.
        diff (int) : required temperature difference between f4t and pi to be less than this value.
    """
    pi_temp = pi_sensor.get_temperature()
    my_target_temp = target_temp
    okay = False
    while True:
        pi_temp = pi_sensor.get_temperature()
        if okay:
            break
        if abs(pi_temp - target_temp) <= diff:
            log.info("temperature is stable now {}".format(target_temp))
            for i in range(cali_wt):
                time.sleep(1)
                if i % 60 == 0:
                    log.info("wait for checking again {}/{}".format(i, cali_wt))
            if abs(pi_temp - target_temp) <= diff:
                okay = True
            else:
                continue
        else:
            log.info(
                "temperature mismatch pi:{} now and the target:{}".format(
                    pi_temp, target_temp
                )
            )
            if pi_temp < target_temp:
                my_target_temp += 1
                f4t.set_temperature(my_target_temp)
                f4t.wait_temperature(my_target_temp)
            else:
                my_target_temp -= 1
                f4t.set_temperature(my_target_temp)
                f4t.wait_temperature(my_target_temp)
            for i in range(int(cali_wt / 2)):
                time.sleep(1)
                if i % 60 == 0:
                    log.info("wait for checking again {}/{}".format(i, cali_wt))


class BetaDAQ:
    def __init__(self):
        log.info("initializing {}".format(self.__class__.__name__))
        self.config_file = DAQConfigReader.open()
        self.instruments = {
            "chamber": None,
            "scope": None,
            "hv_ps": None,
            "lv_ps": None,
            "pi_sensor": None,
        }

    # ===========================================================================
    # ===========================================================================
    def setup_dir(self):
        FileDir.setup_data_folder(
            self.config_file.config.file_setting.master_dir,
            self.config_file.config.file_setting.output_dir,
            self.config_file.config.file_setting.prefix,
            self.config_file.config.file_setting.run_number,
        )
        self.current_mon_file = open(
            FileDir.check_current_mon_file(
                FileDir.setup_current_mon_file(
                    self.config_file.config.file_setting.run_number
                )
            ),
            "w",
        )

    # ===========================================================================
    # ===========================================================================
    def create_description_file(self):
        log.warning("Create description file?[y/n]")
        yes_no = input()
        if "y" in yes_no or "Y" in yes_no:
            editor = GetEditor("gedit")
            CreateDescription(self.config_file.config.file_setting.run_number)
            subprocess.call(
                [
                    editor,
                    "Sr_Run_"
                    + str(self.config_file.config.file_setting.run_number)
                    + "_Description.ini",
                ]
            )
        else:
            pass
        shutil.copy(
            "Sr_Run_"
            + str(self.config_file.config.file_setting.run_number)
            + "_Description.ini",
            self.config_file.config.file_setting.log_dir,
        )

    # ==========================================================================
    # ==========================================================================
    def load_instruments(self):
        log.info("loading (default) instruments")
        self.instruments["pi_sensor"] = PI_TempSensor()
        if self.config_file.config.chamber_setting.name == "new_tenney":
            self.instruments["chamber"] = F4T_Controller()
        self.instruments["scope"] = ScopeProducer(self.config_file.config)
        self.instruments["hv_ps"] = PowerSupplyProducer(self.config_file.config)
        self.instruments["lv_ps"] = E3646A_PS()
        log.info("checking instruments")
        for name, inst in self.instruments.items():
            if not inst is None:
                log.info("{} looks fine.".format(name))
            else:
                log.critical("something wrong with {}".format(name))

    # ==========================================================================
    # ==========================================================================
    def waiting(self):
        log.warning(
            "Be quiet! The DAQ is sleeping now. It will be back in {nap_time} sec".format(
                nap_time=self.config_file.config.general_setting.cycle_wait_time
            )
        )
        for leftTime in np.arange(
            self.config_file.config.general_setting.cycle_wait_time, 0, -1
        ):
            time.sleep(1)
            if leftTime % 300 == 0:
                log.info(
                    "nap time remaining...{remain_time}".format(remain_time=leftTime)
                )
        log.info("\nGood Morning!\n")

    # ===========================================================================
    # ===========================================================================
    def create_output_file(self, dataFileName, dut_bias, cycle):
        outROOTFile = ROOTFileOutput(
            dataFileName, self.config_file.config.scope_setting.enable_channels
        )

        if self.instruments["chamber"].is_opened:
            outROOTFile.create_branch("temperature", "D")
            outROOTFile.create_branch("humidity", "D")

        if not self.instruments["pi_sensor"] is None:
            outROOTFile.create_branch("pi_temperature", "D")
            outROOTFile.create_branch("pi_humidity", "D")

        if "lecroy" in self.config_file.config.scope_setting.name:
            for ch in self.config_file.config.scope_setting.enable_channels:
                outROOTFile.create_branch("verScale{}".format(ch), "D")
                outROOTFile.create_branch("horScale{}".format(ch), "D")
                verScale = float(
                    self.instruments["scope"]
                    .scope._query("C{}:VDIV?".format(ch))
                    .split("VDIV ")[1]
                    .split(" ")[0]
                )
                horScale = float(
                    self.instruments["scope"]
                    .scope._query("TDIV?")
                    .split("TDIV ")[1]
                    .split(" ")[0]
                )
                log.info("Ver scale ch{}: {}".format(ch, verScale))
                log.info("Hor scale ch{}: {}".format(ch, horScale))
                outROOTFile.additional_branch["verScale{}".format(ch)][0] = verScale
                outROOTFile.additional_branch["horScale{}".format(ch)][0] = horScale

        outROOTFile.create_branch("bias", "D")
        outROOTFile.additional_branch["bias"][0] = dut_bias

        outROOTFile.create_branch("mon_dut_bias", "D")
        outROOTFile.create_branch("mon_trig_bias", "D")

        outROOTFile.create_branch("rate", "D")
        outROOTFile.create_branch("ievent", "I")
        outROOTFile.create_branch(
            "cycle", "I"
        )  # recored the (temperature or repeated msmt) cycle number.
        outROOTFile.additional_branch["cycle"][0] = cycle

        outROOTFile.create_branch("reverse_scan", "I")
        if self.config_file.config.dut_setting.reverse_scan:
            outROOTFile.additional_branch["reverse_scan"][0] = 1
        else:
            outROOTFile.additional_branch["reverse_scan"][0] = 0

        if self.instruments["lv_ps"].is_opened:
            outROOTFile.create_branch("lowVoltPS_V_ch1", "D")
            outROOTFile.create_branch("lowVoltPS_C_ch1", "D")
            outROOTFile.create_branch("lowVoltPS_V_ch2", "D")
            outROOTFile.create_branch("lowVoltPS_C_ch2", "D")

        return outROOTFile

    def fill_lowVolt(self, outROOTFile):
        if self.instruments["lv_ps"].is_opened:
            lowVoltage_PS_Ch1 = self.instruments["lv_ps"].read_voltageCurrent(1)
            lowVoltage_PS_Ch2 = self.instruments["lv_ps"].read_voltageCurrent(2)
            outROOTFile.additional_branch["lowVoltPS_V_ch1"][0] = lowVoltage_PS_Ch1[0]
            outROOTFile.additional_branch["lowVoltPS_C_ch1"][0] = lowVoltage_PS_Ch1[1]
            outROOTFile.additional_branch["lowVoltPS_V_ch2"][0] = lowVoltage_PS_Ch2[0]
            outROOTFile.additional_branch["lowVoltPS_C_ch2"][0] = lowVoltage_PS_Ch2[1]

    # ==========================================================================
    # ==========================================================================
    def _core(self, outROOTFile, nevent, temperature=None):

        for name, inst in self.instruments.items():
            if not inst is None:
                log.info("{} looks fine.".format(name))
            else:
                log.critical("something wrong with {}".format(name))

        start_time = time.time()
        rate_checker = time.time()
        daq_current_rate = 0

        event = 0
        fail_counter = 0

        current_100cycle = self.instruments["hv_ps"].CurrentReader(
            self.config_file.config.dut_setting.ps_ch
        )

        while event < nevent:
            try:
                event += self.config_file.config.scope_setting.segment_count
                outROOTFile.additional_branch["ievent"][0] = event

                if self.instruments["chamber"].is_opened:
                    outROOTFile.additional_branch["temperature"][0] = self.instruments[
                        "chamber"
                    ].get_temperature()
                    outROOTFile.additional_branch["humidity"][0] = self.instruments[
                        "chamber"
                    ].get_humidity()

                piData = self.instruments["pi_sensor"].getData()
                outROOTFile.additional_branch["pi_temperature"][0] = piData[
                    "temperature"
                ]
                outROOTFile.additional_branch["pi_humidity"][0] = piData["humidity"]

                self.instruments["scope"].WaitForTrigger()

                outROOTFile.i_timestamp[0] = time.time()
                if (
                    (event - self.config_file.config.scope_setting.segment_count) == 0
                    or (event + self.config_file.config.scope_setting.segment_count)
                    % 100
                    == 0
                ):
                    current_100cycle = self.instruments["hv_ps"].CurrentReader(
                        self.config_file.config.dut_setting.ps_ch
                    )
                    outROOTFile.additional_branch["mon_dut_bias"][0] = self.instruments[
                        "hv_ps"
                    ].VoltageReader(self.config_file.config.dut_setting.ps_ch)
                    outROOTFile.additional_branch["mon_trig_bias"][
                        0
                    ] = self.instruments["hv_ps"].VoltageReader(
                        self.config_file.config.trigger_setting.ps_ch
                    )
                    self.fill_lowVolt(outROOTFile)
                outROOTFile.i_current[0] = current_100cycle
                waveData = ""
                try:
                    waveData = self.instruments["scope"].GetWaveform(
                        self.config_file.config.scope_setting.enable_channels
                    )
                    # print(waveData)
                except Exception as e:
                    event -= self.config_file.config.scope_setting.segment_count
                    fail_counter += 1
                    log.critical(
                        "fail getting data. {} because of : {}".format(fail_counter, e)
                    )

                    try:
                        self.instruments["scope"].scope.reopen_resource()
                    except Exception as err:
                        log.critical(err)

                    if fail_counter == 5000:
                        break
                    else:
                        continue

                if len(waveData) == 0:
                    event -= self.config_file.config.scope_setting.segment_count
                    log.critical("empyt waveData...Please report this issue")
                    continue
                elif len(waveData[0]) != len(
                    self.config_file.config.scope_setting.enable_channels
                ):
                    event -= self.config_file.config.scope_setting.segment_count
                    log.critical(
                        "waveData and channel mismatch {} {}, Please report this issue".format(
                            len(waveData[0]),
                            len(self.config_file.config.scope_setting.enable_channels),
                        )
                    )
                    continue
                else:
                    pass

                for ch in range(
                    len(self.config_file.config.scope_setting.enable_channels)
                ):
                    for j in range(len(waveData[0][ch])):
                        outROOTFile.w[ch].push_back(float(waveData[1][ch][j]))
                        outROOTFile.t[ch].push_back(waveData[0][ch][j])
                outROOTFile.Fill()
                waveData = []
                waveData = ""
                gc.collect()

                if (event + self.config_file.config.scope_setting.segment_count) % (
                    100
                ) == 0:
                    daq_current_rate = 100.0 / (time.time() - rate_checker)
                    outROOTFile.additional_branch["rate"][0] = daq_current_rate
                    date = datetime.datetime.now()
                    rate_checker = time.time()
                    log.info(
                        "[{date}] Saved event on local disk : {event}/{total}, rate:{rate}".format(
                            date=str(date),
                            event=event
                            + self.config_file.config.scope_setting.segment_count,
                            total=nevent,
                            rate=daq_current_rate,
                        )
                    )
                    if daq_current_rate < 1.5:
                        log.warning(
                            "The rate is less than 1. Performaing trigger check "
                        )
                        self.instruments["hv_ps"].PowerSupply.checkTripped(
                            self.config_file.config.dut_setting.ps_ch,
                            self.config_file.config.trigger_setting.ps_ch,
                        )

            except socket.error as e:
                event -= 1
                log.critical("Catch exception: {daq_error}, ".format(daq_error=e))
                log.warning("Continue data taking.")
            except Exception as E:
                event -= 1
                log.critical(
                    "Catch unknown exception: {daq_error}, ".format(daq_error=E)
                )
                log.warning("Continue data taking.")

                try:
                    """
                    Scope.Scope.rm.close()
                    Scope = ScopeProducer( self.configFile )
                    Scope.Scope.inst.clear()
                    """
                    self.instruments["scope"].scope.reopen_resource()
                except Exception as err:
                    log.critical(err)

        outROOTFile.Close()
        currentAfter = self.instruments["hv_ps"].CurrentReader(
            self.config_file.config.dut_setting.ps_ch
        )
        self.current_mon_file.write(
            "{}:{}:{}\n".format(
                self.instruments["hv_ps"].VoltageReader(
                    self.config_file.config.dut_setting.ps_ch
                ),
                "After",
                currentAfter,
            )
        )
        end_time = time.time()
        log.info("Rate = {}/s".format(nevent / (end_time - start_time)))

    # ==========================================================================
    # ==========================================================================
    def run_core(self, dut_bias, trig_bias, temperature, cyc):
        out_file_name = "{prefix}{run_num}_{dut_bias}V_trig{trig_bias}V_temp{temperature}.root".format(
            prefix=self.config_file.config.file_setting.prefix,
            run_num=self.config_file.config.file_setting.run_number,
            dut_bias=dut_bias,
            trig_bias=trig_bias,
            temperature=temperature,
        )

        self.instruments["hv_ps"].SetVoltage(
            self.config_file.config.trigger_setting.ps_ch, trig_bias, 1.5
        )
        v_check = self.instruments["hv_ps"].ConfirmVoltage(
            self.config_file.config.trigger_setting.ps_ch, trig_bias
        )

        self.instruments["hv_ps"].SetVoltage(
            self.config_file.config.dut_setting.ps_ch, dut_bias, 1.5
        )
        v_check = self.instruments["hv_ps"].ConfirmVoltage(
            self.config_file.config.dut_setting.ps_ch, dut_bias
        )

        if v_check:
            outROOTFile = self.create_output_file(out_file_name, dut_bias, cyc)
            self._core(
                outROOTFile, self.config_file.config.general_setting.nevent, temperature
            )
        else:
            log.critical("voltage dose not match! ({})".format(dut_bias))

    # ==========================================================================
    # ==========================================================================
    def voltage_scanner(self, temperature, cyc):

        if self.config_file.config.dut_setting.reverse_scan:
            self.config_file.config.dut_setting.voltage_list.reverse()
        for volt in self.config_file.config.dut_setting.voltage_list:
            self.run_core(
                volt,
                self.config_file.config.trigger_setting.bias_voltage,
                temperature,
                cyc,
            )

    # ==========================================================================
    # ==========================================================================
    def run_cycle_no_chamber(self, temperature):
        for cyc in range(1, self.config_file.config.general_setting.cycle + 1):
            self.voltage_scanner(temperature, cyc)
            self.waiting()

    # ==========================================================================
    # ==========================================================================

    def run_normal_cycle(self, temperature):
        for cyc in range(1, self.config_file.config.general_setting.cycle + 1):
            if self.instruments["chamber"].is_opened:
                self.instruments["chamber"].set_temperature(temperature)
                self.instruments["chamber"].check_temperature(temperature)
                temperature_compare(
                    self.instruments["chamber"],
                    self.instruments["pi_sensor"],
                    temperature,
                    self.config_file.config.chamber_setting.cali_wt,
                )
            self.voltage_scanner(temperature, cyc)
            self.instruments["hv_ps"].Close()
            if self.config_file.config.general_setting.cycle > 1:
                if not self.instruments["chamber"] is None:
                    if self.config_file.config.chamber_setting.cycle_reset:
                        reset_temp = (
                            self.config_file.config.chamber_setting.cycle_reset_temperature
                        )

                        log.warning(
                            "You have told it to do cycle with reset temperature! going to {temp}".format(
                                temp=reset_temp
                            )
                        )
                        self.instruments["chamber"].set_temperature(reset_temp)
                        self.instruments["chamber"].check_temperature(reset_temp)

                        log.info(
                            "Let's wait a bit to let the temperature settle down :)"
                        )
                        time.sleep(900)

                log.warning(
                    "Be quiet! The DAQ is sleeping now. It will be back in {nap_time} sec".format(
                        nap_time=self.config_file.config.general_setting.cycle_wait_time
                    )
                )
                for leftTime in np.arange(
                    self.config_file.config.general_setting.cycle_wait_time, 0, -1
                ):
                    time.sleep(1)
                    if leftTime % 300 == 0:
                        log.info(
                            "nap time remaining...{remain_time}".format(
                                remain_time=leftTime
                            )
                        )
                log.info("\nGood Morning!\n")
            else:
                if not self.instruments["chamber"] is None:
                    self.instruments["chamber"].set_temperature(20)

    # ==========================================================================
    # ==========================================================================
    def temperature_scanner(self):
        if self.instruments["chamber"].is_opened:
            for (
                i_temp,
                i_maxv,
                i_maxi,
                i_trigV,
            ) in self.config_file.config.chamber_setting.cycle_temperature_list:
                self.instruments["chamber"].set_temperature(i_temp)
                self.instruments["chamber"].check_temperature(i_temp)
                new_volt_list = np.arange(
                    self.config_file.config.chamber_setting.dut_min_voltage,
                    i_maxv,
                    self.config_file.config.chamber_setting.dut_voltage_step,
                )
                for cyc in range(1, self.config_file.config.general_setting.cycle):
                    for volt in new_volt_list:
                        self.run_core(volt, i_trigV, i_temp, cyc)
        else:
            log.critical("chamber is not there!")

    def BetaMeas(self):
        self.setup_dir()
        self.create_description_file()
        self.load_instruments()

        if self.config_file.config.chamber_setting.mode == 1:
            self.temperature_scanner()
        elif self.config_file.config.chamber_setting.mode == 2:
            self.voltage_scanner(
                self.config_file.config.chamber_setting.target_temperature, 1
            )
        elif self.config_file.config.chamber_setting.mode == 3:
            self.run_normal_cycle(
                self.config_file.config.chamber_setting.target_temperature
            )
        elif self.config_file.config.chamber_setting.mode == 4:
            self.run_cycle_no_chamber(
                self.config_file.config.chamber_setting.target_temperature
            )
        else:
            pass

        self.current_mon_file.close()

        if self.instruments["chamber"]:
            self.instruments["chamber"].set_temperature(20)

    """
    def ThreshodVsPeriod(self):
        print("Using Threshold vs Period Scan scripts")
        progress = general.progress(1)
        Scope = ScopeProducer(self.configFile)
        PowerSupply = PowerSupplyProducer(self.configFile)
        MASTER_PATH = self.configFile.DAQMasterDir
        PARENT_DIR = self.configFile.DAQDataDir
        Setup_Data_Folder(
            self.configFile.DAQMasterDir,
            self.configFile.DAQDataDir,
            self.configFile.RunNumber,
        )

        for i in range(len(self.configFile.ThresholdScan_VoltageList)):
            PowerSupply.SetVoltage(
                self.configFile.ThresholdScan_PSChannel,
                self.configFile.ThresholdScan_VoltageList[i],
            )
            V_Check = PowerSupply.ConfirmVoltage(
                self.configFile.ThresholdScan_PSChannel,
                self.configFile.ThresholdScan_VoltageList[i],
            )
            if V_Check:
                outFileName = self.configFile.ThresholdScan_FileNameList[i] + ".text"
                outFile = open(outFileName, "w")
                outFile.write("Threshold[V],Period[s],STD,NumEvent\n")
                print("Ready...")

                ini_threshold = self.configFile.ThresholdScan_StartValue
                while ini_threshold <= self.configFile.ThresholdScan_EndValue:
                    if ini_threshold < 0:
                        Scope.SetTrigger(
                            self.configFile.ThresholdScan_ScopeChannel,
                            ini_threshold,
                            "NEG",
                            "STOP",
                        )
                        Scope.Scope.inst.write("BUZZ ON;")
                        sleep(2)
                    else:
                        Scope.SetTrigger(
                            self.configFile.ThresholdScan_ScopeChannel,
                            ini_threshold,
                            "POS",
                            "STOP",
                        )
                        Scope.Scope.inst.write("BUZZ ON;")
                        sleep(2)
                    count = 1
                    t_0 = time.time()
                    startT = t_0
                    triggerCounter = []
                    endT = ""
                    timeout = self.configFile.ThresholdScan_Timeout
                    while count <= self.configFile.ThresholdScan_MaxEvent:
                        next = Scope.WaitForTrigger(timeout, "Th Scan")
                        deltaT = time.time() - t_0
                        if deltaT >= timeout - 0.1:
                            endT = time.time()
                            break
                        if time.time() - startT > self.configFile.ThresholdScan_MaxTime:
                            print("\nExceed data taking max time {}".format(startT))
                            endT = time.time()
                            break
                        if "1" in next:
                            t_0 = time.time()
                            waveform_data = Scope.GetWaveform(
                                int(self.configFile.ThresholdScan_ScopeChannel),
                                "binary raw",
                            )
                            trigger_Tdiff = trcReader(
                                waveform_data[0],
                                "Trigger_Tdiff",
                                self.configFile.ThresholdScan_ScopeChannel,
                                "sequence_mode",
                            )
                            for k in range(len(trigger_Tdiff) - 1):
                                triggerCounter.append(
                                    trigger_Tdiff[i + 1][0] - trigger_Tdiff[i][0]
                                )
                            count += 1
                        else:
                            pass
                        if count % 100 == 0:
                            tmp = np.array(triggerCounter)
                            avg = np.mean(tmp)
                            progress(
                                "Period Mean: {}   Finisehd".format(avg),
                                count,
                                self.configFile.ThresholdScan_MaxEvent,
                            )
                    triggerCounter = np.array(triggerCounter)
                    period = ""
                    if count > self.configFile.ThresholdScan_MaxEvent:
                        period = np.mean(triggerCounter)
                        std = np.std(triggerCounter)
                    else:
                        period = np.mean(triggerCounter)
                        std = np.std(triggerCounter)
                    outFile.write(
                        "{},{},{},{}\n".format(
                            ini_threshold, period, std, len(triggerCounter)
                        )
                    )
                    print(
                        "Results: {},{},{},{}\n".format(
                            ini_threshold, period, std, len(triggerCounter)
                        )
                    )
                    outFile.flush()
                    ini_threshold += self.configFile.ThresholdScan_Step
                    print("Next threshold : {}".format(ini_threshold))
                outFile.close()
                print("Moving to next voltage...")
        PowerSupply.Close()
        print("Finished!")
    """
