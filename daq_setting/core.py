"""
DAQ Configuration reader class
"""

import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", logger=log)

import configparser
import os
from general.Color_Printing import ColorFormat


class DAQConfigBase(object):
    """
    DAQ Configuration base class
    """

    def __init__(self, config_file):
        self.config_file = config_file
        self.config_parser = configparser.ConfigParser()
        self.is_opened = False
        try:
            self.config_parser.read(config_file)
            log.info("DAQ configuration file is read")
            self.is_opened = True
            self._read_all_section()
        except Exception as e:
            log.warning("catch {}".format(e))
            log.warning("Cannot find DAQ configuration file. Exiting")

    @classmethod
    def open(cls, config_file):
        return cls(config_file)

    def read_section(self, section):
        try:
            setattr(self, section, self.config_parser[section])
        except KeyError:
            log.warning(
                " {}::{} cannot find key '{}'.".format(
                    self.__class__.__name__, self.read_section.__name__, section
                )
            )

    def _read_all_section(self):
        if self.is_opened:
            for sec in self.config_parser.sections():
                self.read_section(sec)


class DAQConfig(DAQConfigBase):

    measurement_type = ["beta", "threshold_scan"]

    class Setting(object):
        def __init__(self, name):
            self.name = name

    def __init__(self, config_file):
        super(DAQConfig, self).__init__(config_file)

    def prepare(self, measurement_type="beta"):

        if measurement_type == "beta":

            log.info(
                "preparing 'Beta-Scope' setting from configuration file: {}".format(
                    self.config_file
                )
            )
            self.general_setting = DAQConfig.Setting("general")
            self.general_setting.cycle = self.GENERAL.getint("cycle")
            self.general_setting.cycle_wait_time = self.GENERAL.getint(
                "cycle_wait_time"
            )
            self.general_setting.nevent = self.GENERAL.getint("nevent")
            self.general_setting.start_wait_time = self.GENERAL.getint(
                "start_wait_time"
            )

            self.file_setting = DAQConfig.Setting("file")
            self.file_setting.master_dir = self.OUTPUT_FILES_DIR.get("master_dir")
            self.file_setting.run_number = self.OUTPUT_FILES_DIR.getint("run_number")
            self.file_setting.prefix = self.OUTPUT_FILES_DIR.get("prefix")
            self.file_setting.output_dir = self.OUTPUT_FILES_DIR.get("output_dir")
            self.file_setting.log_dir = self.OUTPUT_FILES_DIR.get("log_dir")

            self.scope_setting = DAQConfig.Setting("scope")
            self.scope_setting.name = self.OSCILLOSCOPE.get("name")
            self.scope_setting.ip = self.OSCILLOSCOPE.get("scope_ip_address")
            self.scope_setting.enable_channels = [
                int(x) for x in self.OSCILLOSCOPE.get("enable_channels").split(",")
            ]
            self.scope_setting.segment_count = self.OSCILLOSCOPE.getint("segment_count")

            self.ps_setting = DAQConfig.Setting("power_supply")
            self.ps_setting.name = self.POWER_SUPPLY.get("name")
            self.ps_setting.enable_channels = [
                int(x) for x in self.POWER_SUPPLY.get("enable_channels").split(",")
            ]
            self.ps_setting.software_compliance = self.POWER_SUPPLY.getfloat(
                "software_compliance"
            )

            self.trigger_setting = DAQConfig.Setting("trigger")
            self.trigger_setting.bias_voltage = self.TRIGGER_SETTING.getint(
                "trigger_voltage"
            )
            self.trigger_setting.scope_threshold = self.OSCILLOSCOPE.getfloat(
                "trigger_threshold"
            )
            self.trigger_setting.threshold_type = self.OSCILLOSCOPE.get(
                "trigger_trigger_type"
            )
            self.trigger_setting.scope_ch = self.OSCILLOSCOPE.getint("trigger_channel")
            self.trigger_setting.mode = self.OSCILLOSCOPE.get("trigger_mode")
            self.trigger_setting.ps_ch = self.POWER_SUPPLY.getint("trigger_channel")

            self.dut_setting = DAQConfig.Setting("dut")
            self.dut_setting.voltage_list = [
                int(x) for x in self.VOLTAGE_SCAN.get("voltage_list").split(",")
            ]
            self.dut_setting.reverse_scan = self.VOLTAGE_SCAN.getboolean("reverse_scan")
            self.dut_setting.ps_ch = self.POWER_SUPPLY.getint("dut_channel")
            self.dut_setting.scope_channels = [
                int(x) for x in self.OSCILLOSCOPE.get("dut_channel").split(",")
            ]

            self.chamber_setting = DAQConfig.Setting("chamber")
            self.chamber_setting.name = self.CHAMBER.get("name")
            self.chamber_setting.mode = self.CHAMBER.getint("mode")
            self.chamber_setting.target_temperature = self.CHAMBER.getint(
                "target_temperature"
            )
            self.chamber_setting.cycle_reset = self.CHAMBER.getboolean("cycle_reset")
            self.chamber_setting.cycle_reset_temperature = self.CHAMBER.getint(
                "cycle_reset_temperature"
            )
            self.chamber_setting.cycle_temperature_list = [
                (int(temp), int(max_volt), int(max_current), int(trig_volt))
                for temp, max_volt, max_current, trig_volt in zip(
                    self.CHAMBER.get("cycle_temperature_list").split(","),
                    self.CHAMBER.get("dut_max_voltage_list").split(","),
                    self.CHAMBER.get("dut_max_current_list").split(","),
                    self.CHAMBER.get("trigger_voltage_list").split(","),
                )
            ]
            self.chamber_setting.dut_min_voltage = self.CHAMBER.getint(
                "dut_min_voltage"
            )
            self.chamber_setting.dut_voltage_step = self.CHAMBER.getint(
                "dut_voltage_step"
            )

        elif measurement_type == "threshold_scan":

            self.threshold_scan_setting = DAQConfig.Setting("threshold_scan")
            self.threshold_scan_setting.voltage_list = [
                int(x) for x in self.THRESHOLD_SCAN.get("voltage_list").split(",")
            ]
            self.threshold_scan_setting.scope_channel = self.THRESHOLD_SCAN.getint(
                "scope_channel"
            )
            self.threshold_scan_setting.ps_channel = self.THRESHOLD_SCAN.getint(
                "ps_channel"
            )
            self.threshold_scan_setting.threshold_start = self.THRESHOLD_SCAN.getfloat(
                "threshold_start"
            )
            self.threshold_scan_setting.threshold_end = self.THRESHOLD_SCAN.getfloat(
                "threshold_end"
            )
            self.threshold_scan_setting.threshold_step = self.THRESHOLD_SCAN.getfloat(
                "threshold_step"
            )
            self.threshold_scan_setting.timeout = self.THRESHOLD_SCAN.getint("timeout")
            self.threshold_scan_setting.max_wait_time = self.THRESHOLD_SCAN.getint(
                "max_wait_time"
            )
            self.threshold_scan_setting.nevent = self.THRESHOLD_SCAN.getint("nevent")

        else:
            log.critical(
                "cannot identify measurement type: {}".format(measurement_type)
            )
