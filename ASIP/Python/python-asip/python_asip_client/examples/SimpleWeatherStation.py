__author__ = 'Gianluca Barbon'

from simple_serial_board import SimpleSerialBoard
from services import sparkfunws_service
import sys
import time


# A simple board with just the I/O services.
# The main method does a standard blink test.
class SimpleWeatherStation(SimpleSerialBoard):

    p0 = None
    h0 = None
    __DEBUG = False

    def __init__(self):
        SimpleSerialBoard.__init__(self)
        try:
            time.sleep(0.3)
            self.p0 = sparkfunws_service.SparkfunWSService.Pressure(0, self.get_asip_client())
            self.h0 = sparkfunws_service.SparkfunWSService.Humidity(0, self.get_asip_client())
            time.sleep(0.3)
            self.add_service('P', self.p0)
            self.add_service('H', self.h0)
            time.sleep(0.3)
            self.p0.enable_continuous_reporting('500')
            self.h0.enable_continuous_reporting('500')
            time.sleep(0.1)
            self.get_asip_client().set_auto_report_interval('0')
        except Exception as e:
            sys.stdout.write("Exception: caught {} in init\n".format(e))

    def get_pressure(self):
        return self.p0.get_pressure()

    def get_humidity(self):
        return self.h0.get_humidity()

    def main(self):
        while True:
            try:
                time.sleep(0.5)
                sys.stdout.write("Pressure is {}\n".format(self.get_pressure()))
                sys.stdout.write("Humidity is {}\n".format(self.get_humidity()))
            except Exception as e:
                sys.stdout.write("Exception: caught {} in digital_write".format(e))

# test SimpleBlink
if __name__ == "__main__":
    SimpleWeatherStation().main()
