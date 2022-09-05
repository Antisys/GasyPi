import threading
import MySQLdb
import time
import smbus

# ===========================================================================
# Class FT-Daten-Import
# ===========================================================================
class FT_Daten:
  def __init__(self):
    self.stopSig = 0
    self.readData()
    self.timestamp = -1
    self.boiler_temp = -1
    self.flue_gas_temp = -1
    self.chamber_temp = -1
    self.primary_power = -1
    self.oxygen = -1
    self.secondary_power = -1
    self.reduction = -1
    self.losses = -1


  def readData(self):
    db = MySQLdb.connect(host="localhost", user="gasypi", passwd="gasypi", db="Heater_DB")
    cur = db.cursor() 
    string = "SELECT * FROM (SELECT * FROM Heater_Data ORDER BY ID DESC LIMIT 1) sub ORDER BY ID ASC"
    cur.execute(string)    
    data = cur.fetchall()
    cur.close()
    db.close()
    self.timestamp = data[0][1]
    self.boiler_temp = data[0][2]
    self.flue_gas_temp = data[0][3]
    self.chamber_temp = data[0][4]
    self.primary_power = data[0][5]
    self.oxygen = data[0][6]
    self.secondary_power = data[0][7]
    self.reduction = data[0][8]
    self.losses = data[0][9]
    
    self.timerThread = threading.Timer(6, self.readData) #Starte Endlosschleife in eigenem Thread
    if(self.stopSig == 0):
      self.timerThread.start()

  def getRestO2(self):
    return(self.oxygen)

  def __del__(self):
    self.stopSig = 1
# ===========================================================================
# End of Class FT-Daten-Import
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
    def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0, Integrator_max=500, Integrator_min=-500):

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
        print self.P_value, self.I_value, self.D_value
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

    def setKi(self,I):
        self.Ki=I

    def setKd(self,D):
        self.Kd=D

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
# Class Sekundaer-Steuerung
# ===========================================================================
class Sekundaer_Steuerung:
  def __init__(self, flammtronik):
    self.PID=PID(5, 0.2, 7, 0, 0, 5, -5)
    self.PID.setPoint(4.5)
    self.SecPercentMin = 0
    self.SecPercentMax = 100
    self.actSecPercent = 0
    self.minSecPercent = 21  #18 keeps it alive, 21 can start it
    self.stopSig = 0
    self.ft = flammtronik
    self.I2Cbus = smbus.SMBus(1)
    #self.setSecondaryPower(100)
    #time.sleep(1)
    self.Controller()

  def setSecondaryPower(self, power): #power ist in %
    if power < self.minSecPercent:
      power = self.minSecPercent
    print power
    power = 100 - power               #und muss fuer das Dimmermodul umgerechnet werden 
    self.I2Cbus.write_byte_data(0x27, 0x81, int(power))

  def Controller(self):
    if self.ft.getRestO2() == -1:
      self.actSecPercent = 0 #Notfallmodus, wenn keine O2 Werte geliefert werden
    else:
      self.actSecPercent = self.actSecPercent + round(self.PID.update(self.ft.getRestO2()))
      if self.actSecPercent > self.SecPercentMax:
        self.actSecPercent = self.SecPercentMax
      if self.actSecPercent < self.SecPercentMin:
        self.actSecPercent = self.SecPercentMin
    self.setSecondaryPower(self.actSecPercent)
    #print self.ft.getRestO2(), self.actSecPercent
    
    
    self.timerThread = threading.Timer(6, self.Controller) #Starte Endlosschleife in eigenem Thread
    if(self.stopSig == 0):
      self.timerThread.start()

# ===========================================================================
# End of Class Sekundaer-Steuerung
# ===========================================================================
flammtronik = FT_Daten()
sek_steuerung = Sekundaer_Steuerung(flammtronik)

while(True):
  pass
