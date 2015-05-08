__author__ = 'Gianluca Barbon'

# import AsipWriter
import sys
# import traceback
from port_manager import PortManager


class AsipClient:

    # Constants inherited from Java client version
    # TODO: implement emulation of constant through dedicated file / function

    # ************   BEGIN CONSTANTS DEFINITION ****************
    DEBUG = False  # Do you want me to print verbose debug information?

    # Low-level tags for I/O service:
    IO_SERVICE = 'I'  # tag indicating message is for I/O service
    PIN_MODE = 'P'  # i/o request  to Arduino to set pin mode
    DIGITAL_WRITE = 'd'  # i/o request  to Arduino is digitalWrite
    ANALOG_WRITE = 'a'  # i/o request to Arduino is analogWrite
    ANALOG_DATA_REQUEST = 'A'  # i/o request to Arduino to set Autoreport to a certain value in ms
    PORT_DATA = 'd'  # i/o event from Arduino is digital port data
    ANALOG_VALUE = 'a'  # i/o event from Arduino is value of analog pin
    PORT_MAPPING = 'M'  # i/o event from Arduino is port mapping to pins
    GET_PIN_MODES = 'p'  # gets a list of pin modes
    GET_PIN_SERVICES_LIST = 's'  # gets a list of pins indicating registered service
    # tag_GET_SERVICES_NAMES    = 'n' # gets a list of service tags/name pairs
    GET_PIN_CAPABILITIES = 'c'  # gets a bitfield array indicating pin capabilities
    
    #tag for system messages:
    SYSTEM_GET_INFO = '?' # Get version and hardware info
    RESTART_REQUEST = 'R' # disables all autoevents and attempts to restart all services 

    # Pin modes (these are public)
    INPUT = 1  # defined in Arduino.h
    INPUT_PULLUP = 2  # defined in Arduino.h
    OUTPUT = 3  # defined in Arduino.h
    ANALOG = 4  # analog pin in analogInput mode
    PWM = 5  # digital pin in PWM output mode

    EVENT_HANDLER = '@'  # Standard incoming message
    SYSTEM_MSG_HEADER    = '#'  # incoming is a system message 
    ERROR_MESSAGE_HEADER = '~'  # Incoming message: error report
    DEBUG_MESSAGE_HEADER = '!'  # A debug message from the board (can be ignored, probably)

    # ************   END CONSTANTS DEFINITION ****************

    # ************   BEGIN PRIVATE FIELDS DEFINITION ****************

    # __digital_input_pins = []
    # __analog_input_pins = []
    # __pin_mode = []  # FIXME: do we need this at all?

    # PortManager object
    __port_map = None

    # A map from service IDs to actual implementations.
    # FIXME: there could be more than one service with the same ID!
    # (two servos, two distance sensors, etc).
    # use of the dict for python for hashmap
    __services = None

    # The output channel (where we write messages). This should typically be a serial port, but could be anything else.
    # out = AsipWriter()
    __out = None

    __AsipVersionOk = False # flag to indicate that a valid version message has been received
     
    # ************   END PRIVATE FIELDS DEFINITION ****************

    #  A constructor taking the writer as parameter.
    def __init__(self, w=None):

        # Ports, pins, and services initialization
        # self.__pin_mode = [None]*(self.MAX_NUM_DIGITAL_PINS + self.MAX_NUM_ANALOG_PINS)
        self.__services = {}
        self.__port_map = PortManager()

        # constructor also work without writer parameter
        if w is not None:
            self.__out = w
            if self.DEBUG:
                sys.stdout.write('DEBUG: Constructor, writer supplied\n')

        if self.DEBUG:
            sys.stdout.write('DEBUG: End of constructor: arrays and maps created\n')

    # ************ BEGIN PUBLIC METHODS *************

    # returns the port_map object (port_manager)
    def request_port_map(self):
        return self.__port_map

    # This method processes an input received on the serial port.
    # See protocol description for more detailed information.
    def process_input(self, input_str):
        if self.DEBUG:
            sys.stdout.write("DEBUG: received input in process_input is {}\n".format(input_str))
        if input_str[0] == self.EVENT_HANDLER:
            self.__handle_input_event(input_str)
        elif input_str[0] == self.ERROR_MESSAGE_HEADER:
            self.__handle_input_error(input_str)
        elif input_str[0] == self.DEBUG_MESSAGE_HEADER:
            self.__handle_debug_event(input_str)
        else:
            # FIXME: better error handling required! (raise exception) ?
            if self.DEBUG:
                sys.stdout.write("DEBUG: Strange character received at position 0: {}\n".format(input_str))

    # method to request ASIP system info
    def request_info(self):
        self.__out.write("{},{}\n".format(self.SYSTEM_MSG_HEADER,self.SYSTEM_GET_INFO))     
        if self.DEBUG:
            sys.stdout.write("DEBUG: Requesting info {},{}\n".format(self.SYSTEM_MSG_HEADER,self.SYSTEM_GET_INFO))               
    # A method to request the mapping between ports and pins.
    # See process_port_data and process_pin_mapping for additional details on the actual mapping.
    def request_port_mapping(self):
        self.__out.write("{},{}\n".format(self.IO_SERVICE,self.PORT_MAPPING))
        if self.DEBUG:
            sys.stdout.write("DEBUG: Requesting port mapping with {},{}\n".format(self.IO_SERVICE,self.PORT_MAPPING))

    def digital_read(self, pin):
        # FIXME: should add error checking here
        return self.__port_map.digital_read(pin)

    def analog_read(self, pin):
        # FIXME: should add error checking here
        return self.__port_map.analog_read(pin)

    def set_pin_mode(self, pin, mode):
        self.__out.write("{},{},{},{}\n".format(self.IO_SERVICE, self.PIN_MODE, pin, mode))
        if self.DEBUG:
            sys.stdout.write(
                "DEBUG: Setting pin mode with {},{},{},{}\n".format(self.IO_SERVICE,self.PIN_MODE,pin, mode))

    # A method to write to a digital pin
    def digital_write(self, pin, value):
        self.__out.write("{},{},{},{}\n".format(self.IO_SERVICE, self.DIGITAL_WRITE,pin,value))
        if self.DEBUG:
            sys.stdout.write(
                "DEBUG: Setting digital pin with {},{},{},{}\n".format(self.IO_SERVICE,self.DIGITAL_WRITE,pin,value))

    # A method to write to an analog pin
    def analog_write(self, pin, value):
        self.__out.write("{},{},{},{}\n".format(self.IO_SERVICE,self.ANALOG_WRITE,pin,value))
        if self.DEBUG:
            sys.stdout.write(
                "DEBUG: Setting analog pin with {},{},{},{}\n".format(self.IO_SERVICE,self.DIGITAL_WRITE,pin,value))

    # A method to set the autoreport interval (in ms)
    def set_auto_report_interval(self, interval):
        self.__out.write("{},{},{}\n".format(self.IO_SERVICE,self.ANALOG_DATA_REQUEST,interval))
        if self.DEBUG:
            sys.stdout.write(
                "DEBUG: Setting autoreport interval {},{},{}\n".format(self.IO_SERVICE,self.ANALOG_DATA_REQUEST,interval))

    # It is possible to add a service at run-time:
    def add_service(self, service_id, asip_service):
        # If there is already a service with the same ID, we add this new one to the list:
        if service_id in self.__services:
            self.__services[service_id].append(asip_service)
            #self.__services[service_id] = asip_service
        # otherwise, we create a new list, a new key for the dictionary and associate the list to that key
        else:
            new_list = [asip_service]
            self.__services.update({service_id: new_list})

    # FIXME: maybe with python the following method is unuseful (Does the previous do the same?)
    # It is possible to add a list of services at run-time:
    def add_services(self, service_id, asip_ser_list):
        # we create a new key for the dictionary and associate the list to that key
        self.__services.update({service_id: asip_ser_list})

    # Just return the list of services
    def get_services(self):
        return self.__services

    # I'm not sure we want this public... FIXME?
    def get_digital_pins(self):
        return self.__port_map.get_digital_pins()

    # Getter and Setter for output channel
    def get_asip_writer(self):
        return self.__out

    def set_asip_writer(self, w):
        self.__out = w
        
    def isVersionOk(self):
        return self.__AsipVersionOk

    # ************ END PUBLIC METHODS *************

    # ************ BEGIN PRIVATE METHODS *************

    # A method to do what is says on the tin...
    def __handle_input_event(self, input_str):   
        #print("mm: received message {}\n".format(input_str))    
        if self.DEBUG:
            sys.stdout.write("DEBUG: received message {}\n".format(input_str))

        if input_str[1] == self.IO_SERVICE:
            # Digital pins (in port)

            # the port data event is something like: @I,P,4,F
            # this message says the data on port 4 has a value of F
            if input_str[3] == self.PORT_DATA:
                self.__port_map.process_port_data(input_str)
            elif input_str[3] == self.PORT_MAPPING:
                self.__port_map.process_pin_mapping(input_str)
            elif input_str[3] == self.ANALOG_VALUE:
                self.__port_map.process_analog_data(input_str)

            # TODO: implement missing messages!
            else:
                if self.DEBUG:
                    sys.stdout.write("DEBUG: Service not recognised in position 3 for I/O service: {}\n".format(input_str))
            # end of IO_SERVICE
            
        elif input_str[1] == self.SYSTEM_MSG_HEADER:      
            if input_str[3] == self.SYSTEM_GET_INFO:
                field = input_str[5:].split(',')   #extract info fields
                info = 'ASIP version %s.%s running on %s using sketch: %s\n' % (field[0], field[1],field[2], field[4])
                self.__AsipVersionOk = True   #TODO - check that the major version (field[0]) is supported by this client 
                print(info)            

        elif input_str[1] in self.__services.keys():
            # Is this one of the services we know? If this is the case, we call it and we process the input
            # I want a map function here!! For the moment we use a for loop...
            for s in self.__services[input_str[1]]:
                s.process_response(input_str)
                if self.DEBUG:
                    sys.stdout.write("DEBUG: calling process response for key {} and input {}\n".format(s,input))     
        else:
            # We don't know what to do with it.
            if self.DEBUG:
                sys.stdout.write("DEBUG: Event not recognised at position 1: {}\n".format(input_str))

    # To handle a message starting with an error header (this is a form of error reporting from Arduino)
    def __handle_input_error(self, input_str):
        # FIXME: improve error handling
         print("Error message received: {}\n".format(input_str))

    # For the moment we just report board's debug messages on screen
    # FIXME: do something smarter?
    def __handle_debug_event(self, input_str):
        print("dbg msg: {}\n".format(input_str))

    # ************ END PRIVATE METHODS *************/


# ************ TESTING *************
# A simple main method to test off-line


def main():
    test_client = AsipClient()
    test_client.process_input("@I,M,20{4:1,4:2,4:4,4:8,4:10,4:20,4:40,4:80,2:1,2:2,2:4,2:8,2:10,2:20,3:1,3:2,3:4,3:8,3:10,3:20}")
    test_client.process_input("@I,p,4,F")
    test_client.process_input("@I,p,4,10")
    test_client.process_input("@I,p,4,FF")

# De-comment to test this class
#main()


