__author__ = 'Gianluca Barbon'

import time
import sys
import glob
import serial
from threading import Thread
import threading
import paho.mqtt.client as mqtt
from serial import Serial
#try:
from Queue import Queue
#except ImportError:
#    from queue import Queue


class MQTTBridge:

    # ************   BEGIN CONSTANTS DEFINITION ****************

    DEBUG = True
    TCP_IP = '127.0.0.1' #socket.gethostname()
    BUFFER_SIZE = 20  # Normally 1024, 20 grants fast response

    # ************   END CONSTANTS DEFINITION ****************

    # ************   BEGIN PRIVATE FIELDS DEFINITION ****************

    ser_conn = None  # self board uses serial communication
    queue = Queue(10)  # Buffer # TODO: use pipe instead of queue for better performances
    #  FIXME: fix Queue dimension?
    # _port = "" #serial port
    _ports = [] #serial ports array
    __running = False
    _TCPport = 1883

    # ************   END PRIVATE FIELDS DEFINITION ****************

    # self constructor takes the name of the serial port and it creates a Serial object
    # Here the serial listener and the queue reader are started
    def __init__(self, broker_ip, board_id):
        try:
            self.ser_conn = Serial()
            portIndexToOpen = 0
            self.serial_port_finder(portIndexToOpen)
            sys.stdout.write("Attempting to open serial port {}\n".format(self._ports[portIndexToOpen]))
            self.open_serial(self._ports[0], 57600)
            sys.stdout.write("Serial port {} opened\n".format(self._ports[0]))
        except Exception as e:
            sys.stdout.write("Exception: caught {} while init serial and asip protocols\n".format(e))

        try:
            self._BrokerIP = broker_ip
            self._BoardID = "Board_"+board_id
            self._PUBTOPIC = "asip/"+board_id+"/out"
            self._SUBTOPIC = "asip/"+board_id+"/in"
            self.mqtt_client = mqtt.Client(self._BoardID)
            self.mqtt_client.on_connect = self.on_connect
            self.connect()
            sys.stdout.write("****\nThis is board {}\nConnected to broker with IP {}\nSubscribed to topic {}\nWill publish in topic {}\n****\n"
                             .format(self._BoardID, self._BrokerIP, self._SUBTOPIC, self._PUBTOPIC))
        except Exception as e:
            #TODO: improve exception handling
            sys.stdout.write("Exception: caught {} while creating socket\n".format(e))

    # ************ BEGIN PUBLIC METHODS *************

    def sub_test(self):
        print("Test")
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.subscribe(topic="asip/#")
        self.mqtt_client.loop_start()

    def test(self, seconds):
        self.mqtt_client.loop_start()
        time.sleep(seconds)

    def run(self):
        try:
            worker = []
            worker.append(self.ListenerThread(self.queue, self.ser_conn))
            worker.append(self.ConsumerThread(self.queue, self.mqtt_client, self._PUBTOPIC))
            worker.append(self.WriterThread(self.ser_conn, self.mqtt_client, self._SUBTOPIC))
            for i in worker:
                print("Starting {}".format(i))
                i.start()
            #time.sleep(1)
            sys.stdout.write("Threads created\n")
            self.mqtt_client.loop_start()
            # time.sleep(5)
            # while len(threading.enumerate()) == 5: # main thread + listener + consumer + writer + mqtt?
            #     # print("we are 3")
            #     pass
            # print("less than 3 now")
            # for i in worker:
            #     #try:
            #     i.event.set()
            #     print("JUST killed {}".format(i))
            #     #except: pass
            # for i in worker:
            #     i.join()
            #     print("JUST joined thread {}".format(i))
            # print("All terminated")

        except Exception as e:
            #TODO: improve exception handling
            sys.stdout.write("Exception: caught {} while launching threads\n".format(e))

    # ************ END PUBLIC METHODS *************


    # ************ BEGIN PRIVATE METHODS *************
    def on_message(self, client, userdata, msg):
            print("On message")
            if not msg.payload:
                pass
            else:
                print("Payload {}".format(msg.payload.decode('utf-8')))

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        if self.DEBUG:
            sys.stdout.write("DEBUG: Connected with result code {}\n".format(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        #self.mqtt_client.subscribe("$SYS/#")
        #self.mqtt_client.subscribe(self._SUBTOPIC)

    def connect(self):
        if self.DEBUG:
            sys.stdout.write("DEBUG: Connecting to mqtt broker {} on port {}\n".format(self._BrokerIP,self._TCPport))
        self.mqtt_client.connect(self._BrokerIP, self._TCPport, 180)

    def sendData(self, msg):
        self.mqtt_client.publish(self._PUBTOPIC, msg)

    def disconnect(self):
        if self.DEBUG:
            sys.stdout.write("DEBUG: DEBUG: Disconnected from mqtt")
        self.mqtt_client.disconnect()


    def open_serial(self, port, baudrate):
        if self.ser_conn.isOpen():
            self.ser_conn.close()
        self.ser_conn.port = port
        self.ser_conn.baudrate = baudrate
        #self.ser_conn.timeout = None # 0 or None?
        self.ser_conn.open()
        # Toggle DTR to reset Arduino
        self.ser_conn.setDTR(False)
        time.sleep(1)
        # toss any data already received, see
        self.ser_conn.flushInput()
        time.sleep(1)
        self.ser_conn.setDTR(True)
        time.sleep(1)

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
        system = sys.platform
        if system.startswith('win'):
            temp_ports = ['COM' + str(i + 1) for i in range(255)]
        elif system.startswith('linux'):
            # this is to exclude your current terminal "/dev/tty"
            temp_ports = glob.glob('/dev/tty[A-Za-z]*')
        elif system.startswith('darwin'):
            temp_ports = glob.glob('/dev/tty.usbmodem*')
            cp2104 = glob.glob('/dev/tty.SLAB_USBtoUART') # append usb to serial converter cp2104
            ft232rl = glob.glob('/dev/tty.usbserial-A9MP5N37') # append usb to serial converter ft232rl
            fth = glob.glob('/dev/tty.usbserial-FTHI5TLH') # append usb to serial cable
            if cp2104 is not None:
                temp_ports += cp2104
            if ft232rl is not None:
                temp_ports += ft232rl
            if fth is not None:
                temp_ports += fth
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
    class WriterThread(Thread):
        BUFFER_SIZE = 1024
        DEBUG = True
        #sub_buff = ""

        def __init__(self, ser_conn, mqtt_client, sub_topic):
            Thread.__init__(self)
            self.ser_conn = ser_conn
            self.mqtt_client = mqtt_client
            self.mqtt_client.on_message = self.on_message
            self.sub_topic = sub_topic
            self.write_buffer = ""
            self.event = threading.Event()
            print("Sub topic is {}".format(self.sub_topic))
            self.mqtt_client.subscribe(topic=sub_topic)

        # The callback for when a PUBLISH message is received from the server.
        def on_message(self, client, userdata, msg):
            print("On message")
            if not msg.payload:
                pass
            else:
                data = msg.payload.decode('utf-8')
                print("Payload is {}".format(data))
                self.ser_conn.write(data.encode())

        # def run(self):
        #     while not self.event.is_set():
        #         pass
        #     self.mqtt_client.on_message = None

    # ListenerThread and ConsumerThread are implemented following the Producer/Consumer pattern
    # A class for a listener that rad the serial stream and put incoming messages on a queue
    # TODO: implement try catch
    class ListenerThread(Thread):

        DEBUG = True

        # overriding constructor
        def __init__(self, queue, ser_conn):
            Thread.__init__(self)
            self.queue = queue
            self.ser_conn = ser_conn
            self.event = threading.Event()
            if self.DEBUG:
                sys.stdout.write("DEBUG: serial thread process created \n")

        # overriding run method, thread activity
        def run(self):
            while not self.event.is_set():
                temp = ""
                while True:
                    c = self.ser_conn.read() # attempt to read a character from Serial
                    c = c.decode('utf-8', errors= 'ignore')
                    if c=='\n' or c=='\n':
                        if len(temp)>0:
                            temp += '\n'
                            self.queue.put(temp)
                            #print("temp is now {}".format(temp))
                        break
                    else:
                        temp += c

            print("Stopping Listener")

    # A class that reads the queue and launch the processInput method of the AispClient.
    class ConsumerThread(Thread):

        DEBUG = True

        # overriding constructor
        def __init__(self, queue, mqtt_client, pub_topic):
            Thread.__init__(self)
            self.queue = queue
            self.mqtt_client = mqtt_client
            self.pub_topic = pub_topic
            self.event = threading.Event()
            if self.DEBUG:
                sys.stdout.write("DEBUG: consumer thread created \n")

        # overriding run method, thread activity
        def run(self):
            while not self.event.is_set():
                temp = self.queue.get()
                self.mqtt_client.publish(self.pub_topic,temp)
                self.queue.task_done()
            print("Stopping consumer")

    # ************ END PRIVATE CLASSES *************

# method for testing is called
if __name__ == "__main__":
    #MQTTBridge( "127.0.0.1","test").test(300)
    temp = MQTTBridge( "192.168.0.103","test")
    temp.run()
    #temp.sub_test()