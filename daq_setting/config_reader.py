import logging, coloredlogs

logging.basicConfig()
log = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", logger=log)

from .core import DAQConfig
import os
import subprocess


class DAQConfigReader(object):
    def __init__(self, config_file):
        self.config = DAQConfig(config_file)

    @classmethod
    def open(cls, config_file=os.path.dirname(__file__) + "/config.ini"):
        log.info("open {}".format(config_file))
        log.warning("Which Measurement?[beta(Beta Measurement), ts(Threshold Scan)]: ")
        measurement_type = input()
        log.warning("Modify configuration file?[Y/N] ")
        modify_config = input()
        if "Y" in modify_config or "y" in modify_config:
            log.warning("which editor? you can skip this by calling default editor")
            editor = input()
            if editor:
                if "gui" in editor:
                    pass
                else:
                    EDITOR = os.environ.get("EDITOR", str(editor))
                    subprocess.call([EDITOR, config_file])
            else:
                EDITOR = os.environ.get("EDITOR", str("gedit"))
                subprocess.call([EDITOR, config_file])

        obj = cls(config_file)
        obj.config.prepare(measurement_type)
        return obj
