__author__ = 'Gianluca Barbon'

from services.asip_service import AsipService
from asip_client import AsipClient
import sys

class SparkfunWSService(AsipService):

    class Pressure(AsipService):
        _serviceID = 'P'

        DEBUG = False
        _pressureID = 0

        # The service should be attached to a client
        asip = None

        # This is the last measured distance (-1 if not initialised)
        _lastPressure = -1

        # Some constants (see docs)
        REQUEST_SINGLE_PRESSURE = 'M';
        PRESSURE_EVENT = 'e';

        # The constructor takes the id of the distance sensor.
        def __init__(self, id, asipclient):
            AsipService.__init__(self)
            self._pressureID = id
            self.asip = asipclient
            self._lastPressure = -1

        def get_service_id(self):
            return self._serviceID

        def set_service_id(self,id):
            self._serviceID = id

        def request_pressure(self):
            self.asip.get_asip_writer().write(self._serviceID+","+self.REQUEST_SINGLE_PRESSURE+"\n")

        def enable_continuous_reporting(self,interval):
            self.asip.get_asip_writer().write(self._serviceID+","+AsipService.AUTOEVENT_REQUEST+","+interval+"\n")

        def get_pressure(self):
            return self._lastPressure

        def process_response(self, message):
            # A response for a message is something like "@D,e,1,25,35,..."
            if message[3] != self.PRESSURE_EVENT:
                # FIXME: improve error checking
                # We have received a message but it is not a distance reporting event
                sys.stdout.write("Distance message received but I don't know how to process it: {}".format(message))
            else:
                if self.DEBUG:
                    sys.stdout.write("DEBUG: received message is {}\n".format(message))
                pressures = message[message.index("{")+1: message.index("}")]
                self._lastPressure = float(pressures.split(",")[self._pressureID])

    class Humidity(AsipService):
        _serviceID = 'H'

        DEBUG = False
        _humidityID = 0

        # The service should be attached to a client
        asip = None

        # This is the last measured distance (-1 if not initialised)
        _lastHumidity = -1

        # Some constants (see docs)
        REQUEST_SINGLE_HUMIDITY = 'M';
        HUMIDITY_EVENT = 'e';

        # The constructor takes the id of the distance sensor.
        def __init__(self, id, asipclient):
            AsipService.__init__(self)
            self._humidityID = id
            self.asip = asipclient
            self._lastHumidity = -1

        def get_service_id(self):
            return self._serviceID

        def set_service_id(self,id):
            self._serviceID = id

        def request_humidity(self):
            self.asip.get_asip_writer().write(self._serviceID+","+self.REQUEST_SINGLE_HUMIDITY+"\n")

        def enable_continuous_reporting(self,interval):
            self.asip.get_asip_writer().write(self._serviceID+","+AsipService.AUTOEVENT_REQUEST+","+interval+"\n")

        def get_humidity(self):
            return self._lastHumidity

        def process_response(self, message):
            # A response for a message is something like "@D,e,1,25,35,..."
            if message[3] != self.HUMIDITY_EVENT:
                # FIXME: improve error checking
                # We have received a message but it is not a distance reporting event
                sys.stdout.write("Distance message received but I don't know how to process it: {}".format(message))
            else:
                if self.DEBUG:
                    sys.stdout.write("DEBUG: received message is {}\n".format(message))
                values = message[message.index("{")+1: message.index("}")]
                self._lastHumidity = float(values.split(",")[self._humidityID])