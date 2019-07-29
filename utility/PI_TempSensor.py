'''
class to retrive humidity and temperature from the sensor connected to the raspbery pi.
'''

import json
import urllib2
import socket

class PI_TempSensor:
    def __init__(self):
        self.http = "http://169.233.167.33/"

    def getData(self):
        try:
            connc = urllib2.urlopen(self.http, timeout = 0.01)
        except urllib2.URLError, e:
            return {"humidity":10e10, "temperature":10e10}
        except socket.timeout, e:
            return {"humidity":10e10, "temperature":10e10}
        data = connc.read()
        odata = json.loads(data)
        return odata


if __name__ == "__main__":

    '''
    Test
    '''
    piSensor = PI_TempSensor()
    piData = piSensor.getData()
    print(piData["humidity"])
    print(piData["temperature"])
