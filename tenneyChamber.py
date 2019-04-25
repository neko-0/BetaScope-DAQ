from tenney_chamber import f4t_controller
from stas_plot_tool import generic_plot
import argparse
import time
import multiprocessing as mp

if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--task", dest="job_type", nargs="?", type=str )

    argv = argparser.parse_args()

    if "record" in argv.job_type:
        f4t = f4t_controller.F4T_Controller()

        '''
        temperature_plot = generic_plot.Generic_Plot("Time", "Temperature")
        humidity_plot = generic_plot.Generic_Plot("Time", "Humidity")

        tempPlot_proc = mp.Process(target=temperature_plot.draw, args=(1,))
        tempPlot_proc.start()

        humiPlot_proc = mp.Process(target=humidity_plot.draw, args=(2,))
        humiPlot_proc.start()

        log_proc = mp.Process(target=f4t.log_temp_humi_to_file )
        log_proc.start()
        print("plotting start here")

        while True:
            #print("update plot...")
            tNow = time.time()
            temp = f4t.get_temperature()
            if temp <= -237.0: continue
            humi = f4t.get_humidity()
            if humi <=-1.0: continue
            temperature_plot.updateValue( tNow, temp )
            humidity_plot.updateValue( tNow, humi )
            time.sleep(3)

        print("hereere")
        humiPlot_proc.join()
        tempPlot_proc.join()
        log_proc.join()
        '''
        f4t.log_temp_humi_to_file()

    if "set_temp=" in argv.job_type:
         f4t = f4t_controller.F4T_Controller()
         set_value = argv.job_type.split("set_temp=")[1]
         f4t.set_temperature( set_value )
