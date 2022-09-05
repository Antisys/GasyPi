import time
import matplotlib
matplotlib.use('TkAgg') # do this before importing pylab
import matplotlib.pyplot as plt
import random

fig = plt.figure()
ax1 = fig.add_subplot(5, 1, 1)
ax2 = fig.add_subplot(5, 1, 2)
ax3 = fig.add_subplot(5, 1, 3)
ax4 = fig.add_subplot(5, 1, 4)
ax5 = fig.add_subplot(5, 1, 5)

ax1.set_ylabel('BK in C')
ax1.set_ylim(500, 1000)

ax2.set_ylabel('AGT in C')
ax2.set_ylim(50, 250)

ax3.set_ylabel('Prim in %')
ax3.set_ylim(0, 100)

ax4.set_ylabel('O2 in %')
ax4.set_ylim(0, 10)

ax5.set_ylabel('Sek in %')
ax5.set_ylim(0, 100)
 


y1 = []
y2 = []
y3 = []
y4 = []
y5 = []

def animate():

    while(1):
        y1.append(random.random() * 1000 + 500)
        y2.append(random.random() * 150)
        y3.append(random.random() * 100)
        y4.append(random.random() * 10)
        y5.append(random.random() * 100)

        x = range(len(y1))

        line1, = ax1.plot(y1)
        line1.set_ydata(y1)
        line2, = ax2.plot(y2)
        line2.set_ydata(y2)
        line3, = ax3.plot(y3)
        line3.set_ydata(y3)
        line4, = ax4.plot(y4)
        line4.set_ydata(y4)
        line5, = ax5.plot(y5)
        line5.set_ydata(y5)

        fig.canvas.draw()
        time.sleep(1)

win = fig.canvas.manager.window
fig.canvas.manager.window.after(1000, animate)
plt.show()

