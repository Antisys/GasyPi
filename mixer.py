#!/usr/bin/python

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
# Class Listener
# ===========================================================================
class Listener:
  def __init__(self):
    # Socket to talk to server
    context = zmq.Context()
    self.socket = context.socket(zmq.SUB)
    self.socket.connect ("tcp://*:%s" % port)
    self.socket.setsockopt(zmq.SUBSCRIBE, "W1_Temp_Boiler_exit:")
    self.ListenerLoop()

  def ListenerLoop(self):
    while True:
      string = self.socket.recv()
      print string
# ===========================================================================
# End of Class Listener
# ===========================================================================


import sys
import zmq
import argparse
import threading
import time
import fcntl

port = 5560

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', required=True, help='The name of the sensor, which shows the temperature of the controlled water mixer')
parser.add_argument('-s', '--set', required=True, help='The setpoint for the controller')
parser.add_argument('-p', '--P', required=True, help='The gain constant (P) for the PID controller')
parser.add_argument('-i', '--I', required=True, help='The integration constant (I) for the PID controller')
parser.add_argument('-d', '--D', required=True, help='The Derivation Constant (D) for the PID controller')
parser.add_argument('-t', '--time', required=True, help='The sampling time for the PID controller')
parser.add_argument('-c', '--cold', required=True, help='The GPIO pin to turn the mixer colder')
parser.add_argument('-w', '--warm', required=True, help='The GPIO pin to turn the mixer warmer')
parser.add_argument('-u', '--pump', required=True, help='The GPIO pin to turn the pump on and off')
parser.add_argument('-X', '--max', help='The positive allowed integration sum')
parser.add_argument('-N', '--min', help='The negative allowed integration sum')
parser.add_argument('-v', '--verbose', action='count', help='Prints the control data to the console.')
args = parser.parse_args()
sensorName = args.name
targetTemp = args.set
tP = args.P
tI = args.I
tD = args.D
samplingTime = args.time
gpioWarm = args.warm
gpioCold = args.cold
gpioPump = args.pump

lock_file = 'gasypi_GPIO' + gpioWarm + '.lock'
fp1 = open(lock_file, 'w')
try:
  fcntl.lockf(fp1, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
  print "Error: The GPIO pin for warm is already in use."
  quit()

lock_file = 'gasypi_GPIO' + gpioCold + '.lock'
fp2 = open(lock_file, 'w')
try:
  fcntl.lockf(fp2, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
  print "Error: The GPIO pin for cold is already in use."
  quit()

lock_file = 'gasypi_GPIO' + gpioPump + '.lock'
fp3 = open(lock_file, 'w')
try:
  fcntl.lockf(fp3, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
  print "Error: The GPIO pin for the pump is already in use."
  quit()

pidClass = PID(tP, tI, tD)
pidClass.setPoint(targetTemp)

t = threading.Thread(target = Listener)
t.setDaemon(True)
t.start()

while True:
  time.sleep(1)


