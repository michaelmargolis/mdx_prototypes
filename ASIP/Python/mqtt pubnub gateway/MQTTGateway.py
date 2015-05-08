from collections import deque
from Pubnub import Pubnub
import threading
from threading import Lock
import sys
import time
import os
from kbhit import KBHit
import paho.mqtt.client as mqtt

from mqttConfig import config

class Format():
    # functions to format time fields
    # todo allow selection of float times? 
    # todo allow passthrough of vicarious time?
    def local_time(self): return str(int( time.mktime(time.localtime())))
    def utc_time(self): return str(int(time.time()))

    #function to scale a value, range is a list containing: (from_min, from_max, to_min, to_max)   
    def scale(self, value, range):
      if value > range[1]:  # limit max
          return range[3]
      if value < range[0]:  # limit min
          return range[2]       
      if range[1] == range[0]:
          return range[2] #avoid div by zero error
      else:      
          return ( (value - range[0]) / (range[1] - range[0]) ) * (range[3] - range[2]) + range[2]
    
class MQTT():

    def __init__(self):
        self.client = mqtt.Client(client_id="", clean_session=True, userdata=None, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("$SYS/#")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload) +"todo - not yet handled")
             

    def connect(self, broker, port=1883):
        print "connecting to mqtt broker " + broker + " on port  " +str(port)
        self.client.connect(broker, port, 180)   
         
    def sendData(self, topic, msg):
        self.client.publish(topic, msg)
         
    def disconnect(self):
        print("Disconnected from mqtt")
        self.client.disconnect()       
                        
    
class MQTTGateway():

    def run(self, channel, latency, bufferSize):
        self.mutex = Lock()
        self.outqueuebuffers = {}
        self.outbuffers = {}
        self.senders = {}
        self.channels = None
        self.channel = channel
        self.buffer_size = bufferSize
        self.timestamp_buffer = [None] * self.buffer_size
        self.debug = False

        self.index = 0
        self.offset = None
        self.latency = latency
        self.setupDone = False
        self.channel_count = 0

        pubnub = Pubnub("pub-c-e655613e-f776-4301-9f29-f71edbcd6559",
                        "sub-c-2eafcf66-c636-11e3-8dcd-02ee2ddab7fe",
                        "sec-c-ZjUwZDgzMTItYzE2Mi00ZGYyLTg2NGMtNmE5N2Q3MGI0MTli",
                        False)

        self.m = MQTT()
        broker = config.mqtt['Broker'] 
        print("Connecting to broker: " + broker)
        self.m.connect(broker)
        
        while(True):
            pubnub.subscribe({
                'channel': self.channel,
                'callback': self.setData
                })              

    def setData(self, message):
        if self.offset is None:
            self.offset = (time.time() - message["data"][0][0]) + self.latency
            self.channel_count = len(message["channelnames"])
            self.channels = message["channelnames"]
            self.channeltypes = message["channeltypes"]
            for i in range(self.channel_count):
                self.outbuffers[i] = [None] * self.buffer_size
                self.outqueuebuffers[i] = deque([], self.buffer_size)
            if self.debug:
                print "Got Data:", len(self.outbuffers)            
        self.mutex.acquire()

        for i in range(len(message["data"])):
            handleit = False

            if self.index > 0:
                if message["data"][i][0] > self.timestamp_buffer[self.index-1]:
                    handleit = True
            else:
                handleit = True

            if handleit:                       
                self.timestamp_buffer[self.index] = message["data"][i][0]
                vals = message["data"][i][1]

                for j in range(len(vals)):
                    self.outbuffers[j][self.index] = vals[j]

                self.index += 1
                if self.index >= self.buffer_size:
                    self.index = 0

        self.mutex.release()

        if not self.setupDone:
            self.delThread = MQTTDeliveryThread(self)
            self.delThread.start()
            self.setupDone = True

        return True

class MQTTDeliveryThread(threading.Thread):
    dataToAverage  = []
    prevTime = 0;
    format = Format()
    
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent 

    def  sendMessage(self, data):  
       
        if len(self.dataToAverage) < config.smoothData :   
            self.dataToAverage.append(data) 
            if len(self.dataToAverage) == config.smoothData :  
                msgString = ""                         
                zipped  = zip(*self.dataToAverage)
                avg = []  # list of averages for each field
                for i,a in enumerate(zipped):                    
                    #avg.append( sum(zipped[i]) / len(zipped[i]) )          
                    avg.append( sum(a) / len(a) )    
                #print "average=", avg
                self.dataToAverage = []  
                msgString = config.MsgPrefix         
                if time.gmtime() != self.prevTime :  
                    #print (self.prevTime)              
                    self.prevTime =  time.gmtime()  #check to see if time has changed
                    if config.timeStamp == 'LocalTime':
                        msgString += self.format.local_time()
                    elif config.timeStamp == 'UTCTime':  
                        msgString += self.format.utc_time()
                else:
                    msgString += '-1' # -1 indicates time is unchanged from previous message 
                  
                for i,a in enumerate(avg):
                    msgString += ","
                    msgString +=str(a)
                    
                topic = config.mqtt['Topic']
                print msgString
                #here's where we publish to MQTT  
                self.parent.m.sendData(topic, msgString)
             
        
    def run(self):
        kb = KBHit()      
        selectedData = []
        dataToAverage = []        
        print('Hit ESC to exit')
        while True:
            if kb.kbhit():
                c = kb.getch()                
                if ord(c) == 27: # ESC
                    kb.set_normal_term() 
                    print "Quitting!"
                    os._exit(0)   
            now = time.time()
            due = now - self.parent.offset
            search_from = self.parent.index - 1
            if search_from == - 1:
                search_from = self.parent.buffer_size - 1
            timestamp = 0
            nextTimestamp = 0
            self.waitForNewData = 0.5
            self.parent.mutex.acquire()

            lastjvalue = 0

            dataArray = []

            for theid in range(self.parent.channel_count):

                data = self.parent.outbuffers[int(theid)][self.parent.index]
                
                for i in range(search_from, search_from - self.parent.buffer_size, -1):
                    j = i if i >= 0 else i + self.parent.buffer_size
                    timestamp = self.parent.timestamp_buffer[j]
                    if timestamp is not None and timestamp <= due:
                        data = self.parent.outbuffers[int(theid)][j]
                        lastjvalue = j
                        if(j<self.parent.buffer_size-2):
                            nextTimestamp = self.parent.timestamp_buffer[j+1]
                        else:
                            nextTimestamp = self.parent.timestamp_buffer[0]
                        break
                if data is not None:                                
                    dataArray.append(data)
            
            #print "data array: ", dataArray     
                         
                
            for f in config.streams:
                stream = f['stream'] 
                if len(dataArray) > stream:  
                    #print "stream = ", stream,  dataArray[stream]                             
                    if 'scale' in f:
                        dataArray[stream] = self.format.scale(dataArray[stream], f['scale'])                  
                    if 'type' in f and f['type'] == int: 
                        #msgString += str(int(dataArray[stream]))
                        selectedData.append(int(dataArray[stream]))                      
                    else:   
                         #msgString += str(dataArray[stream]) 
                         selectedData.append(dataArray[stream]) 
 
                    if len(selectedData) == len(config.streams) :  
                        self.sendMessage(selectedData)                                                                 
                        selectedData = []          

            if timestamp is not None and nextTimestamp is not None:
                waitTime = nextTimestamp - timestamp
                if waitTime > 0:
                    time.sleep(waitTime)
                else:
                    print "timing out waiting for new data - time < 0"
                    time.sleep(self.waitForNewData)
            else:
                print "timing out waiting for new data - time or nextTime is None"
                time.sleep(self.waitForNewData)
            self.parent.mutex.release()


def main(channel,latency,bufferSize):
    c = MQTTGateway()
    c.run(channel,latency,bufferSize)

# argumets:
# channel: the pubnub channel from which you wish to receive (eg. hastingsfiltered)
# latency: any latency you wish to introduce to account for data delays (in seconds) (1.0 suggested)
# buffersize: how many values you wish to buffer (500 suggested - may use less for smaller/slower systems)
#python MQTTGateway.py hastingsfiltered 1.0 500

if __name__ == '__main__':
    main(sys.argv[1],float(sys.argv[2]),int(sys.argv[3]))
