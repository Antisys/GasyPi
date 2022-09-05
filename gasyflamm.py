#!/usr/bin/python

# ===========================================================================
# Class PlotlyGraph
# ===========================================================================
import plotly.plotly as py
import plotly.tools as tls
from plotly.graph_objs import *
import numpy as np
import datetime 
import time 

class PlotlyGraph:
  def __init__(self):
    self.openPlotlyConnection()

  def registerStream(self):
    py.sign_in('hobbele', 'onowo8hs9d')
    trace1 = Scatter(x=[], y=[], stream=dict(token='w3rwp5z8zo', maxpoints=2400))
    trace2 = Scatter(x=[], y=[], stream=dict(token='uxaonwccn8'))
    trace3 = Scatter(x=[], y=[], stream=dict(token='w1720066w6'))
    trace4 = Scatter(x=[], y=[], stream=dict(token='3oz34ims62'))
    trace5 = Scatter(x=[], y=[], stream=dict(token='qk9qd38j1n'))
    layout = Layout(title='GasyFlamm Graph')
    data = Data([trace1, trace2, trace3, trace4, trace5])
    #fig = Figure(data=[trace1, trace2, trace3, trace4, trace5], layout=layout)
    #print py.plot(fig, filename='GasyFlamm Data Log')

  def openPlotlyConnection(self):
    self.s1 = py.Stream('w3rwp5z8zo')
    self.s2 = py.Stream('uxaonwccn8')
    self.s3 = py.Stream('w1720066w6')
    self.s4 = py.Stream('3oz34ims62')
    self.s5 = py.Stream('qk9qd38j1n')
    self.s1.open()
    self.s2.open()
    self.s3.open()
    self.s4.open()
    self.s5.open()

  def sendData(self, flue, o2, speed1, speed2, flame):
    #try:
      x=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
      self.s1.write(dict(x = x,y = flue))
      self.s2.write(dict(x = x, y = o2)) 
      self.s3.write(dict(x = x, y = speed1))
      self.s4.write(dict(x = x, y = speed2))
      self.s5.write(dict(x = x, y = flame))
    #except:
      #self.closePlotlyConnection()
      #self.openPlotlyConnection()

  def closePlotlyConnection(self):
    self.s1.close()
    self.s2.close()
    self.s3.close()
    self.s4.close()
    self.s5.close()
# ===========================================================================
# End of Class PlotlyGraph
# =============================================================

# ===========================================================================
# Class NewDatalogger
# ===========================================================================
import datetime
import gdata.spreadsheet.service
import gdata.docs.client

class NewDatalogger:
  def __init__(self, login, password):
    self.openSpreadsheet(login, password)
    self.login = login
    self.password = password

  def insertRow(self, values):
    tday = datetime.date.weekday(datetime.date.today())
    if(tday != self.lastDay):
      self.openSpreadsheet()
    row = { "a": values[0], "b": values[1], "c": values[2], "d": values[3], "e": values[4], "f": values[5], "g": values[6], "h": values[7], "i": values[8], "j": values[9], "k": values[10]} 
    try:
      self.gs.InsertRow(row, self.spreadsheet_key, self.worksheetID)
    except:
      self.openSpreadsheet(self, self.login, self.password)

  def openSpreadsheet(self, login, password):
    self.email = login
    self.password = password
    self.source = 'GasyFlamm'
    self.worksheetID = 'od6'
    foldername = 'GasyFlamm'
    tday = datetime.date.today()
    self.lastDay = datetime.date.weekday(tday)
    filename = 'GasyFlamm Log ' + str(tday)
    gc = gdata.docs.client.DocsClient()
    gc.ClientLogin(self.email, self.password, self.source)

    try: #Try open existing folder
      q = gdata.docs.client.DocsQuery(title=foldername, title_exact='true', show_collections='true')
      folder = gc.GetResources(q=q).entry[0]
      contents = gc.GetResources(uri=folder.content.src)
    except: #Create new folder
      folder = gdata.docs.data.Resource('folder', foldername)
      contents = gc.CreateResource(folder) 
      q = gdata.docs.client.DocsQuery(title=foldername, title_exact='true', show_collections='true')
      folder = gc.GetResources(q=q).entry[0]
      contents = gc.GetResources(uri=folder.content.src)

    try: #Try open existing spreadsheet
      q = gdata.docs.client.DocsQuery(title=filename, title_exact='true', show_collections='true')
      document = gc.GetResources(q=q).entry[0]
      self.spreadsheet_key = document.GetId().split("%3A")[1]
      self.ssLogin()
    except:
      try: #Copy Template
        q = gdata.docs.client.DocsQuery(title='GasyFlamm Log Template', title_exact='true', show_collections='true')
        document = gc.GetResources(q=q).entry[0]
        copy = gc.CopyResource(document, filename)
        gc.MoveResource(copy, folder, False)
        self.spreadsheet_key = copy.GetId().split("%3A")[1]
        self.ssLogin()
      except: #Create new spreadsheet
        document = gdata.docs.data.Resource('spreadsheet', filename)
        document = gc.CreateResource(document, collection=folder)
        self.spreadsheet_key = document.GetId().split("%3A")[1]
        self.ssLogin()
        headers = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"]
        for i, header in enumerate(headers):
          entry = self.gs.UpdateCell(row=1, col=i+1, inputValue=header, key=self.spreadsheet_key, wksht_id=self.worksheetID)
        row = { "a": "Zeit", "b": "Kessel Temp.", "c": "AbgasTemp", "d": "BrennkammerTemp", "e": "Primaerleistung", "f": "Restsauerstoff", "g": "Sekundaerleistung", "h": "Ruecknahme", "i": "Abgasverlust", "j": "Ladepumpe", "k": "RLA"}
        self.gs.InsertRow(row, self.spreadsheet_key, self.worksheetID)

  def ssLogin(self):
    self.gs = gdata.spreadsheet.service.SpreadsheetsService()
    self.gs.email = self.email
    self.gs.password = self.password
    self.gs.source = self.source
    self.gs.ProgrammaticLogin()
# ===========================================================================
# End of NewDatalogger
# ===========================================================================

import serial
import datetime 

LOGIN = "qschrauber@gmail.com"
PASSWORD = "45134000"
SERIALPORT = "/dev/ttyAMA0"
ALTERNATE_SERIALPORT = "/dev/ttyUSB0"
BAUDRATE = 38400

nd = NewDatalogger(LOGIN, PASSWORD)
plotly = PlotlyGraph()
#plotly.registerStream()
ser = serial.Serial(ALTERNATE_SERIALPORT, BAUDRATE)
ser.open()
ser.flushInput()
ser.readline()

while True:
  flammString = ser.readline()
  #flammString = "T0407.7 K020.9 A104 B00560 P050 O4.5 S080 R000 V06.2 P0 Z000 w--- x--- y--- z---"
  flammString = flammString.translate(None, 'TKABPOSRVPZXY-\r\n\x11')
  googleString = flammString.replace('.', ',')
  values = googleString.split(' ')
  plotstr = flammString.split(' ')
  if int(values[4]) > 0:
    values[0] = datetime.datetime.now().strftime('%H:%M:%S')
    print values
    nd.insertRow(values)
    plotly.sendData(float(plotstr[2]), float(plotstr[5]), float(plotstr[4]), float(plotstr[6]), float(plotstr[3]))