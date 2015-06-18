__author__ = 'Gianluca Barbon'

import time
import sys
import glob
import serial
import socket
from threading import Thread
import threading
from serial import Serial


class TCPBridge:

    # ************   BEGIN CONSTANTS DEFINITION ****************

    DEBUG = True  # Activates debug messages
    __TCP_IP = '127.0.0.1'  # socket.gethostname()
    __TCP_PORT = 5005
    __RECV_TIMEOUT = 2  # socket receive timeout in second
    __SERIAL_TIMEOUT = 2  # serial timeout (avoid blocking in case of issues)
    __BUFFER_SIZE = 256  # Usually 1024, 20 grants fast response, 256 is the value also set in client
    __PORT_INDEX_TO_OPEN = 0
    __BAUD_RATE = 57600

    # ************   END CONSTANTS DEFINITION ****************

    # ************   BEGIN PRIVATE FIELDS DEFINITION ****************

    # __ser_conn: self board uses serial communication
    __ports = []  # serial ports array
    # __sock_obj: tcp/ip socket communication
    __threads = []  # List of threads

    # ************   END PRIVATE FIELDS DEFINITION ****************

    def __init__(self, router_addr='192.168.0.1'):

        self.__ROUTER_ADDR = router_addr

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

        # server init
        try:
            self.__sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__sock_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.ip_retrieve(router=self.__ROUTER_ADDR)
            self.__sock_obj.bind((self.__TCP_IP, self.__TCP_PORT))
            self.__sock_obj.listen(1)  # states the max number of clients that can connect simultaneously
            sys.stdout.write("Server created with IP: {} and PORT: {}\n".format(self.__TCP_IP, self.__TCP_PORT))
        except Exception as e:
            #TODO: improve exception handling
            sys.stdout.write("Exception while creating socket: {}\n".format(e))
            sys.exit(1)

    # ************ BEGIN PUBLIC METHODS *************

    def run(self):
        while True:
            try:
                conn, address = self.__sock_obj.accept()
                sys.stdout.write("Connection accepted, connection address: {}\n".format(address))
                self.__threads.append(self.ListenerThread(conn, self.__ser_conn, self.DEBUG))
                self.__threads.append(self.WriterThread(
                    conn, self.__ser_conn, self.__RECV_TIMEOUT, self.__BUFFER_SIZE, self.DEBUG))
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
                except KeyboardInterrupt:  # KeyboardInterrupt handling in order to close every thread correctly
                    sys.stdout.write("KeyboardInterrupt while checking mapping. Attempting to close listener thread.\n")
                    self.thread_killer()
                    sys.exit()
                else:
                    self.thread_killer()
                    sys.stdout.write("Waiting for new connection.\n")

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
        return True

    # retrieve the ip address, parameter is the router address
    # TODO: add exception handling
    def ip_retrieve(self, router='192.168.0.1'):
        self.__TCP_IP = [(s.connect((router, 80)), s.getsockname()[0], s.close())
                         for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

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

    # TODO: implement connection closure
    # def close_tcp_conn(self, conn):
    #     conn.shutdown(socket.SHUT_RDWR)
    #     conn.close()
    #     sys.stdout.write("Connection closed.\n")

    # This methods retrieves the operating system and set the Arduino serial port
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    # TODO: test needed for linux and windows implementation
    # TODO: improve try except
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

        def __init__(self, sock_conn, ser_conn, timeout, buffer_size=256, debug=False):
            Thread.__init__(self)
            self.sock_conn = sock_conn
            self.sock_conn.settimeout(timeout)  # setting socket recv timeout
            self.ser_conn = ser_conn
            self.BUFFER_SIZE = buffer_size
            self.DEBUG = debug
            self._stopper = threading.Event()

        def stopper(self):
            sys.stdout.write("Writer Thread: now stopping.\n")
            self._stopper.set()

        # TODO: improve try catch
        def run(self):
            write_buffer = ""
            alarm_counter = 0
            while not self._stopper.is_set():
                # alarm_counter is a temporary basic solution to avoid tcp empty messages flooding
                # when connection is broken (no socket exceptions caught) and continue reading empty messages.
                # These are not true empty messages, but they contains no characters and no EOF or EOL.
                # This happens when client connection is closed (maybe not correctly?).
                # TODO: improve this!!
                if alarm_counter > 20:
                    sys.stdout.write("Something strange happened, alarm counter > 20\n")
                    self.stopper()
                try:
                    data = self.sock_conn.recv(self.BUFFER_SIZE)
                except socket.timeout as e:
                    err = e.args[0]
                    if err == 'timed out':  # socket time out, if the _stop value is set, program will exit
                        continue
                except (socket.error, socket.herror, socket.gaierror) as e:
                    sys.stdout.write("Exception caught in writer socket recv: {}\n".format(e))
                    self.stopper()
                else:
                    data = data.decode('utf-8')
                    try:
                        if self.DEBUG:
                            sys.stdout.write("DEBUG: Received data from TCP/IP: {}\n".format(data))
                        # ignore empty lines and empty payload
                        if data != '\r' and data != '\n' and data != ' ' and data is not None:
                            # TODO: improve string check, the one above is not sufficient
                            # (when connection is broken sometimes strange non-asip and non-char messages arrive)
                            if "\n" in data:
                                alarm_counter = 0
                                # If there is at least one newline, we need to process
                                # the message (the buffer may contain previous characters).
                                while "\n" in data and len(data) > 0:
                                    # But remember that there could be more than one newline in the buffer
                                    write_buffer += (data[0:data.index("\n")])
                                    if self.DEBUG:
                                        sys.stdout.write("Serial write buffer is now {}\n".format(write_buffer))
                                    if self.ser_conn.isOpen():
                                            temp = write_buffer + '\n'  # TODO: check \n
                                            self.ser_conn.write(temp.encode()) # serial write
                                            if self.DEBUG:
                                                sys.stdout.write("DEBUG: just wrote in serial {}\n".format(temp))
                                    else:
                                        raise serial.SerialException
                                    write_buffer = ""
                                    if data[data.index("\n")+1:] == '\n':
                                        data = ''
                                        break
                                    else:
                                        data = data[data.index("\n")+1:]
                                if len(data) > 0 and data not in ('\r', '\n', ' '):
                                    write_buffer = data
                            else:
                                alarm_counter += 1
                                write_buffer += data

                    except (OSError, serial.SerialException) as e:
                        sys.stdout.write("Caught exception in Writer serial writing: {}\n".format(e))
                        self.stopper()
            sys.stdout.write("Writer Thread: stopped\n")

    # ListenerThread read the serial stream and send the message to the tcp/ip stream
    class ListenerThread(Thread):

        # overriding constructor
        def __init__(self, sock_conn, ser_conn, debug=False):
            Thread.__init__(self)
            self.sock_conn = sock_conn
            self.ser_conn = ser_conn
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
                        if self.DEBUG:
                            sys.stdout.write("DEBUG: Char from serial: {}\n".format(c))
                        if c == '\n' or c == '\n':
                            if len(ser_buffer) > 0:
                                ser_buffer += '\n'
                                self.sock_conn.send(ser_buffer.encode())
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
    router_ip = '192.168.0.1'
    TCPBridge(router_ip).run()