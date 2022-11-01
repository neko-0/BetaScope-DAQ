import betascopedaq as betaDAQ

import argparse
import time
import logging
from tqdm import tqdm

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

    ofile = betaDAQ.ROOTFileOutput("user_data/temperature_cycle.root", [])
    ofile.create_branch("temperature", "D")
    ofile.create_branch("humidity", "D")
    ofile.create_branch("cycle", "I")

    for cycle_i in range(1, ncycle + 1):

        logger.info(f"Starting cycle {cycle_i}")

        ofile.additional_branch["cycle"][0] = cycle_i + 1

        logger.info(f"Set temperature to {temp1}C")
        f4t.set_temperature(argv.t1)
        while abs(f4t.get_temperature() - temp1) >= 1.5:
            ofile.additional_branch["temperature"][0] = f4t.get_temperature()
            ofile.additional_branch["humidity"][0] = f4t.get_humidity()
            ofile.i_timestamp[0] = time.time()
            ofile.Fill()

        logger.info(f"Staying for {wait1} sec")
        for _ in tqdm(range(int(wait1)), leave=False, desc="waiting..."):
            ofile.additional_branch["temperature"][0] = f4t.get_temperature()
            ofile.additional_branch["humidity"][0] = f4t.get_humidity()
            ofile.i_timestamp[0] = time.time()
            ofile.Fill()
            time.sleep(1)

        logger.info(f"Setting temperature to {temp2}")
        f4t.set_temperature(argv.t2)
        while abs(f4t.get_temperature() - temp2) >= 1.5:
            ofile.additional_branch["temperature"][0] = f4t.get_temperature()
            ofile.additional_branch["humidity"][0] = f4t.get_humidity()
            ofile.i_timestamp[0] = time.time()
            ofile.Fill()

        logger.info(f"Staying for {wait2} sec")
        for _ in tqdm(range(int(wait2)), leave=False, desc="waiting..."):
            ofile.additional_branch["temperature"][0] = f4t.get_temperature()
            ofile.additional_branch["humidity"][0] = f4t.get_humidity()
            ofile.i_timestamp[0] = time.time()
            ofile.Fill()
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
