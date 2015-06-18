__author__ = 'Gianluca Barbon'

import time
import sys
import glob
import serial
from threading import Thread
import threading
import paho.mqtt.client as mqtt
from serial import Serial


class MQTTBridge:

    # ************   BEGIN CONSTANTS DEFINITION ****************

    DEBUG = True
    __SERIAL_TIMEOUT = 2  # serial timeout (avoid blocking in case of issues)
    __PORT_INDEX_TO_OPEN = 0
    __BAUD_RATE = 57600
    __TCP_port = 1883

    # ************   END CONSTANTS DEFINITION ****************

    # ************   BEGIN PRIVATE FIELDS DEFINITION ****************

    # __ser_conn: self board uses serial communication
    __ports = []  # serial ports array
    # __sock_obj: tcp/ip socket communication
    __threads = []  # List of threads

    # ************   END PRIVATE FIELDS DEFINITION ****************

    # self constructor takes the name of the serial port and it creates a Serial object
    # Here the serial listener and the queue reader are started
    def __init__(self, broker_ip, board_id, keepalive=180):

        # serial init
        try:
            self.__ser_conn = Serial()
            self.serial_port_finder(self.__PORT_INDEX_TO_OPEN)
            sys.stdout.write("Setting Serial: attempting to open {}\n".format(self.__ports[self.__PORT_INDEX_TO_OPEN]))
            self.open_serial(self.__ports[self.__PORT_INDEX_TO_OPEN], self.__BAUD_RATE)
            sys.stdout.write("Setting Serial: serial port {} opened\n".format(self.__ports[self.__PORT_INDEX_TO_OPEN]))
        except serial.SerialException as e:
            sys.stdout.write("Exception while init serial connection: {}\n".format(e))
            sys.exit(1)

        # setting mqtt connection and asip protocol
        try:
            sys.stdout.write("Setting mqtt: attempting to connect to broker {}\n".format(broker_ip))
            self.__Broker = broker_ip
            self.__keepalive = keepalive
            self.__SUBTOPIC = "asip/"+board_id+"/out"
            self.__PUBTOPIC = "asip/"+board_id+"/in"

            self.mqtt_client = mqtt.Client(board_id)
            self.mqtt_client.on_connect = self.on_connect
            self.connect()

        except Exception as e:
            sys.stdout.write("Exception caught in init mqtt protocol: {}\n".format(e))
            try:  # try to close connection
                self.disconnect()
            except Exception as e:
                sys.stdout.write("Caught generic exception while disconnecting MQTT: {}\n".format(e))
            finally:
                sys.exit(1)

    # ************ BEGIN PUBLIC METHODS *************

    def run(self):
        try:
            self.__threads.append(self.ListenerThread(self.__ser_conn, self.mqtt_client, self.__PUBTOPIC, self.DEBUG))
            self.__threads.append(self.WriterThread(self.__ser_conn, self.mqtt_client, self.__SUBTOPIC, self.DEBUG))
            sys.stdout.write("Creating Threads: starting\n")
            for i in self.__threads:
                i.start()  # starting each thread
            all_alive = False
            while not all_alive:  # checking that every thread is alive
                # TODO: improve syntax in following line
                if self.__threads[0].is_alive() and self.__threads[1].is_alive():
                    all_alive = True
            active_workers = threading.active_count()
            sys.stdout.write("Creating Threads: all threads created and alive\n")

            self.mqtt_client.loop_start()  # starting mqtt loop

        except Exception as e:
            sys.stdout.write("Caught exception in threads launch: {}\n".format(e))
            self.thread_killer()
            sys.exit(1)
        else:
            # Running
            try:
                # checking that a thread is not killed by an exception
                while len(threading.enumerate()) == active_workers:
                    time.sleep(0.005)
           # KeyboardInterrupt handling in order to close every thread correctly
            except KeyboardInterrupt:  # KeyboardInterrupt handling in order to close every thread correctly
                sys.stdout.write("KeyboardInterrupt while checking mapping. Attempting to close listener thread.\n")
                self.thread_killer()
                sys.exit()
            except Exception as e:  # killing threads and exiting in case of generic exception
                sys.stdout.write("Caught generic exception while checking mapping: {}\n".format(e))
                self.thread_killer()
                sys.exit(1)

    # ************ END PUBLIC METHODS *************


    # ************ BEGIN PRIVATE METHODS *************

    # stops and wait for the join for threads in the given pool
    # TODO: improve in case of timeout of the join
    def thread_killer(self):
        for i in self.__threads:
            try:
                i.stopper()
                sys.stdout.write("Killing Threads: event for {} successfully set\n".format(i))
            except Exception as e:
                sys.stdout.write("Caught exception while stropping thread {}.\nException is: {}\n".format(i, e))
        time.sleep(0.5)
        sys.stdout.write("Killing Threads: waiting for join\n")
        for i in self.__threads:
            i.join()
            sys.stdout.write("Killing Threads: thread {} successfully closed\n".format(i))
        self.__threads = []
        sys.stdout.write("All threads terminated.\n")
        try:
            self.disconnect()
        except Exception as e:
            sys.stdout.write("Caught generic exception while disconnecting MQTT: {}\n".format(e))
        sys.stdout.write("All threads terminated.\n")
        return True

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        if self.DEBUG:
            sys.stdout.write("Connected with result code: {}\n".format(rc))

    def connect(self):
        self.mqtt_client.connect(self.__Broker, self.__TCP_port, self.__keepalive)
        sys.stdout.write("Connected to MQTT broker: {}  port: {} keepalive: {} .\n"
                         .format(self.__Broker, self.__TCP_port, self.__keepalive))

    def disconnect(self):
        self.mqtt_client.disconnect()
        sys.stdout.write("Disconnected from MQTT broker.\n")

    def open_serial(self, port, baud_rate):
        if self.__ser_conn.isOpen():
            self.__ser_conn.close()
        self.__ser_conn.port = port
        self.__ser_conn.baudrate = baud_rate
        self.__ser_conn.timeout = self.__SERIAL_TIMEOUT
        self.__ser_conn.open()
        # Toggle DTR to reset Arduino
        self.__ser_conn.setDTR(False)
        time.sleep(1)
        # toss any data already received, see
        self.__ser_conn.flushInput()
        time.sleep(1)
        self.__ser_conn.setDTR(True)
        time.sleep(1)

    def close_serial(self):
        self.__ser_conn.close()

    # This methods retrieves the operating system and set the Arduino serial port
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    # TODO: test needed for linux and windows implementation
    def serial_port_finder(self, desired_index):

        system = sys.platform
        if system.startswith('win'):
            temp_ports = ['COM' + str(i + 1) for i in range(255)]
        elif system.startswith('linux'):
            # this is to exclude your current terminal "/dev/tty"
            temp_ports = glob.glob('/dev/tty[A-Za-z]*')
        elif system.startswith('darwin'):
            temp_ports = glob.glob('/dev/tty.usbmodem*')
            cp2104 = glob.glob('/dev/tty.SLAB_USBtoUART')  # append usb to serial converter cp2104
            ft232rl = glob.glob('/dev/tty.usbserial-A9MP5N37')  # append usb to serial converter ft232rl
            fth = glob.glob('/dev/tty.usbserial-FTHI5TLH')  # append usb to serial cable
            #new = glob.glob('/dev/tty.usbmodemfd121')
            #temp_ports = glob.glob('/dev/tty.SLAB_USBtoUART')
            #temp_ports = glob.glob('/dev/tty.usbserial-A9MP5N37')
            if cp2104 is not None:
                temp_ports += cp2104
            if ft232rl is not None:
                temp_ports += ft232rl
            if fth is not None:
                temp_ports += fth
            #if new is not None: # FIXME: REMOVE!!! Only used for tests
            #    temp_ports = new
        else:
            raise EnvironmentError('Unsupported platform')

        for port in temp_ports:
            try:
                self.__ser_conn.port = port
                self.__ser_conn.open()
                self.__ser_conn.close()
                self.__ports.append(port)
                if len(self.__ports) > desired_index:
                    return  # we have found the desired port
            except serial.SerialException:
                pass
        if self.DEBUG:
            sys.stdout.write("DEBUG: available ports are {}\n".format(self.__ports))

    # ************ END PRIVATE METHODS *************

    # ************ BEGIN PRIVATE CLASSES *************

    # WriterThread writes messages to the serial port.
    class WriterThread(Thread):

        def __init__(self, ser_conn, mqtt_client, subtopic, debug=False):
            Thread.__init__(self)
            self.mqtt_client = mqtt_client
            self.mqtt_client.on_message = self.on_message
            self.ser_conn = ser_conn
            self.subtopic = subtopic
            self.DEBUG = debug
            self.writer_buffer = ""
            self.mqtt_client.subscribe(topic=subtopic)
            sys.stdout.write("Writer Thread: subscribed to topic: {} .\n".format(subtopic))
            self._stopper = threading.Event()
            sys.stdout.write("Writer Thread: thread process created.\n")

        # if needed, kill will stops the loop inside run method
        def stopper(self):
            sys.stdout.write("Writer Thread: now stopping.\n")
            self._stopper.set()

        # The callback for when a PUBLISH message is received from the server.
        def on_message(self, client, userdata, msg):
            try:
                if not msg.payload:
                    pass
                else:
                    data = msg.payload.decode('utf-8')
                    if data != '\r' and data != '\n' and data != ' ':  # ignore empty lines
                        self.writer_buffer += data
                    if self.DEBUG:
                        sys.stdout.write("DEBUG: Received {}\n".format(data))
            except Exception as e:
                sys.stdout.write("Exception in writer on_message method: {}\nWriter will now stop\n".format(e))
                self.stopper()

        # overriding run method, thread activity
        def run(self):
            time.sleep(2)  # TODO: maybe reduce this sleep?
            sys.stdout.write("Writer Thread: now running.\n")
            while not self._stopper.is_set():
                time.sleep(0.001)  # TODO: thread concurrency
                try:
                    # If there is at least one newline, we need to process the message
                    # (the buffer may contain previous characters).
                    while "\n" in self.writer_buffer:
                        temp = self.writer_buffer[0:self.writer_buffer.index("\n")]
                        temp += '\n'
                        self.ser_conn.write(temp.encode())
                        self.writer_buffer = self.writer_buffer[self.writer_buffer.index("\n")+1:]
                except Exception as e:
                    sys.stdout.write("Exception in writer run method: {}\nWriter will now stop\n".format(e))
                    self.stopper()

    # ListenerThread read the serial stream and send the message to the mqtt stream
    class ListenerThread(Thread):

        # overriding constructor
        def __init__(self, ser_conn, mqtt_client, pubtopic, debug=False):
            Thread.__init__(self)
            self.mqtt_client = mqtt_client
            self.ser_conn = ser_conn
            self.pubtopic = pubtopic
            self.DEBUG = debug
            self._stopper = threading.Event()
            sys.stdout.write("Listener Thread: thread process created.\n")

        # if needed, kill will stops the loop inside run method
        def stopper(self):
            sys.stdout.write("Listener Thread: now stopping.\n")
            self._stopper.set()

        # overriding run method, thread activity
        def run(self):
            time.sleep(0.5)  # TODO: 2 sec, maybe reduce this sleep?
            sys.stdout.write("Listener Thread: now running.\n")
            ser_buffer = ""
            while not self._stopper.is_set():
                try:
                    c = self.ser_conn.read()  # attempt to read a character from Serial
                    c = c.decode('utf-8', errors='ignore')
                    if len(c) == 0:  # was anything read?
                        if self.DEBUG:
                            sys.stdout.write("DEBUG: nothing from serial\n")
                        pass
                    else:
                        #if self.DEBUG:
                        #    sys.stdout.write("DEBUG: Char from serial: {}\n".format(c))
                        if c == '\n' or c == '\n':
                            if len(ser_buffer) > 0:
                                ser_buffer += '\n'
                                # self.sock_conn.send(ser_buffer.encode())
                                self.mqtt_client.publish(self.pubtopic, ser_buffer)
                                if self.DEBUG:
                                    sys.stdout.write("DEBUG: Complete message from serial: {}\n".format(ser_buffer))
                            ser_buffer = ""
                        else:
                            ser_buffer += c
                except serial.SerialTimeoutException as e:
                    sys.stdout.write(
                        "Caught SerialTimeoutException in serial read: {}\n".format(e))
                    continue  # Continue to next iteration in case of serial timeout
                except serial.SerialException as e:
                    sys.stdout.write(
                        "Caught SerialException in serial read: {}\nListener Thread will now stop\n".format(e))
                    self.stopper()
                except Exception as e:
                    sys.stdout.write("Caught exception: {}\nListener Thread will now stop\n".format(e))
                    self.stopper()

            sys.stdout.write("Listener Thread: stopped\n")

    # ************ END PRIVATE CLASSES *************

# method for running is called
if __name__ == "__main__":
    MQTTBridge( "192.168.0.100","board4").run()