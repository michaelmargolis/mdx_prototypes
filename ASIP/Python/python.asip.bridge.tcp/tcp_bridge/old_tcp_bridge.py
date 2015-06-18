__author__ = 'Gianluca Barbon'

import time
import sys
import glob
import serial
import socket
import os
import pipes
from threading import Thread
import threading
from serial import Serial
try:
    from Queue import Queue
    from Queue import Empty
except ImportError:
    from queue import Queue
    from queue import Empty


class TCPBridge:

    # ************   BEGIN CONSTANTS DEFINITION ****************

    DEBUG = False
    TCP_IP = '127.0.0.1' #socket.gethostname()
    TCP_PORT = 5005
    BUFFER_SIZE = 20  # Normally 1024, 20 grants fast response
    __RECV_TIMEOUT = 2 # socket receive timeout in second
    __SERIAL_TIMEOUT = 2 # serial timeout (avoid blocking in case of issues)

    # ************   END CONSTANTS DEFINITION ****************

    # ************   BEGIN PRIVATE FIELDS DEFINITION ****************

    ser_conn = None  # self board uses serial communication
    asip = None  # The client for the aisp protocol
    queue = Queue(10)  # Buffer # TODO: use pipe instead of queue for better performances
    pipe = pipes.Template()
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
            self.open_serial_simple(self._ports[0], 57600)
            sys.stdout.write("Serial port {} opened\n".format(self._ports[0]))
        except Exception as e:
            sys.stdout.write("Exception while init serial connection: {}\n".format(e))
            sys.exit(1)

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ip_retrieve()
            self.s.bind((self.TCP_IP, self.TCP_PORT))
            self.s.listen(1) #states the max number of clients that can connect simultaneously
            sys.stdout.write("Server created with IP: {} and PORT: {}\n".format(self.TCP_IP,self.TCP_PORT))
        except Exception as e:
            #TODO: improve exception handling
            sys.stdout.write("Exception while creating socket: {}\n".format(e))
            sys.exit(1)

    # ************ BEGIN PUBLIC METHODS *************

    def run(self):
        while True:
            worker = []
            try:
                conn, addr = self.s.accept()
                sys.stdout.write("Connection accepted, connection address: {}\n".format(addr))
                worker.append(self.ListenerThread(self.queue, self.ser_conn))
                worker.append(self.ConsumerThread(self.queue, conn))
                worker.append(self.WriterThread(self, conn, self.__RECV_TIMEOUT))
                for i in worker:
                    if self.DEBUG:
                        print("Starting {}".format(i))
                    i.start() # starting each thread
                all_alive = False
                while not all_alive: # cheching that every thread is alive
                    # TODO: improve syntax in following line
                    if worker[0].is_alive() and worker[1].is_alive() and worker[2].is_alive():
                        all_alive = True
                active_workers = threading.active_count()
                sys.stdout.write("All threads created and alive\n")
            except Exception as e:
                sys.stdout.write("Caught exception in thread launch: {}".format(e))
                self.thread_killer(worker)
                sys.exit(1)
            else:
                try:
                    # checking that a thread is not killed by an exception
                    while len(threading.enumerate()) == active_workers:
                        pass
                # KeyboardInterrupt handling in order to close every thread correctly
                except KeyboardInterrupt:
                    sys.stdout.write("KeyboardInterrupt: attempting to close threads.\n")
                    # killing thread in case of keyboardinterrupt
                    self.thread_killer(worker)
                    sys.stdout.write("All terminated.\n")
                    sys.exit()
                # killing in case of exception in one of the thread: this allows to wait for a new connection
                else:
                    self.thread_killer(worker)
                    sys.stdout.write("All terminated. Waiting for new connection.\n")

    # ************ END PUBLIC METHODS *************


    # ************ BEGIN PRIVATE METHODS *************

    # stops and wait for the join for threads in the given pool
    # TODO: improve in case of timeout of the join
    def thread_killer(self, thread_pool):
        for i in thread_pool:
            i.stop()
            if self.DEBUG:
                sys.stdout.write("Event for {} successfully set\n".format(i))
        sys.stdout.write("Waiting for join\n")
        for i in thread_pool:
            i.join()
            if self.DEBUG:
                sys.stdout.write("Thread {} successfully closed\n".format(i))
        return True

    def ip_retrieve(self):
        #print([(s.connect(('192.168.0.1', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])
        self.TCP_IP = [(s.connect(('192.168.0.1', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

    def open_serial(self, port, baudrate):
        if self.ser_conn.isOpen():
            self.ser_conn.close()
        self.ser_conn.port = port
        self.ser_conn.baudrate = baudrate
        #self.ser_conn.timeout = None # 0 or None?
        self.ser_conn.timeout = self.__SERIAL_TIMEOUT
        self.ser_conn.open()
        # Toggle DTR to reset Arduino
        self.ser_conn.setDTR(False)
        time.sleep(1)
        # toss any data already received, see
        self.ser_conn.flushInput()
        time.sleep(1)
        self.ser_conn.setDTR(True)
        time.sleep(1)

    # def open_serial_simple(self, port, baudrate):
    #     self.ser_conn.port = port
    #     self.ser_conn.baudrate = baudrate
    #     # the timeout is needed to exit from the reader thread, otherwise the serial read is blocking
    #     self.ser_conn.timeout = self.__SERIAL_TIMEOUT
    #     self.ser_conn.open()
    #     time.sleep(1)

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
            processor = os.uname()[4]
            # TODO: improve this check, it is not sufficient to state that the system is raspberry
            if processor.startswith('armv6') or processor.startswith('armv7'):
                temp_ports = glob.glob('/dev/ttyA[A-Za-z]*') # for AMA0 and ACM0 (respectively mirto and usb arduino)
            else:
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

        def __init__(self, parent, conn,timeout):
            Thread.__init__(self)
            self.parent = parent
            self.conn = conn
            self.conn.settimeout(timeout) # setting socket recv timeout
            self._stop = threading.Event()

        def stop(self):
            self._stop.set()

        # TODO: improve try catch
        def run(self):
            write_buffer = ""
            #alarm = False
            #alarm_counter = 0
            while not self._stop.is_set():
                try:
                    data = self.conn.recv(self.BUFFER_SIZE)
                except socket.timeout as e:
                    err = e.args[0]
                    if err == 'timed out': # socket time out, if the _stop value is set, program will exit
                        continue
                except (socket.error, socket.herror, socket.gaierror) as e:
                    sys.stdout.write("Exception caught in writer socket recv: {}\n".format(e))
                    self.stop()
                else:
                    # data = data.encode('utf-8')
                    try:
                        if self.DEBUG:
                            sys.stdout.write("DEBUG: Received data from TCP/IP: {}\n".format(data))
                        # ignore empty lines and empty payload
                        if data != '\r' and data != '\n' and data !=' ' and data is not None:
                            # TODO: improve string check, the one above is not sufficient
                            # (when connection is broken sometimes strange non-asip and non-char messages arrive)
                            #alarm = False
                            if "\n" in data:
                                # If there is at least one newline, we need to process
                                # the message (the buffer may contain previous characters).
                                while ("\n" in data and len(data) > 0):
                                    # But remember that there could be more than one newline in the buffer
                                    write_buffer += (data[0:data.index("\n")])
                                    if self.DEBUG:
                                        sys.stdout.write("Serial write buffer is now {}\n".format(write_buffer))
                                    if self.parent.ser_conn.isOpen():
                                            temp = write_buffer.encode() + '\n' # TODO: check \n
                                            self.parent.ser_conn.write(temp) # serial write
                                            if self.DEBUG:
                                                sys.stdout.write("DEBUG: just wrote in serial {}\n".format(temp))
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
                        # this will avoid a particular case in which the bridge does not understand that the
                        # connection is broken (no socket exceptions caught) and continue reading empty messages)
                        # FIXME: not working! Messages are caught by previous if!!
                        # else:
                        #     print("I'm in")
                        #     if alarm:
                        #         alarm_counter += 1
                        #         if alarm_counter >= 50:
                        #             self.stop()
                        #     else:
                        #         alarm = True
                        #         alarm_counter = 1

                    except (OSError, serial.SerialException) as e:
                        sys.stdout.write("Caught exception in Writer serial writing: {}\n".format(e))
                        self.stop()
            sys.stdout.write("STOPPING writer\n")


    # ListenerThread and ConsumerThread are implemented following the Producer/Consumer pattern
    # A class for a listener that rad the serial stream and put incoming messages on a queue
    # TODO: implement try catch
    class ListenerThread(Thread):

        DEBUG = False

        # overriding constructor
        def __init__(self, queue, ser_conn):
            Thread.__init__(self)
            self.queue = queue
            self.ser_conn = ser_conn
            self._stop = threading.Event()
            if self.DEBUG:
                sys.stdout.write("DEBUG: serial thread process created \n")

        def stop(self):
            self._stop.set()

        # overriding run method, thread activity
        def run(self):
            #print("Run!")
            # temp_buff = ""
            #time.sleep(2)
            # TODO: implement ser.inWaiting() >= minMsgLen to check number of char in the receive buffer?
            # serBuffer = ""
            temp = ""
            #while self.running:
            while not self._stop.is_set():
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
                try:
                    c = self.ser_conn.read() # attempt to read a character from Serial
                    c = c.decode('utf-8', errors= 'ignore')
                    if self.DEBUG:
                        sys.stdout.write("Char from serial: {}\n".format(c))
                    if c=='\n' or c=='\n':
                        if len(temp)>0:
                            temp += '\n'
                            self.queue.put(temp)
                            if self.DEBUG:
                                sys.stdout.write("Complete message from serial: {}\n".format(temp))
                        temp = ""
                    else:
                        temp += c
                except serial.SerialTimeoutException:
                    continue
                except serial.SerialException as e:
                    sys.stdout.write("Caught SerialException in serial read: {}\n".format(e))
                    sys.stdout.write("Listener Thread will now stop\n")
                    self.stop()
                except Queue as e:
                    sys.stdout.write("Caught Queue Exception: {}\n".format(e))
                    sys.stdout.write("Listener Thread will now stop\n")
                    self.stop()
                except Exception as e:
                    sys.stdout.write("Caught exception: {}\n".format(e))
                    sys.stdout.write("Listener Thread will now stop\n")
                    self.stop()

            sys.stdout.write("Stopping Listener\n")

    # A class that reads the queue and launch the processInput method of the AispClient.
    class ConsumerThread(Thread):

        DEBUG = False
        _queue_timeout = 2

        # overriding constructor
        def __init__(self, queue, conn):
            Thread.__init__(self)
            self.queue = queue
            self.conn = conn
            self._stop = threading.Event()
            if self.DEBUG:
                sys.stdout.write("DEBUG: consumer thread created \n")

        def stop(self):
            self._stop.set()

        # overriding run method, thread activity
        def run(self):
            while not self._stop.is_set():
                try:
                    temp = self.queue.get(True, self._queue_timeout)
                    self.conn.send(temp)
                    if self.DEBUG:
                        sys.stdout.write("Just sent via tcp/ip socket: {}\n".format(temp))
                    self.queue.task_done()
                except Empty as e: #queue timeout reached
                    continue
                except Exception as e:
                    sys.stdout.write("Caught exception in socket or queues: {}\n".format(e))
                    sys.stdout.write("Consumer Thread will now stop\n")
                    self.stop()
            sys.stdout.write("Stopping consumer\n")

    # ************ END PRIVATE CLASSES *************

# method for testing is called
if __name__ == "__main__":
    TCPBridge().run()