#!/usr/bin/python

# ===========================================================================
# Class Listener
# ===========================================================================
import signal
import zmq

class Proxy:
  def __init__(self):
    signal.signal(signal.SIGINT, self.signal_handler)
    try:
      self.context = zmq.Context(1)
      # Socket facing clients
      self.frontend = self.context.socket(zmq.SUB)
      self.frontend.bind("tcp://*:5557")
        
      self.frontend.setsockopt(zmq.SUBSCRIBE, "")
        
      # Socket facing services
      self.backend = self.context.socket(zmq.PUB)
      self.backend.bind("tcp://*:5560")

      zmq.device(zmq.FORWARDER, self.frontend, self.backend)
    except Exception, e:
      print e
      print "bringing down zmq device"
    finally:
      pass
      self.frontend.close()
      self.backend.close()
      self.context.term()

  def signal_handler(self, signal, frame):
    print('\r\nExiting proxy.')
    self.frontend.close()
    self.backend.close()
    self.context.term()
    quit()

# ===========================================================================
# End of Class Listener
# ===========================================================================
Proxy()