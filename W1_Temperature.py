#!/usr/bin/python

# ===========================================================================
# Class OneWire
# ===========================================================================
from threading import Thread
import signal
import os
import time
import zmq

class OneWire:
  def __init__(self, file, name, verbose):
    signal.signal(signal.SIGINT, self.signal_handler)
    self.file = "/sys/bus/w1/devices/" + file + "/w1_slave"
    self.temperature = -999
    context = zmq.Context()
    self.socket = context.socket(zmq.PUB)
    self.socket.connect("tcp://*:5557")
    self.alive = False
    self.name = name 
    self.verbose = verbose
    self.exit = False
    heartBeatThreat = Thread(target = self.heartBeat) #The W1 driver may get stuck.
    heartBeatThreat.setDaemon(True)                   #In that case also opening the W1 temperature file
    heartBeatThreat.start()                           #will get stuck. To make that visible the heartBeat
                                                      #task is necessary. Otherwise the process will just 
                                                      #get stuck without further temperature update 

    while True:                                       
      self.alive = True
      if self.exit:
        break
      text = ""
      try:
        myfile = open(self.file)
      except:
        print "Can't open specified sensor. Are you sure you entered it's address correctly?"
        break
      try:
        text = myfile.read()
        myfile.close()
      except:
        text = "NO"
        self.temperature = -999
      if text.find("NO") == -1:
        temp_data = text.split()[-1]
        temp = float(temp_data[2:])
        self.temperature = temp / 1000
        self.socket.send("%s: %.3f" % (self.name, self.temperature))
        if self.verbose:
          print("%s: %.3f" % (self.name, self.temperature))
      #End of while loop
    os.kill(os.getpid(), signal.SIGKILL)

  def signal_handler(self, signal, frame):
    print('You pressed Ctrl+C! Please allow a few seconds to exit gracefully.')
    self.exit = True

  def heartBeat(self):
    while not self.exit:
      time.sleep(10)
      if(self.alive == False):
        self.temperature = -999
        self.socket.send("%s: %.3f" % (self.name, self.temperature))
      self.alive = False 

# ===========================================================================
# End of Class OneWire
# ===========================================================================

# ===========================================================================
# GasyPi 1-Wire Temperature Server
# ===========================================================================
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--id', type=str, required=True, help='Add the OneWire thermocouple ID ind the format 28-000000000001. The number after 28- must be 12 digits.')
parser.add_argument('-n', '--name', required=True, help='Give your thermocouple a name')
parser.add_argument('-v', '--verbose', action='count', help='Prints the temperature to the console.')
args = parser.parse_args()
if len(args.id) != 15:
  print "Thermocouple ID has the wrong format. It should be something like this: 28-000000000001"
  quit()
file = args.id
name = args.name 
verbose = args.verbose
OneWire(file, name, verbose)

