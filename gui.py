# ===========================================================================
# End of Class PlotlyGraph
# =============================================================

# ===========================================================================
# Class GUI
# ===========================================================================
from Tkinter import *
import ttk
from random import randint


class GUI:
  def onO2Scale(self, value):
    self.O2.set(round(float(value), 1))
    self.burnerClass.setTargetO2(float(value))
 
  def onExhaustScale(self, value):
    self.exhaustTemp.set(round(float(value), 0))
    self.burnerClass.setTargetTemp(float(value))

  def onExP(self, value):
    self.ExP.set(round(float(value), 1))
    self.burnerClass.setPrimaryP(float(value))

  def onExI(self, value):
    self.ExI.set(round(float(value), 1))
    self.burnerClass.setPrimaryI(float(value))

  def onExD(self, value):
    self.ExD.set(round(float(value), 1))
    self.burnerClass.setPrimaryD(float(value))

  def onExT(self, value):
    self.ExT.set(round(float(value), 1))
    self.burnerClass.setPrimaryTimer(float(value))

  def onO2P(self, value):
    self.O2P.set(round(float(value), 1))
    self.burnerClass.setSecondaryP(float(value))

  def onO2I(self, value):
    self.O2I.set(round(float(value), 1))
    self.burnerClass.setSecondaryI(float(value))

  def onO2D(self, value):
    self.O2D.set(round(float(value), 1))
    self.burnerClass.setSecondaryD(float(value))

  def onO2T(self, value):
    self.O2T.set(round(float(value), 1))
    self.burnerClass.setSecondaryTimer(float(value))

  def onRLAScale(self, value):
    self.RLATemp.set(round(float(value), 0))
    self.rla.setRLATemp(float(value))

  def onHWScale(self, value):
    self.hWTemp.set(round(float(value), 0))

  def onWHButton(self):
    self.whButton.state(['disabled'])
    self.root.after(1801000, self.activateWHButton) #Time in Microseconds
    self.alarm.startWaterHeater(1800) #Time in Seconds

  def activateWHButton(self):
    self.whButton.state(['!disabled'])
 
  def updateData(self):
    self.root.after(1000, self.updateData)
    self.actO2.set(self.lc.getRestO2() + "%")
    self.actET.set(str(self.ac.getTemp()) + u"\N{DEGREE SIGN}C")
    self.actEW.set(round(self.rla.getRLAOutTemp(), 1))
    self.actBlower1.set(str(self.burnerClass.getPrimarySpeed()) + "%")
    self.actBlower2.set(str(self.burnerClass.getSecondarySpeed()) + "%")

  def __init__(self, bc, rla, alarm, lc, ac):
    self.burnerClass = bc
    self.rla = rla
    self.alarm = alarm
    self.lc = lc
    self.ac = ac
    root = Tk()
    self.root = root
    root.title("GasiPy Heating System Control")
    root.geometry("480x272")
    self.mainframe = ttk.Notebook(root, padding="6 6 12 12")
    self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    f0 = ttk.Frame(self.mainframe, padding="6 6 12 12")
    f1 = ttk.Frame(self.mainframe, padding="6 6 12 12")
    f2 = ttk.Frame(self.mainframe)
    f3 = ttk.Frame(self.mainframe)
    f4 = ttk.Frame(self.mainframe)
    f5 = ttk.Frame(self.mainframe)
    f6 = ttk.Frame(self.mainframe)

    tab0 = self.mainframe.add(f0, text='Readings')
    tab4 = self.mainframe.add(f4, text='Heat')
    tab5 = self.mainframe.add(f5, text='Waterheater')
    tab1 = self.mainframe.add(f1, text='Blower I')
    tab2 = self.mainframe.add(f2, text='Blower II')
    tab3 = self.mainframe.add(f3, text='RLA')
    tab6 = self.mainframe.add(f6, text='Oiler')

    self.mainframe.columnconfigure(0, weight=1)
    self.mainframe.rowconfigure(0, weight=1)
    self.O2 = StringVar()
    self.O2.set(str(self.burnerClass.getTargetO2()))
    self.exhaustTemp = StringVar()
    self.exhaustTemp.set(str(self.burnerClass.getTargetTemp()))
    self.RLATemp = StringVar()
    self.RLATemp.set("72.0")
    self.hWTemp = StringVar()
    self.hWTemp.set("45.0")
    self.ExP = StringVar()
    self.ExP.set(str(self.burnerClass.getPrimaryP()))
    self.ExI = StringVar()
    self.ExI.set(str(self.burnerClass.getPrimaryI()))
    self.ExD = StringVar()
    self.ExD.set(str(self.burnerClass.getPrimaryD()))
    self.ExT = StringVar()
    self.ExT.set(str(self.burnerClass.getPrimaryFreq()))
    self.O2P = StringVar()
    self.O2P.set(str(self.burnerClass.getSecondaryP()))
    self.O2I = StringVar()
    self.O2I.set(str(self.burnerClass.getSecondaryI()))
    self.O2D = StringVar()
    self.O2D.set(str(self.burnerClass.getSecondaryD()))
    self.O2T = StringVar()
    self.O2T.set(str(self.burnerClass.getSecondaryFreq()))
    self.actO2 = StringVar()
    self.actET = StringVar()
    self.actEW = StringVar()
    self.actBlower1 = StringVar()
    self.actBlower2 = StringVar()

    orlanImage = PhotoImage(file='Orlan.gif')
    ttk.Label(f0, image=orlanImage).place(x=120, y =10)#grid(column=11, row=1, columnspan = 10, rowspan = 20,sticky = W, padx=5, pady=5)
    ttk.Label(f0, textvariable = self.actO2, foreground = 'red', font = 'helvetica 20').place(x=85, y=5)
    ttk.Label(f0, textvariable = self.actET, foreground = 'red', font = 'helvetica 20').place(x=65, y=75)
    ttk.Label(f0, textvariable = self.actBlower1, foreground = 'red', font = 'helvetica 20').place(x=320, y=80)
    ttk.Label(f0, textvariable = self.actBlower2, foreground = 'red', font = 'helvetica 20').place(x=320, y=150)
 
    self.whButton = ttk.Button(f5, text = "Start Water Heater Pump for 30 Minutes", command = self.onWHButton)
    self.whButton.grid(column = 1, row = 1, sticky = W, padx = 5, pady = 5)

    #self.updateData() #Start Update Timer
    
    ttk.Label(f1, text=u"Target Exhaust Temp in \N{DEGREE SIGN}C").grid(column=1, row=1, sticky=W, padx=5, pady=5)
    ttk.Scale(f1, orient=HORIZONTAL, length=200, from_=120, to=250, command = self.onExhaustScale, variable = self.exhaustTemp).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f1, textvariable=self.exhaustTemp).grid(column=3, row=1, sticky=W, padx=5, pady=5)
    f11 = ttk.Labelframe(f1, text='PID Settings', padding="6 6 12 12")
    f11.grid(column = 1, row = 2, columnspan=3, sticky = (W, E, S))
    ttk.Label(f11, text="P value").grid(column=1, row = 1, sticky=W, padx=5, pady=5)
    ttk.Scale(f11, orient=HORIZONTAL, length=200, from_= 0, to = 20, command = self.onExP, variable = self.ExP).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f11, textvariable=self.ExP).grid(column=3, row = 1, sticky=W, padx=5, pady=5)
    myrow = 2
    ttk.Label(f11, text="I value").grid(column=1, row=myrow, sticky=W, padx=5, pady=5)
    ttk.Scale(f11, orient=HORIZONTAL, length=200, from_= 0, to = 20, command = self.onExI, variable = self.ExI).grid(column = 2, row = myrow, sticky=W, padx=5, pady=5)
    ttk.Label(f11, textvariable=self.ExI).grid(column=3, row=myrow, sticky=W, padx=5, pady=5)
    myrow +=1
    ttk.Label(f11, text="D value").grid(column=1, row=myrow, sticky=W, padx=5, pady=5)
    ttk.Scale(f11, orient=HORIZONTAL, length=200, from_= 0, to = 20, command = self.onExD, variable = self.ExD).grid(column = 2, row = myrow, sticky=W, padx=5, pady=5)
    ttk.Label(f11, textvariable=self.ExD).grid(column=3, row=myrow, sticky=W, padx=5, pady=5)
    myrow +=1
    ttk.Label(f11, text="Timer in seconds").grid(column=1, row=myrow, sticky=W, padx=5, pady=5)
    ttk.Scale(f11, orient=HORIZONTAL, length=200, from_= 0.1, to = 20, command = self.onExT, variable = self.ExT).grid(column = 2, row = myrow, sticky=W, padx=5, pady=5)
    ttk.Label(f11, textvariable=self.ExT).grid(column=3, row=myrow, sticky=W, padx=5, pady=5)
    
    ttk.Label(f2, text="Target O2 in %").grid(column=1, row=1, sticky = W, padx=5, pady=5)
    ttk.Scale(f2, orient=HORIZONTAL, length = 200, from_= 2.0, to = 10.0, command = self.onO2Scale, variable = self.O2).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f2, textvariable=self.O2).grid(column=3, row=1, sticky=W, padx=5, pady=5)
    f21 = ttk.Labelframe(f2, text='PID Settings', padding="6 6 12 12")
    f21.grid(column=1, row=2, columnspan=3, sticky=(W, E, S))
    ttk.Label(f21, text="P value").grid(column=1, row = 1, sticky=W, padx=5, pady=5)
    ttk.Scale(f21, orient=HORIZONTAL, length=200, from_= 0, to = 20, command = self.onO2P, variable = self.O2P).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f21, textvariable=self.O2P).grid(column=3, row = 1, sticky=W, padx=5, pady=5)
    myrow = 2
    ttk.Label(f21, text="I value").grid(column=1, row=myrow, sticky=W, padx=5, pady=5)
    ttk.Scale(f21, orient=HORIZONTAL, length=200, from_= 0, to = 20, command = self.onO2I, variable = self.O2I).grid(column = 2, row = myrow, sticky=W, padx=5, pady=5)
    ttk.Label(f21, textvariable=self.O2I).grid(column=3, row=myrow, sticky=W, padx=5, pady=5)
    myrow +=1
    ttk.Label(f21, text="D value").grid(column=1, row=myrow, sticky=W, padx=5, pady=5)
    ttk.Scale(f21, orient=HORIZONTAL, length=200, from_= 0, to = 20, command = self.onO2D, variable = self.O2D).grid(column = 2, row = myrow, sticky=W, padx=5, pady=5)
    ttk.Label(f21, textvariable=self.O2D).grid(column=3, row=myrow, sticky=W, padx=5, pady=5)
    myrow +=1
    ttk.Label(f21, text="Timer in seconds").grid(column=1, row=myrow, sticky=W, padx=5, pady=5)
    ttk.Scale(f21, orient=HORIZONTAL, length=200, from_= 0.1, to = 20, command = self.onO2T, variable = self.O2T).grid(column = 2, row = myrow, sticky=W, padx=5, pady=5)
    ttk.Label(f21, textvariable=self.O2T).grid(column=3, row=myrow, sticky=W, padx=5, pady=5)

    ttk.Label(f3, text=u"Target RLA Temperature in \N{DEGREE SIGN}C").grid(column = 1, row = 1, sticky = W, padx = 5, pady = 5)
    ttk.Scale(f3, orient=HORIZONTAL, length = 200, from_= 60, to= 85, command = self.onRLAScale, variable = self.RLATemp).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f3, textvariable=self.RLATemp).grid(column = 3, row = 1, sticky =W , padx = 5, pady = 5) 
    
    ttk.Label(f4, text=u"Target Heating Water Temperature in \N{DEGREE SIGN}C").grid(column=1, row=1, sticky=W, padx=5, pady=5)
    ttk.Scale(f4, orient=HORIZONTAL, length=200, from_=35, to=85, command = self.onHWScale, variable = self.hWTemp).grid(column = 2, row = 1, sticky=W, padx=5, pady=5)
    ttk.Label(f4, textvariable=self.hWTemp).grid(column=3, row=1, sticky=W, padx=5, pady=5)

    root.mainloop()

# ===========================================================================
# End of Class GUI
# ===========================================================================
GUI(True, True, True, True, True)