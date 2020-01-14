import logging, coloredlogs

logging.basicConfig(filename="/tmp/beta_daq.log", filemode="a")
log = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG", logger=log)

from BetaDAQ import BetaDAQ

if __name__ == "__main__":

    # create log file
    # sys.stdout = logger.Logger()

    log.info("BetaScope DAQ is created")

    DAQ = BetaDAQ()
    DAQ.BetaMeas()

    log.info("DAQ is closed")
