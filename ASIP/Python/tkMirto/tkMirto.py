#!/usr/bin/python

from Tkinter import *
import mySerial
import asip

class SerialUI(LabelFrame):
    def __init__(self, parent, name):
        LabelFrame.__init__(self, parent,text=name, padx=5, pady=5)
        self.pack(fill=BOTH, expand=1)
        l = Label(self, text='Com Port').pack(side = LEFT)

        ports = mySerial.list()        
        self.comport = StringVar(self)
        self.comport.set(ports[0]) #default to first port
        o = OptionMenu(self, self.comport, *ports )
        o["menu"].config(bg="white",)
        arrow = PhotoImage(file="Arrow.gif")
        o.image = arrow
        o.configure(indicatoron=0, compound='right', image=arrow)
        o.pack(side=LEFT) 
     
        self.btnOpen = Button(self, text="Open", command=self.onOpen)
        self.btnOpen.pack(side=LEFT,padx=(20,4))
        self.status = Label(self, text='Not Connected',fg='red')
        self.status.pack(side = LEFT,padx=(20,4))
        
    def onOpen(self):
        if mySerial.isOpen():
            self.closeSerial()            
        else:
            self.openSerial()

    def openSerial(self):     
        baudRate = 57600
        myport = self.comport.get()
        mySerial.open(myport,baudRate)
        if mySerial.isOpen():
            self.btnOpen.configure(text = 'Close')
            if mySerial.send(asip.INFO_REQUEST):
                self.status.configure(text = 'Connected',fg='DarkGreen')
                global isReady
                isReady = True
        else:
            logMsg('Failed to open serial port')    
                
    def closeSerial(self):
        mySerial.close() 
        self.btnOpen.configure(text = 'Open')      
        self.status.configure(text = 'Not Connected',fg='red')
        global isReady
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
            if mySerial.send('M,m,' + motor + ',' + value + '\n') == False:
                commsUI.closePort() # send failed so close port  
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
        if mySerial.send(svcId + ',' + asip.tag_AUTOEVENT_REQUEST + ','+ value + '\n') == False:
            commsUI.closePort() # send failed so close port  
    else:
        print 'Not Connected'
   
def logMsg(msg):
    print msg
    log.insert(msg)
    
def msgDispatcher(msg):
    #logMsg(msg)
    if msg[0] == asip.EVENT_HEADER:
        if msg[1] == asip.SYSTEM_MSG_HEADER:
            showInfo(msg[5:-1]) 
        else:
            evtDispatcher(msg[1], msg[8:-2])
    elif msg[0] == asip.DEBUG_MSG_HEADER:
        logMsg(msg[1:])
    elif msg[0] == asip.ERROR_MSG_HEADER:
        logMsg('Err: ' + msg[1:])    
      
def showInfo(msg):
    info = msg.split(',')
    msg = 'ASIP version %s.%s running on %s using sketch: %s' % (info[0], info[1],info[2], info[4])
    logMsg(msg)

def evtDispatcher(id, values):
    #print values
    fields = values.split(',')
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
   
def main():
    root.title("ASIP Mirto Tester")        
    mySerial.init(root,msgDispatcher,log)
    root.after(100, mySerial.poll) # serial polling routine
    root.mainloop()  

global root
root = Tk()
global isReady
isReady = False
commsUI = SerialUI(root, 'Serial Port')

motors = Motor(root,'Motor Control', ('Left', 'Right'))
encoders = Encoder(root,'Encoders',asip.id_ENCODER_SERVICE, ('Left', 'Right'))
bump = Service(root,'Bump Sensors',asip.id_BUMP_SERVICE, ('Left', 'Right'))
reflectance = Service(root,'Reflectance Sensors',asip.id_IR_REFLECTANCE_SERVICE,('Left', 'Center','Right'))
#Distance = Service(root,'Distance Sensor',('distance',))

log = Log(root)
  
if __name__ == '__main__':
    main() 