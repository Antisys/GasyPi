#!/usr/bin/python

import os.path
import time
import datetime
import threading
import serial
import sys
import os
import fcntl
import MySQLdb


pid_file = 'gasypi.pid'
fp = open(pid_file, 'w')
try:
  fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
  print "Error: Instance of GasyPi is already running."
  sys.exit(0)

os.system('gpio mode 1 out') #Board 12 / RLA Pump
os.system('gpio mode 2 out') #Board 13 / Heat-Exchanger Pump
os.system('gpio mode 0 out') #Board 11 / Heizkreis Pump 
os.system('gpio mode 3 out') #Board 15 / Heizkreis
os.system('gpio mode 4 out') #Board 16 / Heizkreis
os.system('gpio mode 5 out') #Board 18 / RLA
os.system('gpio mode 6 out') #Board 22 / RLA

os.system('gpio write 0 1')
os.system('gpio write 2 0') #Pump Heat Exchanger
os.system('gpio write 1 1')

# ===========================================================================
# Class OneWire
# ===========================================================================
from threading import Thread

class OneWire:
  def __init__(self, file):
    self.file = file
    self.temperature = -999
    self.alive = False
    t = Thread(target = self.readTemp)
    t.setDaemon(True)
    t.start()
    heartBeatThreat = Thread(target = self.heartBeat) #The W1 driver may get stuck.
    heartBeatThreat.setDaemon(True)                   #In that case also opening the W1 temperature file
    heartBeatThreat.start()                           #will get stuck. To make that visible the heartBeat
                                                      #task is necessary
  def heartBeat(self):
    self.active = 1
    while self.active:
      time.sleep(10)
      if(self.alive == False):
        self.temperature = -999
      self.alive = False      

  def readTemp(self):
    self.active = 1
    while self.active:
      text = ""
      try:
        myfile = open(self.file)
        text = myfile.read()
        myfile.close()
      except:
        text = "NO"
        self.temperature = -999
      if text.find("NO") == -1:
        temp_data = text.split()[-1]
        temp = float(temp_data[2:])
        self.temperature = temp / 1000
      self.alive = True

  def getTemp(self):
    return(self.temperature)

# ===========================================================================
# End of Class OneWire
# ===========================================================================

# ===========================================================================
# Class PID
# ===========================================================================

#The recipe gives simple implementation of a Discrete Proportional-Integral-Derivative (PID) controller. PID controller gives output value for error between desired reference input and measurement feedback to minimize error value.
#More information: http://en.wikipedia.org/wiki/PID_controller
#
#cnr437@gmail.com
#
#######    Example    #########
#
#p=PID(3.0,0.4,1.2)
#p.setPoint(5.0)
#while True:
#     pid = p.update(measurement_value)
#
#


class PID:
    """
    Discrete PID control
    """

    def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0, Integrator_max=10, Integrator_min=-10):

        self.Kp=P
        self.Ki=I
        self.Kd=D
        self.Derivator=Derivator
        self.Integrator=Integrator
        self.Integrator_max=Integrator_max
        self.Integrator_min=Integrator_min

        self.set_point=0.0
        self.error=0.0

    def update(self,current_value):
        """
        Calculate PID output value for given reference input and feedback
        """

        self.error = self.set_point - current_value

        self.P_value = self.Kp * self.error
        self.D_value = self.Kd * ( self.error - self.Derivator)
        self.Derivator = self.error

        self.Integrator = self.Integrator + self.error

        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min

        self.I_value = self.Integrator * self.Ki

        PID = self.P_value + self.I_value + self.D_value
        return PID

    def setPoint(self,set_point):
        """
        Initilize the setpoint of PID
        """
        self.set_point = set_point
        self.Integrator=0
        self.Derivator=0

    def setIntegrator(self, Integrator):
        self.Integrator = Integrator

    def setDerivator(self, Derivator):
        self.Derivator = Derivator

    def setKp(self,P):
        self.Kp=P

    def getKp(self):
        return(self.Kp)

    def setKi(self,I):
        self.Ki=I

    def getKi(self):
        return(self.Ki)

    def setKd(self,D):
        self.Kd=D

    def getKd(self):
        return(self.Kd)

    def getPoint(self):
        return self.set_point

    def getError(self):
        return self.error

    def getIntegrator(self):
        return self.Integrator

    def getDerivator(self):
        return self.Derivator

# ===========================================================================
# End of Class PID
# ===========================================================================

# ===========================================================================
# Class MixerControl
# ===========================================================================

class MixerControl:
  def __init__(self, mytc, Target, P, I, D, timer, GPIO_warm, GPIO_cold):
    self.myTempClass = mytc
    self.TargetTemp = Target
    self.p=PID(P, I, D, Integrator_max = 10, Integrator_min = -10)
    self.timer = timer
    self.pin_warm = GPIO_warm
    self.pin_cold = GPIO_cold
    self.p.setPoint(Target)
    self.mixerControl()

  def mixerCold(self, secs):
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_warm)))
    os.system('gpio write {gpio} 1'.format(gpio=str(self.pin_cold)))
    self.timerThread = threading.Timer(secs, self.mixerOff)
    self.timerThread.setDaemon(True)
    self.timerThread.start()

  def mixerWarm(self, secs):
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_cold)))
    os.system('gpio write {gpio} 1'.format(gpio=str(self.pin_warm)))
    self.timerThread = threading.Timer(secs, self.mixerOff)
    self.timerThread.setDaemon(True)
    self.timerThread.start()

  def mixerOff(self):
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_cold)))
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_warm)))

  def setTemp(self, value):
    self.p.setPoint(value)   
    self.TargetTemp = value
 
  def mixerControl(self):
    actTemp = self.myTempClass.getTemp()
    pid = self.p.update(actTemp)
    if pid > 0:
      if pid > 30:
        pid = 30
      self.mixerWarm(pid)
    else:
      if pid < -30:
        pid = -30
      self.mixerCold(pid * -1)
    self.thr = threading.Timer(self.timer, self.mixerControl)
    self.thr.setDaemon(True)
    self.thr.start()

# ===========================================================================
# End of Class MixerControl
# ===========================================================================

# ===========================================================================
# Class MixerControl
# ===========================================================================

class Pt1000MixerControl:
  def __init__(self, ft, Target, P, I, D, timer, GPIO_warm, GPIO_cold):
    self.myTempClass = ft
    self.TargetTemp = Target
    self.p=PID(P, I, D, Integrator_max = 20, Integrator_min = -20)
    self.timer = timer
    self.pin_warm = GPIO_warm
    self.pin_cold = GPIO_cold
    self.p.setPoint(Target)
    self.mixerControl()

  def mixerCold(self, secs):
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_warm)))
    os.system('gpio write {gpio} 1'.format(gpio=str(self.pin_cold)))
    self.timerThread = threading.Timer(secs, self.mixerOff)
    self.timerThread.setDaemon(True)
    self.timerThread.start()

  def mixerWarm(self, secs):
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_cold)))
    os.system('gpio write {gpio} 1'.format(gpio=str(self.pin_warm)))
    self.timerThread = threading.Timer(secs, self.mixerOff)
    self.timerThread.setDaemon(True)
    self.timerThread.start()

  def mixerOff(self):
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_cold)))
    os.system('gpio write {gpio} 0'.format(gpio=str(self.pin_warm)))

  def setTemp(self, value):
    self.p.setPoint(value)   
    self.TargetTemp = value
 
  def mixerControl(self):
    actTemp = self.myTempClass.getBoilerT()
    pid = self.p.update(actTemp)
    print self.p.P_value, self.p.I_value, self.p.D_value
    if pid > 0:
      if pid > 30:
        pid = 30
      self.mixerWarm(pid)
    else:
      if pid < -30:
        pid = -30
      self.mixerCold(pid * -1)
    self.thr = threading.Timer(self.timer, self.mixerControl)
    self.thr.setDaemon(True)
    self.thr.start()

# ===========================================================================
# End of Class MixerControl
# ===========================================================================

# ===========================================================================
# Class FlammtronikData
# ===========================================================================
import datetime
import os
import zmq
from rrdtool import update as rrd_update

class FTData:
  def __init__(self, outside, mixforward, bentryt, bexitt, tank1top, tank1middle, tank1bottom, tank2top, tank2middle, tank2bottom, tank3top, tank3middle, tank3bottom, tank4top, tank4middle, tank4bottom):
    self.outside = outside
    self.mixforward = mixforward
    self.bentry = bentryt
    self.bexit = bexitt
    self.tank1 = tank1top
    self.tank2 = tank1middle
    self.tank3 = tank1bottom
    self.tank4 = tank2top
    self.tank5 = tank2middle
    self.tank6 = tank2bottom
    self.tank7 = tank3top
    self.tank8 = tank3middle
    self.tank9 = tank3bottom
    self.tank10 = tank4top
    self.tank11 = tank4middle
    self.tank12 = tank4bottom

    try:
      self.ser = serial.Serial("/dev/ttyUSB0", 38400, timeout=7)
      t = Thread(target = self.getFTData)
      t.setDaemon(True)
      t.start()
    except:
      print "No Serial Port."
 
  def getFTData(self):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://*:5557")

    while True:
      flammString = self.ser.readline()
      print flammString
      if len(flammString) == 0:
        self.ser.close()
        self.ser = serial.Serial("/dev/ttyUSB0", 38400, timeout=7)
        continue
      flammString = flammString.translate(None, '\x11\r\n')
      self.values = flammString.split(' ')
      #res = rrd_update('/media/USB/gasypi.rrd', 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(self.getExhaustT(), self.getChamberT(), self.getPrimSpeed(), self.getSecSpeed(), self.getO2(), self.bentry.getTemp(), self.bexit.getTemp(), self.tank1.getTemp(), self.tank2.getTemp(), self.tank3.getTemp(), self.tank4.getTemp(), self.tank5.getTemp(), self.tank6.getTemp(), self.tank7.getTemp(), self.tank8.getTemp(), self.tank9.getTemp(), self.tank10.getTemp(), self.tank11.getTemp(), self.tank12.getTemp(), self.outside.getTemp(), self.mixforward.getTemp(), self.getHeatExchangerT()));
      socket.send("FT_Time: %s" % (self.getTime()))
      socket.send("FT_Oven: %s" % (self.getBoilerT()))
      socket.send("FT_Flue_Gas: %s" % (self.getExhaustT()))
      socket.send("FT_Chamber: %s" % (self.getChamberT()))
      socket.send("FT_Prim_Blower: %s" % (self.getPrimSpeed()))
      socket.send("FT_Oxygen: %s" % (self.getO2()))
      socket.send("FT_Sec_Blower: %s" % (self.getSecSpeed()))
      socket.send("FT_Hot_Water: %s" % (self.getHeatExchangerT()))

  def getTime(self):
    try:
      time = self.values[0].translate(None, 'T')
      return float(time)
    except:
      return(-1)

  def getBoilerT(self):
    try:
      return(float(self.values[1].translate(None, 'K')))
    except:
      return(-1)

  def getExhaustT(self):
    try:
      et = self.values[2].translate(None, 'A')
      return(int(et))
    except:
      return(-1)

  def getChamberT(self):
    try:
      return(int(self.values[3].translate(None, 'B')))
    except:
      return(-1)

  def getPrimSpeed(self):
    try:
      ps = self.values[4].translate(None, 'P')
      return(int(ps))
    except:
      return(-1)

  def getSecSpeed(self):
    try:
      ss = self.values[6].translate(None, 'S')
      return(int(ss))
    except:
      return(-1)

  def getO2(self):
    try:
      O2 = self.values[5].translate(None, 'O')
      return(float(O2))
    except:
      return(-1)

  def getReduction(self):
    try:
      return(int(self.values[7].translate(None, 'R')))
    except:
      return(-1)

  def getLosses(self):
    try:
      return(float(self.values[8].translate(None, 'V')))
    except:
      return(-1) 

  def getHeatExchangerT(self):
    try:
      return(float(self.values[13].translate(None, 'Sp')))
    except:
      return(-1) 
# ===========================================================================
# End of Class FlammtronikData
# ===========================================================================

# ===========================================================================
# Class RLA
# ===========================================================================
class RLAControl:
  def __init__(self, mixerClass, tempInClass, tempOutClass, flammtronik):
    self.mixerClass = mixerClass
    self.tempInClass = tempInClass
    self.tempOutClass = tempOutClass
    self.flammtronik = flammtronik
    self.pumpStartTemp = 65 #Emergency value
    t = Thread(target = self.controlRLA)
    t.setDaemon(True)
    t.start()
 
  def controlRLA(self):
    self.active = 1
    while self.active:
      if self.tempOutClass.getTemp() > self.pumpStartTemp or self.tempInClass.getTemp() > self.pumpStartTemp or self.flammtronik.getPrimSpeed() > 0 or self.flammtronik.getSecSpeed() > 0:
        os.system('gpio write 1 1') #RLA Pump on
      else:
        os.system('gpio write 1 0') #RLA Pump off 
      time.sleep(10)

  def setRLATemp(self, value):
    self.mixerClass.setTemp(value)

  def getRLAOutTemp(self):
    return(self.tempOutClass.getTemp())
    #return(self.flammtronik.getBoilerT())

  def getRLAInTemp(self):
    return(self.tempInClass.getTemp())

# ===========================================================================
# End of Class RLA
# ===========================================================================

# ===========================================================================
# Class HeatExchanger
# ===========================================================================
class HeatExchanger:
  def __init__(self, classFT, setPoint):
    self.classFT = classFT
    self.setPoint = setPoint
    t = Thread(target = self.controlHeatExchanger)
    t.setDaemon(True)
    t.start()
 
  def controlHeatExchanger(self):
    pumpOn = 0
    os.system('gpio write 2 0') #HE Pump off 
    self.active = 1
    while True:
      if self.active == 1:
        if pumpOn == 1:
          if self.getHETemp() > self.setPoint:
            os.system('gpio write 2 0') #HE Pump off 
            pumpOn = 0
        else:
          if self.getHETemp() < self.setPoint:
            os.system('gpio write 2 1') #HE Pump on 
            pumpOn = 1
      else:
        os.system('gpio write 2 0') #HE Pump off
        pumpOn = 0
      time.sleep(5)

  def setHETemp(self, value):
    self.setPoint = value

  def getHETemp(self):
    return(self.classFT.getHeatExchangerT())

  def activateHeatExchanger(self):
    self.active = 1

  def deactivateHeatExchanger(self):
    self.active = 0

# ===========================================================================
# End of Class HeatExchanger
# ===========================================================================

# ===========================================================================
# Class HeatingCurve
# ===========================================================================
class HeatingCurve:
  def __init__(self, mixerClass, outsideTempClass, bufferTempClass):
    self.mixerClass = mixerClass
    self.outsideTempClass = outsideTempClass
    self.baseTemp = 60 # at 0 Celsius outside
    self.bufferTempClass = bufferTempClass
    t = Thread(target = self.controlHeat)
    time.sleep(5) #Give outsideTempClass a chance to start first
    t.setDaemon(True)
    t.start()
 
  def controlHeat(self):
    self.active = 1
    while self.active:
      if (self.outsideTempClass.getTemp() > 40 and self.outsideTempClass.getTemp() < 85):
        os.system('gpio write 0 0')
      else:
        os.system('gpio write 0 1')
      self.setpoint = self.baseTemp - self.outsideTempClass.getTemp()
      if self.outsideTempClass.getTemp() > 0:
        self.setpoint -= self.outsideTempClass.getTemp()
      if self.setpoint > 100 or self.setpoint < 0:
        self.setpoint = self.baseTemp
      self.mixerClass.setTemp(self.setpoint)  
      time.sleep(150)

  def setBaseTemp(self, value):
    self.baseTemp = value

  def getBaseTemp(self):
    return(self.baseTemp)

  def getSetPoint(self):
    return(self.setpoint)

# ===========================================================================
# End of Class HeatingCurve
# ===========================================================================


# ===========================================================================
# Class GUI
# ===========================================================================
from Tkinter import *
import ttk
from random import randint


class GUI:

  def onRLAScale(self, value):
    self.RLATemp.set(round(float(value), 0))
    self.rla.setRLATemp(float(value))

  def onHWScale(self, value):
    self.hWTemp.set(round(float(value), 0))
    self.hc.setBaseTemp(float(value))

  def onWHButton(self):
    if self.whButton.config('text')[-1][2] == 'active':
        self.whButton.config(text='Heat Exchanger off')
        self.he.deactivateHeatExchanger()
    else:
        self.whButton.config(text='Heat Exchanger active')
        self.he.activateHeatExchanger()

  def updateData(self):
    self.root.after(1000, self.updateData)
    self.actO2.set(str(self.ft.getO2()) + "%")
    self.chamber.set(str(self.ft.getChamberT()) + u"\N{DEGREE SIGN}C")
    self.actET.set(str(self.ft.getExhaustT()) + u"\N{DEGREE SIGN}C")
    self.actEW.set(round(self.rla.getRLAOutTemp(), 1))  
    self.actBlower1.set(str(self.ft.getPrimSpeed()) + "%")
    self.actBlower2.set(str(self.ft.getSecSpeed()) + "%")
    self.tank1.set(str(round(self.t1.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank2.set(str(round(self.t2.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank3.set(str(round(self.t3.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank4.set(str(round(self.t4.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank5.set(str(round(self.t5.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank6.set(str(round(self.t6.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank7.set(str(round(self.t7.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank8.set(str(round(self.t8.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank9.set(str(round(self.t9.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank10.set(str(round(self.t10.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank11.set(str(round(self.t11.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.tank12.set(str(round(self.t12.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.rlaIn.set(str(round(self.rla.getRLAOutTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.rlaOut.set(str(round(self.rla.getRLAInTemp(), 1)) + u"\N{DEGREE SIGN}C")
    #self.rlaOut.set(str(round(self.ft.getBoilerT(), 1)) + u"\N{DEGREE SIGN}C")
    self.outside.set(str(round(self.os.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.mixforward.set(str(round(self.mf.getTemp(), 1)) + u"\N{DEGREE SIGN}C")
    self.mixsetpoint.set(str(round(self.hc.getSetPoint(), 1)) + u"\N{DEGREE SIGN}C")

  def __init__(self, rla, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, hc, ft, mixforward, outside, he):
    self.rla = rla
    #self.alarm = alarm
    self.ft = ft
    self.t1 = t1
    self.t2 = t2
    self.t3 = t3
    self.t4 = t4
    self.t5 = t5
    self.t6 = t6
    self.t7 = t7
    self.t8 = t8
    self.t9 = t9
    self.t10 = t10
    self.t11 = t11
    self.t12 = t12
    self.hc = hc
    self.os = outside
    self.mf = mixforward
    self.he = he
    root = Tk()
    self.root = root
    root.title("GasyPi Heating System Control")
    root.geometry("480x272+0+0")
    self.mainframe = ttk.Notebook(root, padding="6 6 12 12")
    self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    f0 = ttk.Frame(self.mainframe, padding="6 6 12 12", height = 250)
    f3 = ttk.Frame(self.mainframe)
    f4 = ttk.Frame(self.mainframe)
    f5 = ttk.Frame(self.mainframe)
    #f6 = ttk.Frame(self.mainframe)
    f7 = ttk.Frame(self.mainframe)

    tab0 = self.mainframe.add(f0, text='Burner')
    tab7 = self.mainframe.add(f7, text='Buffer')
    tab4 = self.mainframe.add(f4, text='Heat')
    tab5 = self.mainframe.add(f5, text='Waterheater')
    tab3 = self.mainframe.add(f3, text='RLA')
    #tab6 = self.mainframe.add(f6, text='Oiler')

    self.mainframe.columnconfigure(0, weight=1)
    self.mainframe.rowconfigure(0, weight=1)
    self.RLATemp = StringVar()

    self.RLATemp.set("65.0")
    self.onRLAScale(65)

    self.hWTemp = StringVar()
    self.hWTemp.set(str(self.hc.getBaseTemp()))
    self.ExP = StringVar()
    self.actO2 = StringVar()
    self.chamber = StringVar()
    self.actET = StringVar()
    self.actEW = StringVar()
    self.actBlower1 = StringVar()
    self.actBlower2 = StringVar()
    self.tank1 = StringVar()
    self.tank2 = StringVar()
    self.tank3 = StringVar()
    self.tank4 = StringVar()
    self.tank5 = StringVar()
    self.tank6 = StringVar()
    self.tank7 = StringVar()
    self.tank8 = StringVar()
    self.tank9 = StringVar()
    self.tank10 = StringVar()
    self.tank11 = StringVar()
    self.tank12 = StringVar()

    self.rlaOut = StringVar()
    self.rlaIn = StringVar()
    self.outside = StringVar()
    self.mixforward = StringVar()
    self.mixsetpoint = StringVar()
   

    orlanImage = PhotoImage(file='Orlan.gif')
    ttk.Label(f0, image = orlanImage).place(x=120, y =10)
    ttk.Label(f0, text = "O2 in Flue Gas", font = 'helvetica 10', borderwidth=2, relief="groove", width = 14).place(x=30, y=5)
    ttk.Label(f0, textvariable = self.actO2, foreground = 'red', font = 'helvetica 20', borderwidth = 2, relief="groove", width = 7).place(x=30, y=20)
    ttk.Label(f0, textvariable = self.actET, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 7).place(x=30, y=80)
    ttk.Label(f0, text = "Flue Gas Temp.", font = 'helvetica 10', borderwidth=2, relief="groove", width = 14).place(x=30, y=65)
    ttk.Label(f0, text = "Primary Blower", font = 'helvetica 10', borderwidth=2, relief="groove", width = 16).place(x=330, y=80)
    ttk.Label(f0, textvariable = self.actBlower1, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 8).place(x=330, y=95)
    ttk.Label(f0, text = "Secondary Blower", font = 'helvetica 10', borderwidth=2, relief="groove", width = 16).place(x=330, y=140)
    ttk.Label(f0, textvariable = self.actBlower2, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 8).place(x=330, y=155)
    ttk.Label(f0, text = "Boiler in", font = 'helvetica 10', borderwidth=2, relief="groove", width = 14).place(x=30, y=130)
    ttk.Label(f0, textvariable = self.rlaIn, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 7).place(x=30, y=145)
    ttk.Label(f0, text = "Boiler out", font = 'helvetica 10', borderwidth=2, relief="groove", width = 14).place(x=30, y=175)
    ttk.Label(f0, textvariable = self.rlaOut, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 7).place(x=30, y=190)
    ttk.Label(f0, textvariable = self.chamber, background = '#FFFCD9', foreground = 'red', font = 'helvetica 20', borderwidth=0, relief="groove").place(x=195, y=173)
 
    tankImage = PhotoImage(file='Tanks.gif')
    ttk.Label(f7, image = tankImage).place(x=0, y =10)
    ttk.Label(f7, textvariable = self.tank1, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=20, y=50)
    ttk.Label(f7, textvariable = self.tank2, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=20, y=100)
    ttk.Label(f7, textvariable = self.tank3, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=20, y=150)
    ttk.Label(f7, textvariable = self.tank4, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=128, y=50)
    ttk.Label(f7, textvariable = self.tank5, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=128, y=100)
    ttk.Label(f7, textvariable = self.tank6, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=128, y=150)
    ttk.Label(f7, textvariable = self.tank7, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=240, y=50)
    ttk.Label(f7, textvariable = self.tank8, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=240, y=100)
    ttk.Label(f7, textvariable = self.tank9, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=240, y=150)
    ttk.Label(f7, textvariable = self.tank10, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=347, y=50)
    ttk.Label(f7, textvariable = self.tank11, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=347, y=100)
    ttk.Label(f7, textvariable = self.tank12, foreground = 'red', font = 'helvetica 18', borderwidth = 2, relief="groove", width = 6).place(x=347, y=150)
    

    self.whButton = ttk.Button(f5, text = "Heat Exchanger active", command = self.onWHButton)
    self.whButton.grid(column = 1, row = 1, sticky = W, padx = 5, pady = 5)

    self.updateData() #Start Update Timer
   
    ttk.Label(f3, text=u"Target RLA Temperature in \N{DEGREE SIGN}C").grid(column = 1, row = 1, sticky = W, padx = 5, pady = 5)
    ttk.Scale(f3, orient=HORIZONTAL, length = 200, from_= 60, to= 85, command = self.onRLAScale, variable = self.RLATemp).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f3, textvariable=self.RLATemp).grid(column = 3, row = 1, sticky =W , padx = 5, pady = 5)
   
    ttk.Label(f4, text=u"Target Heating Water Temp. in \N{DEGREE SIGN}C").grid(column=1, row=1, sticky=W, padx=5, pady=5)
    ttk.Scale(f4, orient=HORIZONTAL, length=200, from_=35, to=85, command = self.onHWScale, variable = self.hWTemp).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f4, textvariable=self.hWTemp).grid(column=3, row=1, sticky=W, padx=5, pady=5)
    ttk.Label(f4, text = "Outside Temp.", font = 'helvetica 10', borderwidth=2, relief="groove", width = 14).place(x=5, y=30)
    ttk.Label(f4, textvariable = self.outside, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 7).place(x=5, y=45)
    ttk.Label(f4, text = "Water Temp.", font = 'helvetica 10', borderwidth=2, relief="groove", width = 14).place(x=100, y=30)
    ttk.Label(f4, textvariable = self.mixforward, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 7).place(x=100, y=45)
    ttk.Label(f4, text = "Water Setpoint", font = 'helvetica 10', borderwidth=2, relief="groove", width = 14).place(x=195, y=30)
    ttk.Label(f4, textvariable = self.mixsetpoint, foreground = 'red', font = 'helvetica 20', borderwidth=2, relief="groove", width = 7).place(x=195, y=45)

    root.mainloop()

# ===========================================================================
# End of Class GUI
# ===========================================================================

# ===========================================================================
# Main Code
# ===========================================================================
bexitt = OneWire("/sys/bus/w1/devices/28-000004abfb55/w1_slave") # Boilerwater exit temp
bentryt = OneWire("/sys/bus/w1/devices/28-000005e5ccc8/w1_slave") # Boilerwater entry temp
#mixreturn = OneWire("/sys/bus/w1/devices/28-000005143eb4/w1_slave") # Mixer heating water forward temp
mixforward = OneWire("/sys/bus/w1/devices/28-000005f403dc/w1_slave") #Mixer heating return temp
tank1top = OneWire("/sys/bus/w1/devices/28-000005f1ff79/w1_slave") #Buffer Tank 1 top
tank1middle = OneWire("/sys/bus/w1/devices/28-000005f2fe6f/w1_slave") #Buffer Tank 1 middle
tank1bottom = OneWire("/sys/bus/w1/devices/28-000005f2f56c/w1_slave") #Buffer Tank 1 bottom
tank2top = OneWire("/sys/bus/w1/devices/28-000005f3d4e2/w1_slave") #Buffer Tank 2 top
tank2middle = OneWire("/sys/bus/w1/devices/28-000005f375bc/w1_slave") #Buffer Tank 2 middle
tank2bottom = OneWire("/sys/bus/w1/devices/28-000005f318a9/w1_slave") #Buffer Tank 2 bottom
tank3top = OneWire("/sys/bus/w1/devices/28-051686d678ff/w1_slave")
tank3middle = OneWire("/sys/bus/w1/devices/28-051686d3b7ff/w1_slave")
tank3bottom = OneWire("/sys/bus/w1/devices/28-0416864c2bff/w1_slave")
tank4top = OneWire("/sys/bus/w1/devices/28-0416861978ff/w1_slave") 
tank4middle = OneWire("/sys/bus/w1/devices/28-051686d9fbff/w1_slave")
tank4bottom = OneWire("/sys/bus/w1/devices/28-051686d745ff/w1_slave")
outside = OneWire("/sys/bus/w1/devices/28-000004bff14b/w1_slave") 
ric = MixerControl(bentryt, 65, 0.5, 0.05, 0.5, 20, 6, 5)
roomHeat = MixerControl(mixforward, 35, 0.2, 0.01, 1, 10, 4, 3)
hc = HeatingCurve(roomHeat, outside, tank1top)
ft = FTData(outside, mixforward, bentryt, bexitt, tank1top, tank1middle, tank1bottom, tank2top, tank2middle, tank2bottom, tank3top, tank3middle, tank3bottom, tank4top, tank4middle, tank4bottom)
#ric = Pt1000MixerControl(ft, 75, 0.1, 0.03, 3, 60, 6, 5)
rla = RLAControl(ric, bexitt, bentryt, ft)
he = HeatExchanger(ft, 30)
GUI(rla, tank1top, tank1middle, tank1bottom, tank2top, tank2middle, tank2bottom, tank3top, tank3middle, tank3bottom, tank4top, tank4middle, tank4bottom, hc, ft, mixforward, outside, he)
quit()
