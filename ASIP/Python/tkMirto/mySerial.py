#mySerial.py

#from serial import *
import serial
from time import sleep
import sys
import glob

global ser
ser = serial.Serial()

#make our own buffer
serBuffer = ""

tkRoot = ''

def init(root, callback, log):
    global tkRoot
    tkRoot = root;
    global _log
    _log = log
    global uiCallback
    uiCallback = callback
    ser.timeout = 0       #ensure non-blocking
    ser.writeTimeout = 0  #ensure non-blocking
   
def open(port, baud):
    if ser.isOpen():
        ser.close()
    ser.port = port
    ser.baudrate = baud   
    ser.open()        
    # Toggle DTR to reset Arduino
    ser.setDTR(False)
    sleep(1)
    # toss any data already received, see
    ser.flushInput()
    ser.setDTR(True)
        
def close():    
    ser.close()

def isOpen():
    return ser.isOpen()
        
def send(msg):
    if ser.isOpen():
        try:
            ser.write(msg)
            return True
        except (OSError, serial.SerialException):
            pass
    return False
    #    _log.insert('Err: Unable to send (' + msg  + '), port not open');
    
def poll():
    if ser.isOpen() == False:
        tkRoot.after(50, poll)
    else:            
        global serBuffer
        try:
            while True:
                c = ser.read() # attempt to read a character from Serial                
                #was anything read?
                if len(c) == 0:
                    tkRoot.after(10, poll)
                    break
                
                # check if character is a delimiter
                if c == '\r':
                    c = '' # ignore CR                    
                elif c == '\n':
                    serBuffer += "\n" # add the newline to the buffer
                    #print serBuffer
                    uiCallback(serBuffer)
                    serBuffer = '' # empty the buffer
                else:
                    serBuffer += c # add to the buffer
        except (OSError, serial.SerialException):
            serBuffer = 'ERROR'
            
  
def list():
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]

    elif sys.platform.startswith('linux'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            ser.port = port
            s = ser.open()
            ser.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
