'''
logging function from stackoverflow.
https://stackoverflow.com/questions/14906764/how-to-redirect-stdout-to-both-file-and-console-with-scripting/14906787
'''

import sys
import os

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.user_data_path = os.environ.get("BetaDAQ", "/tmp/") #getting the user data path
        self.log = open( self.user_data_path+"beta_daq.log", "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass

#to use the Logger, do sys.stdout = Logger()
