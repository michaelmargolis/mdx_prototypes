#!/usr/bin/python

from Tkinter import *
import select
import socket
import asip

BUFFER_SIZE = 255

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  

class TcpUI(LabelFrame):
    def __init__(self, parent, name):    
      
        LabelFrame.__init__(self, parent,text=name, padx=5, pady=5)
        self.pack(fill=BOTH, expand=1)
        ipLbl = Label(self, text='IP address').pack(side = LEFT)
        
        self.TCP_Adr = Entry(self, width=14) 
        self.TCP_Adr.pack(side = LEFT,padx=4) 
        self.TCP_Adr.insert(0, "192.168.1.13")        

        portLbl = Label(self, text='Port').pack(side = LEFT)
        self.TCP_Port = Entry(self, width=6) 
        self.TCP_Port.pack(side = LEFT,padx=4) 
        self.TCP_Port.insert(0, "5507")  
        
        self.btnOpen = Button(self, text="Connect", command=self.onOpen)
        self.btnOpen.pack(side=RIGHT,padx=(4,4))
        self.status = Label(self, text='Not Connected',fg='red')
        self.status.pack(side = RIGHT,padx=(4,4))
        
    def onOpen(self):
       global isReady
       if isReady == False:
           try: 
               adr = self.TCP_Adr.get()
               port = 5507 #int(self.TCP_Port.get())
               sock.connect((adr, port))
               print(adr)
               self.btnOpen.configure(text = 'Close')
               self.status.configure(text = 'Connected',fg='DarkGreen')    
               isReady = True
           except socket.error, e:
               print 'Could not connect to server @%s' % adr 
       else:   
           sock.close();
           self.status.configure(text = 'Not connected',fg='red')           
           self.btnOpen.configure(text = 'Connect')
           isReady = False
      
    
class Motor(LabelFrame):
  
    def __init__(self, parent, name, fields):
        LabelFrame.__init__(self, parent,text=name, padx=5, pady=5)        
        self.pack(fill=BOTH, expand=1)
        for index, f in enumerate(fields): 
           self.initFields(index, f)
           
        self.stopMotors() 
        b = Button(self, text="Stop", command=self.stopMotors)
        b.pack(side=RIGHT,padx=(20,4))


    def initFields(self, index, label):
        l = Label(self, text=label)
        l.pack(side = LEFT,padx=4)
        if index == 0:
            self.m0 = Scale(self, from_=-100, to=100,tickinterval=50, length=180,orient=HORIZONTAL,
            command=self.onChangeM0)
            self.m0.pack(side = LEFT)                   
        elif index == 1:
            self.m1 = Scale(self, from_=-100, to=100,tickinterval=50, length=180,orient=HORIZONTAL,
            command=self.onChangeM1)
            self.m1.pack(side = LEFT)
           
        else:
            print 'invalid motor'
        
    def onChangeM0(self, value):
        self.onChangeMotor('0', value)
   
    def onChangeM1(self, value):
        self.onChangeMotor('1', value)
            
    def onChangeMotor(self, motor, value):
        global isReady
        if isReady == True:
            print 'Motor ' + motor + ' value= ' + value
            sock.send('M,m,' + motor + ',' + value + '\n')               
        else:
            print ' not ready'
        
    def stopMotors(self):
        self.m0.set(0)
        self.m1.set(0)
 
class Encoder(LabelFrame):
  
    def __init__(self, parent, name, svcId, fields):  
        LabelFrame.__init__(self,parent,text=name, padx=5, pady=5)        
        self.svcId = svcId
        self.fieldVars = []        
        self.pack(fill=BOTH, expand=1)        
        fr1 = Frame(self, padx=5, pady=5)
        l = Label(fr1, text='Pulse Width').pack(side = TOP)
        l = Label(fr1, text='      Count').pack(side = TOP)
        fr1.pack(side = LEFT) 
        
        for f in fields:
            self.initFields(f)
        
        self.entReq = Entry(self, width=5) 
        self.entReq.pack(side = RIGHT,padx=4) 
        self.entReq.insert(0, "0")        
        b = Button(self, text="Request", command=self.request)
        b.pack(side=RIGHT,padx=(20,4))

    def initFields(self, label):
        fr = Frame(self, padx=5, pady=5)
        self.fieldVars.append([StringVar(),StringVar()])
        pw = Entry(fr,width=8,textvariable=self.fieldVars[-1][0])
        pw.pack(side = TOP,padx=(1,16)) 
        cnt = Entry(fr,width=12,textvariable=self.fieldVars[-1][1])
        cnt.pack(side = TOP,padx=(1,20)) 
        fr.pack(side = LEFT)  
        
    def request(self):
        t = self.entReq.get()
        sendRequest(self.svcId,t) 
    
class Service(LabelFrame):
  
    def __init__(self, parent, name, svcId, fields):
        LabelFrame.__init__(self, parent,text=name, padx=5, pady=5)  
        self.svcId = svcId
        self.fieldVars = []
        
        self.pack(fill=BOTH, expand=1)
        for f in fields:
           self.initFields(f);
         
        self.entReq = Entry(self, width=5) 
        self.entReq.pack(side = RIGHT,padx=4) 
        self.entReq.insert(0, "0")        
        b = Button(self, text="Request", command=self.request)
        b.pack(side=RIGHT,padx=(20,4))

    def initFields(self, label):
        l = Label(self, text=label).pack(side = LEFT)
        self.fieldVars.append(StringVar())
        e = Entry(self, width=8, textvariable=self.fieldVars[-1]) 
        e.pack(side = LEFT, padx=(2,16))   

    def request(self):
        t = self.entReq.get()
        sendRequest(self.svcId,t) 

class Log(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        s = Scrollbar(self, orient=VERTICAL)
        self.log = Listbox(self, height=6,yscrollcommand=s.set)
        self.log.pack(side=LEFT,fill = X, expand =1)
        s.config(command=self.log.yview)
        s.pack(side=RIGHT, fill=Y)
        self.pack(fill=BOTH, expand=1)
    def insert(self, msg):
        self.log.insert(0,msg)
        
def sendRequest(svcId, value):
    global isReady
    if isReady == True:
        print 'request for svc ' + svcId + ':' + value       
        sock.send(svcId + ',' + asip.tag_AUTOEVENT_REQUEST + ','+ value + '\n')           
    else:
        print 'Not Connected'
   
def logMsg(msg):
    #print("log:" + msg)
    log.insert(msg)
    
def msgDispatcher(msg):
    logMsg(msg)
    if msg[0] == asip.EVENT_HEADER:
        if msg[1] == asip.SYSTEM_MSG_HEADER:
            if msg[3] == asip.tag_SYSTEM_GET_INFO:
                showInfo(msg[5:-1]) 
        else:
            evtDispatcher(msg[1], msg[8:-1])
    elif msg[0] == asip.DEBUG_MSG_HEADER:
        logMsg(msg[1:])
    elif msg[0] == asip.ERROR_MSG_HEADER:
        logMsg('Err: ' + msg[1:])    
      
def showInfo(msg):
    info = msg.split(',')
    msg = 'ASIP version %s.%s running on %s using sketch: %s' % (info[0], info[1],info[2], info[4])
    logMsg(msg)

def evtDispatcher(id, values):
    #print("evt dispatch:" +  values)
    if  values.find("{") == 0 and  values.find("}") == len(values-1):
        values = values[1:]
    if  values.find("}") == len(values[:-1]):   
        values = values[:-1]       
    fields = values.split(',')
    try:
        for index, f in enumerate(fields): 
           if id == asip.id_ENCODER_SERVICE:
               subField = f.split(':')
               encoders.fieldVars[index][0].set(subField[0])
               encoders.fieldVars[index][1].set(subField[1])
               #print 'encoder'
           elif id == asip.id_BUMP_SERVICE:            
               bump.fieldVars[index].set(f)
               #print 'bump'
           elif id == asip.id_IR_REFLECTANCE_SERVICE:
               reflectance.fieldVars[index].set(f)
               #print 'reflectance'                  
    except IndexError:
        print("parse error: " , fields)
        
def poll():
    if isReady :       
        try:
            ready = select.select([sock], [], [], 0.01)
            if ready[0]:                     
                packet = sock.recv(255)               
                if len(packet) > 0 and packet[0] != '!': #ignore debug messages from arduino
                    #print("in poll:" + packet)
                    msgs = packet.split('\n')  # may be more than one msg per packet
                    for m in msgs: 
                        if len(m) > 0:
                            #print("  poll msg-> ", m)
                            msgDispatcher(m)       
        except socket.error, (value,message): 
            print "Socket err: ", message   
    root.after(10, poll)    
            
def main():
    root.title("ASIP Mirto Net Tester")
    root.after(10, poll) # socket receive polling routine    
    root.mainloop()  
    if isReady == True:
        sock.close()

global root
root = Tk()
global isReady
isReady = False
socketUI = TcpUI(root, 'ASIP Connection')

motors = Motor(root,'Motor Control', ('Left', 'Right'))
encoders = Encoder(root,'Encoders',asip.id_ENCODER_SERVICE, ('Left', 'Right'))
bump = Service(root,'Bump Sensors',asip.id_BUMP_SERVICE, ('Left', 'Right'))
reflectance = Service(root,'Reflectance Sensors',asip.id_IR_REFLECTANCE_SERVICE,('Left', 'Center','Right'))
#Distance = Service(root,'Distance Sensor',('distance',))

log = Log(root)

  
if __name__ == '__main__':
    main() 