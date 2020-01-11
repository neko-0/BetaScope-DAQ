"""
class to retrive humidity and temperature from the sensor connected to the raspbery pi.
"""

import json
from urllib.request import urlopen, URLError
import socket


class PI_TempSensor:
    def __init__(self):
        self.http = "http://169.233.167.33/"

    def getData(self):
        try:
            connc = urlopen(self.http, timeout=0.01)
        except URLError as e:
            return {"humidity": 10e10, "temperature": 10e10}
        except socket.timeout as e:
            return {"humidity": 10e11, "temperature": 10e11}
        data = connc.read()
        odata = json.loads(data)
        return odata

    def get_temperature(self):
        data = self.getData()
        return float(data["temperature"])


if __name__ == "__main__":

    """
    Test
    """
    piSensor = PI_TempSensor()
    piData = piSensor.getData()
    print(piData["humidity"])
    print(piData["temperature"])
