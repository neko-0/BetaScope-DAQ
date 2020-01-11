from tenney_chamber import f4t_controller
from utility.Password import Password
from file_io import ROOTClass
import argparse
import time

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

    if argv.test:
        print("Testing")
        print("list all input arguments:")
        print("-n : {}".format(argv.numCycle))
        print("-t1 : {}".format(argv.t1))
        print("-t2 : {}".format(argv.t2))
        print("-w1 : {}".format(argv.w1))
        print("-w2 : {}".format(argv.w2))
    else:
        if (
            argv.numCycle == None
            or argv.t1 == None
            or argv.t2 == None
            or argv.w1 == None
            or argv.w2 == None
        ):
            print("Please specify each flags")
        else:
            while True:
                check = Password.check_login()
                if check:
                    break

            f4t = f4t_controller.F4T_Controller()

            outROOTFile = ROOTClass.ROOTFileOutput(
                "user_data/temperature_cycle.root", []
            )
            outROOTFile.create_branch("temperature", "D")
            outROOTFile.create_branch("humidity", "D")
            outROOTFile.create_branch("cycle", "I")

            for cyc in range(argv.numCycle):

                print("Starting cycle : {}".format(cyc + 1))

                outROOTFile.additional_branch["cycle"][0] = cyc + 1

                print("Set to temperature 1 : {}".format(argv.t1))
                f4t.set_temperature(argv.t1)
                while abs(f4t.get_temperature() - argv.t1) >= 1.5:
                    outROOTFile.additional_branch["temperature"][
                        0
                    ] = f4t.get_temperature()
                    outROOTFile.additional_branch["humidity"][0] = f4t.get_humidity()
                    outROOTFile.i_timestamp[0] = time.time()
                    outROOTFile.Fill()

                print("Waiting on temperature 1 for {} sec".format(argv.w1))
                for nap in xrange(argv.w1, 0, -1):
                    outROOTFile.additional_branch["temperature"][
                        0
                    ] = f4t.get_temperature()
                    outROOTFile.additional_branch["humidity"][0] = f4t.get_humidity()
                    outROOTFile.i_timestamp[0] = time.time()
                    outROOTFile.Fill()
                    time.sleep(1)
                    if nap % 100 == 0:
                        print("time remaining at temperature 1: {}".format(nap))

                print("Set to temperature 2 : {}".format(argv.t2))
                f4t.set_temperature(argv.t2)
                while abs(f4t.get_temperature() - argv.t2) >= 1.5:
                    outROOTFile.additional_branch["temperature"][
                        0
                    ] = f4t.get_temperature()
                    outROOTFile.additional_branch["humidity"][0] = f4t.get_humidity()
                    outROOTFile.i_timestamp[0] = time.time()
                    outROOTFile.Fill()

                print("Waiting on temperature 2 for {} sec".format(argv.w2))
                for nap in xrange(argv.w2, 0, -1):
                    outROOTFile.additional_branch["temperature"][
                        0
                    ] = f4t.get_temperature()
                    outROOTFile.additional_branch["humidity"][0] = f4t.get_humidity()
                    outROOTFile.i_timestamp[0] = time.time()
                    outROOTFile.Fill()
                    time.sleep(1)
                    if nap % 100 == 0:
                        print("time remaining at temperature 2: {}".format(nap))

                print("cycle {} is finish, move to next cycle".format(cyc + 1))

            outROOTFile.Close()
            print("all cycle are finished. Set 20C")
            f4t.set_temperature(20)
