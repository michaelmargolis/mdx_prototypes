__author__ = 'Gianluca Barbon'

import time
import sys
import glob
import serial
import socket
from threading import Thread
import threading
from serial import Serial
#try:
from Queue import Queue
#except ImportError:
#    from queue import Queue


class TCPBridge:

    # ************   BEGIN CONSTANTS DEFINITION ****************

    DEBUG = True
    TCP_IP = '127.0.0.1' #socket.gethostname()
    TCP_PORT = 5005
    BUFFER_SIZE = 20  # Normally 1024, 20 grants fast response

    # ************   END CONSTANTS DEFINITION ****************

    # ************   BEGIN PRIVATE FIELDS DEFINITION ****************

    ser_conn = None  # self board uses serial communication
    asip = None  # The client for the aisp protocol
    queue = Queue(10)  # Buffer # TODO: use pipe instead of queue for better performances
    #  FIXME: fix Queue dimension?
    _port = "" #serial port
    _ports = [] #serial ports array
    __running = False

    # ************   END PRIVATE FIELDS DEFINITION ****************

    # self constructor takes the name of the serial port and it creates a Serial object
    # Here the serial listener and the queue reader are started
    def __init__(self):
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
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ip_retrieve()
            self.s.bind((self.TCP_IP, self.TCP_PORT))
            self.s.listen(1) #states the max number of clients that can connect simultaneously
            sys.stdout.write("Server created with IP: {} and PORT: {}\n".format(self.TCP_IP,self.TCP_PORT))
        except Exception as e:
            #TODO: improve exception handling
            sys.stdout.write("Exception: caught {} while creating socket\n".format(e))

    # ************ BEGIN PUBLIC METHODS *************

    def run(self):
        while True:
            try:
                conn, addr = self.s.accept()
                sys.stdout.write("Connection accepted, connection address: {}\n".format(addr))
                worker = []
                worker.append(self.ListenerThread(self.queue, self.ser_conn))
                worker.append(self.ConsumerThread(self.queue, conn))
                worker.append(self.WriterThread(self, conn))
                for i in worker:
                    print("Starting {}".format(i))
                    i.start()
                #time.sleep(1)
                sys.stdout.write("Threads created\n")
                time.sleep(5)
                while len(threading.enumerate()) == 4: # main thread + listener + consumer + writer
                    # print("we are 3")
                    pass
                print("less than 3 now")
                for i in worker:
                    #try:
                    i.event.set()
                    print("JUST killed {}".format(i))
                    #except: pass
                for i in worker:
                    i.join()
                    print("JUST joined thread {}".format(i))
                print("All terminated")

            except Exception as e:
                #TODO: improve exception handling
                sys.stdout.write("Exception: caught {} while launching threads\n".format(e))

    # ************ END PUBLIC METHODS *************


    # ************ BEGIN PRIVATE METHODS *************

    def ip_retrieve(self):
        #print([(s.connect(('192.168.0.1', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
        self.TCP_IP = [(s.connect(('192.168.0.1', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

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
        DEBUG = False

        def __init__(self, parent, conn):
            Thread.__init__(self)
            self.parent = parent
            self.conn = conn
            self.event = threading.Event()

        # val is a string
        # TODO: improve try catch
        def run(self):
            print("Run writer thread")
            write_buffer = ""
            #while self.running:
            while not self.event.is_set():
                #try:
                data = self.conn.recv(self.BUFFER_SIZE)
                #except:
                #    print("****** Killing from Writer ******")
                # data = data.encode('utf-8')
                if self.DEBUG:
                    sys.stdout.write("DEBUG: Received data from TCP/IP: {}\n".format(data))
                if data != '\r' and data != '\n' and data !=' ' and data is not None: # ignore empty lines
                    if "\n" in data:
                        # If there is at least one newline, we need to process
                        # the message (the buffer may contain previous characters).
                        while ("\n" in data and len(data) > 0):
                            # But remember that there could be more than one newline in the buffer
                            write_buffer += (data[0:data.index("\n")])
                            if self.DEBUG:
                                sys.stdout.write("Serial write buffer is now {}\n".format(write_buffer))

                            #Serial send starts here
                            if self.parent.ser_conn.isOpen():
                                try:
                                    temp = write_buffer.encode()
                                    self.parent.ser_conn.write(temp)
                                    if self.DEBUG:
                                        sys.stdout.write("DEBUG: just wrote in serial {}\n".format(temp))
                                except (OSError, serial.SerialException):
                                    pass
                            else:
                                raise serial.SerialException

                            write_buffer = ""
                            if data[data.index("\n")+1:]=='\n':
                                data = ''
                                break
                            else:
                                data = data[data.index("\n")+1:]
                        if len(data)>0 and data not in ('\r','\n',' '):
                            write_buffer = data
                    else:
                        write_buffer += data

            print("STOPPING writer")


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
            #print("Run!")
            # temp_buff = ""
            #time.sleep(2)
            # TODO: implement ser.inWaiting() >= minMsgLen to check number of char in the receive buffer?
            # serBuffer = ""

            #while self.running:
            while not self.event.is_set():
                #print ("inside first while")
                # #if self.DEBUG:
                # #    sys.stdout.write("DEBUG: Temp buff is now {}\n".format(temp_buff))
                # time.sleep(0.1)
                # val = self.ser_conn.readline()
                # #val = self.ser_conn.read()
                # if self.DEBUG:
                #     sys.stdout.write("DEBUG: val value when retrieving from serial is {}\n".format(val))
                # val = val.decode('utf-8', errors= 'ignore')
                # if self.DEBUG:
                #     sys.stdout.write("DEBUG: val value after decode is {}".format(val))
                # if val is not None and val!="\n" and val!=" ":
                #     if "\n" in val:
                #         # If there is at least one newline, we need to process
                #         # the message (the buffer may contain previous characters).
                #
                #         while ("\n" in val and len(val) > 0):
                #             # But remember that there could be more than one newline in the buffer
                #             temp_buff += (val[0:val.index("\n")])
                #             self.queue.put(temp_buff)
                #             if self.DEBUG:
                #                 sys.stdout.write("DEBUG: Serial produced {}\n".format(temp_buff))
                #             temp_buff = ""
                #             val = val[val.index("\n")+1:]
                #             if self.DEBUG:
                #                 sys.stdout.write("DEBUG: Now val is {}\n".format(val))
                #         if len(val)>0:
                #             temp_buff = val
                #         if self.DEBUG:
                #             sys.stdout.write("DEBUG: After internal while buffer is {}\n".format(temp_buff))
                #     else:
                #         temp_buff += val
                #         if self.DEBUG:
                #             sys.stdout.write("DEBUG: else case, buff is equal to val, so they are {}\n".format(temp_buff))

                # try:
                #     while True:
                #         #print("before serial conn")
                #         c = self.ser_conn.read() # attempt to read a character from Serial
                #         c = c.decode('utf-8', errors= 'ignore')
                #         #was anything read?
                #         #print("start reading")
                #         if len(c) == 0:
                #             break
                #
                #         # check if character is a delimiter
                #         if c == '\r':
                #             c = '' # ignore CR
                #         elif c == '\n':
                #             serBuffer += "\n" # add the newline to the buffer
                #             if self.DEBUG:
                #                 sys.stdout.write("Serial buffer is now {}\n".format(serBuffer))
                #             self.queue.put(serBuffer)
                #             serBuffer = '' # empty the buffer
                #         else:
                #             #print("Try to print: {}".format(c))
                #             serBuffer += c # add to the buffer
                # except (OSError, serial.SerialException):
                #     self.running = False
                #     if self.DEBUG:
                #         sys.stdout.write("Serial Exception in listener\n")
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

        queue = None
        asip = None
        DEBUG = False

        # overriding constructor
        def __init__(self, queue, conn):
            Thread.__init__(self)
            self.queue = queue
            self.conn = conn
            self.event = threading.Event()
            if self.DEBUG:
                sys.stdout.write("DEBUG: consumer thread created \n")

        # overriding run method, thread activity
        def run(self):
            #while self.running:
            while not self.event.is_set():
                temp = self.queue.get()
                try:
                    self.conn.send(temp)
                    #print("Just sent via tcp/ip {}".format(temp))
                except:
                    pass
                    #print("****** Killing from Consumer ******")
                    #self.kill()
                self.queue.task_done()
                # if temp == "\n":
                    # print("WARNING")
                # print ("Consumed", temp)
            print("Stopping consumer")

    # ************ END PRIVATE CLASSES *************

# method for testing is called
if __name__ == "__main__":
    TCPBridge().run()