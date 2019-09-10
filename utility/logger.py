'''
logging function from stackoverflow.
https://stackoverflow.com/questions/14906764/how-to-redirect-stdout-to-both-file-and-console-with-scripting/14906787
'''

import sys
import os
import time

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.user_data_path = os.environ.get("BetaDAQ", "/tmp/") #getting the user data path
        self.log = open( self.user_data_path+"beta_daq.log", "a")
        self.log.write("logger start time {}\n".format(time.time()))

    def write(self, message):
        self.terminal.write(message)
        message = message.replace("\033[92m", "")
        message = message.replace("\033[93m", "")
        message = message.replace("\033[36m", "")
        message = message.replace("\033[35m", "")
        message = message.replace("\033[0m", "")
        self.log.write(message)
        self.log.flush()

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass

#to use the Logger, do sys.stdout = Logger()
