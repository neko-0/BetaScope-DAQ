import betascopedaq as betaDAQ

import argparse
import time
import logging
from tqdm import tqdm

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def write_helper(f4t, ofile):
    try:
        ofile.additional_branch["temperature"][0] = f4t.get_temperature()
        ofile.additional_branch["humidity"][0] = f4t.get_humidity()
    except ValueError:
        ofile.additional_branch["temperature"][0] = -999
        ofile.additional_branch["humidity"][0] = -999
    ofile.i_timestamp[0] = time.time()
    ofile.Fill()


def temperature_cycle(ncycle, temp1, temp2, wait1, wait2):
    """
    performing temperature cycle

    Args:
        ncycle : int
            number of cycle.

        temp1/2 : float
            temperature target 1/2

        wait1/2 : int
            wait time (in sec) for temperature target 1/2.
    """

    f4t = betaDAQ.F4T_Controller()

    temp_list = [temp1, temp2]
    wait_list = [wait1, wait2]

    for cycle_i in range(1, ncycle + 1):

        ofile = betaDAQ.ROOTFileOutput("user_data/temperature_cycle.root", [])
        ofile.create_branch("temperature", "D")
        ofile.create_branch("humidity", "D")
        ofile.create_branch("cycle", "I")

        logger.info(f"Starting cycle {cycle_i}")

        ofile.additional_branch["cycle"][0] = cycle_i + 1

        for c_temp, c_wait in zip(temp_list, wait_list):
            logger.info(f"Set temperature to {c_temp}C")
            f4t.set_temperature(c_temp)
            while abs(f4t.get_temperature() - c_temp) >= 1.5:
                write_helper(f4t, ofile)
                time.sleep(1)

            logger.info(f"Staying for {c_wait} sec")
            for _ in tqdm(range(int(c_wait)), leave=False, desc="waiting..."):
                write_helper(f4t, ofile)
                time.sleep(1)

        logger.info(f"cycle {cycle_i} is finished, move to next cycle")

        ofile.Close()

    logger.info("all cycle are finished. Set 20C")
    f4t.set_temperature(20)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--test", help="for testing", action="store_true")
    argparser.add_argument(
        "-n",
        "--num_cycle",
        help="number of cycles",
        nargs="?",
        const=1,
        type=int,
        dest="numCycle",
    )
    argparser.add_argument(
        "-t1",
        "--temperature1",
        help="temperature 1",
        nargs="?",
        const=1,
        type=int,
        dest="t1",
    )
    argparser.add_argument(
        "-t2",
        "--temperature2",
        help="temperature 2",
        nargs="?",
        const=1,
        type=int,
        dest="t2",
    )
    argparser.add_argument(
        "-w1",
        "--wait1",
        help="wait time at temperature 1",
        nargs="?",
        const=1,
        type=int,
        dest="w1",
    )
    argparser.add_argument(
        "-w2",
        "--wait2",
        help="wait time at temperature 2",
        nargs="?",
        const=1,
        type=int,
        dest="w2",
    )

    argv = argparser.parse_args()

    temperature_cycle(argv.numCycle, argv.t1, argv.t2, argv.w1, argv.w2)
