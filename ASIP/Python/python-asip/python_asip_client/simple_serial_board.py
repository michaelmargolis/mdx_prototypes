__author__ = 'Gianluca Barbon'

import time
import sys
import glob
import serial
from asip_client import AsipClient
from threading import Thread
from Queue import Queue
from asip_writer import AsipWriter
from serial import Serial


class SimpleSerialBoard:

    # ************   BEGIN CONSTANTS DEFINITION ****************

    DEBUG = False

    # ************   END CONSTANTS DEFINITION ****************

    # ************   BEGIN PRIVATE FIELDS DEFINITION ****************

    ser_conn = None  # self board uses serial communication
    asip = None  # The client for the aisp protocol
    queue = Queue(10)  # Buffer # TODO: use pipe instead of queue for better performances
    #  FIXME: fix Queue dimension?
    _port = "" #serial port
    _ports = [] #serial ports array
  
    # ************   END PRIVATE FIELDS DEFINITION ****************

    # self constructor takes the name of the serial port and it creates a Serial object
    # Here the serial listener and the queue reader are started
    def __init__(self):
        # TODO: very simple implementation, need to improve
        #self.ser_conn = Serial()
        #self.serial_port_finder()    
        try:
            # old implementation was:
            #self.ser_conn = Serial(port='/dev/cu.usbmodemfd121', baudrate=57600)
            # self.ser_conn = Serial(port=self._port, baudrate=57600)
            self.ser_conn = Serial()
            portIndexToOpen = 0             
            self.serial_port_finder(portIndexToOpen)          
            print("attempting to open " +self._ports[portIndexToOpen])           
            self.open_serial(self._ports[0], 57600)      
            print("port opened");             
            self.asip = AsipClient(self.SimpleWriter(self))
        except Exception as e:
            sys.stdout.write("Exception: caught {} while init serial and asip protocols\n".format(e))

        try:          
            self.ListenerThread(self.queue, self.ser_conn, True, self.DEBUG).start()
            self.ConsumerThread(self.queue, self.asip, True, self.DEBUG).start()
            while self.asip.isVersionOk() == False:  # flag will be set to true when valid version message is received
                self.request_info()  
                time.sleep(1.0)            
            self.request_port_mapping()          
            #time.sleep(1)
        except Exception as e:
            #TODO: improve exception handling
            sys.stdout.write("Exception: caught {} while launching threads\n".format(e))


    # ************ BEGIN PUBLIC METHODS *************

    # The following methods are just a replica from the asip class.
    # TODO: add parameter checikng in each function (raise exception?)
    def digital_read(self, pin):
        return self.asip.digital_read(pin)

    def analog_read(self, pin):
        return self.asip.analog_read(pin)

    def set_pin_mode(self, pin, mode):
        self.asip.set_pin_mode(pin, mode)

    def digital_write(self, pin, value):
        self.asip.digital_write(pin, value)

    def analog_write(self, pin, value):
        self.asip.analog_write(pin, value)

    def request_info(self):
        self.asip.request_info()
    
    def request_port_mapping(self):
        self.asip.request_port_mapping()

    def set_auto_report_interval(self, interval):
        self.asip.set_auto_report_interval(interval)

    def add_service(self, service_id, asip_service):
        self.asip.add_service(service_id, asip_service)

    def get_asip_client(self):
        return self.asip

    # ************ END PUBLIC METHODS *************


    # ************ BEGIN PRIVATE METHODS *************

    def open_serial(self, port, baudrate):
        if self.ser_conn.isOpen():
            self.ser_conn.close()
        self.ser_conn.port = port
        self.ser_conn.baudrate = baudrate
        self.ser_conn.open()
        # Toggle DTR to reset Arduino
        self.ser_conn.setDTR(False)
        time.sleep(1)
        # toss any data already received, see
        self.ser_conn.flushInput()
        self.ser_conn.setDTR(True)

    def close_serial(self):
        self.ser_conn.close()

    # This methods retrieves the operating system and set the Arduino serial port
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    # TODO: test needed for linux and windows implementation
    def serial_port_finder(self, desiredIndex):
        #system = platform.system()
        # if self.DEBUG:
        #     sys.stdout.write("DEBUG: detected os is {}\n".format(system))
        # if 'linux' in system:
        #     pass
        # elif 'Darwin' == system: # also 'mac' or 'darwin' may work?
        #     for file in os.listdir("/dev"):
        #         if file.startswith("tty.usbmodem"):
        #             self._port = "/dev/" + file
        #             if self.DEBUG:
        #                 sys.stdout.write("DEBUG: serial file is {}\n".format(file))
        #             break
        # elif ('win' in system) or ('Win' in system) or ('cygwin' in system) or ('nt' in system):
        #     pass
        # else:
        #     raise EnvironmentError('Unsupported platform')
        # if self.DEBUG:
        #     sys.stdout.write("DEBUG: port is {}\n".format(self._port))

        system = sys.platform
        if system.startswith('win'):
            temp_ports = ['COM' + str(i + 1) for i in range(255)]          
        elif system.startswith('linux'):
            # this is to exclude your current terminal "/dev/tty"
            temp_ports = glob.glob('/dev/tty[A-Za-z]*')
        elif system.startswith('darwin'):
            temp_ports = glob.glob('/dev/tty.usbmodem*')
        else:
            raise EnvironmentError('Unsupported platform')

        for port in temp_ports:
            try:
                self.ser_conn.port = port
                s = self.ser_conn.open()
                self.ser_conn.close()
                self._ports.append(port)
                if(len(self._ports) > desiredIndex):
                    return  # we have found the desired port
            except serial.SerialException:
                pass
        if self.DEBUG:
             sys.stdout.write("DEBUG: available ports are {}\n".format(self._ports))

    # ************ END PRIVATE METHODS *************


    # ************ BEGIN PRIVATE CLASSES *************

    # As described above, SimpleSerialBoard writes messages to the serial port.
    # inner class SimpleWriter implements abstract class AsipWriter:
    class SimpleWriter(AsipWriter):
        parent = None

        def __init__(self, parent):
            self.parent = parent

        # val is a string
        # TODO: improve try catch
        def write(self, val):
            #print(val), 
            if self.parent.ser_conn.isOpen():
                try:
                    self.parent.ser_conn.write(val.encode())
                except (OSError, serial.SerialException):
                    pass
            else:
                raise serial.SerialException

    # ListenerThread and ConsumerThread are implemented following the Producer/Consumer pattern
    # A class for a listener that rad the serial stream and put incoming messages on a queue
    # TODO: implement try catch
    class ListenerThread(Thread):

        queue = None
        ser_conn = None
        running = False
        DEBUG = False

        # overriding constructor
        def __init__(self, queue, ser_conn, running, debug):
            Thread.__init__(self)
            self.queue = queue
            self.ser_conn = ser_conn
            self.running = running
            self.DEBUG = debug
            if self.DEBUG:
                sys.stdout.write("DEBUG: serial thread process created \n")

        # if needed, kill will stops the loop inside run method
        def kill(self):
            self.running = False

        # overriding run method, thread activity
        def run(self):
            temp_buff = ""
            time.sleep(2)
            # TODO: implement ser.inWaiting() >= minMsgLen to check number of char in the receive buffer?

            while self.running:
                if self.DEBUG:
                    sys.stdout.write("DEBUG: Temp buff is now {}\n".format(temp_buff))
                val = self.ser_conn.readline()
                if self.DEBUG:
                    sys.stdout.write("DEBUG: val value when retrieving from serial is {}\n".format(val))
                val = val.decode('utf-8')
                if self.DEBUG:
                    sys.stdout.write("DEBUG: val value after decode is {}".format(val))
                if val is not None and val!="\n":
                    if "\n" in val:
                        # If there is at least one newline, we need to process
                        # the message (the buffer may contain previous characters).

                        while ("\n" in val and len(val) > 0):
                            # But remember that there could be more than one newline in the buffer
                            temp_buff += (val[0:val.index("\n")])
                            self.queue.put(temp_buff)
                            if self.DEBUG:
                                sys.stdout.write("DEBUG: Serial produced {}\n".format(temp_buff))
                            temp_buff = ""
                            val = val[val.index("\n")+1:]
                            if self.DEBUG:
                                sys.stdout.write("DEBUG: Now val is {}\n".format(val))
                        if len(val)>0:
                            temp_buff = val
                        if self.DEBUG:
                            sys.stdout.write("DEBUG: After internal while buffer is {}\n".format(temp_buff))
                    else:
                        temp_buff += val
                        if self.DEBUG:
                            sys.stdout.write("DEBUG: else case, buff is equal to val, so they are {}\n".format(temp_buff))

    # A class that reads the queue and launch the processInput method of the AispClient.
    class ConsumerThread(Thread):

        queue = None
        asip = None
        running = False
        DEBUG = False

        # overriding constructor
        def __init__(self, queue, asip, running, debug):
            Thread.__init__(self)
            self.queue = queue
            self.asip = asip
            self.running = running
            self.DEBUG = debug
            if self.DEBUG:
                sys.stdout.write("DEBUG: consumer thread created \n")

        # if needed, kill will stops the loop inside run method
        def kill(self):
            self.running = False

        # overriding run method, thread activity
        def run(self):
            # global _queue
            # global asip
            while self.running:
                temp = self.queue.get()
                self.asip.process_input(temp)
                self.queue.task_done()
                # if temp == "\n":
                    # print("WARNING")
                # print ("Consumed", temp)

    # ************ END PRIVATE CLASSES *************