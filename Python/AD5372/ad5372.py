# -*- coding: utf-8 -*-

import os
import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, QSize, QRect
import requests
import numpy as np

dataFile = "data.dat"
# ipFile = "settings.txt"
IP = '192.168.32.154'


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.setConnect()
        self.loadData()

    def createChannels(self):
        self.channels = [QtWidgets.QDoubleSpinBox() for i in range(32)]
        gridLayout = QGridLayout()
        gridLayout.setVerticalSpacing(0)
        self.data = QGroupBox("Channels")
        self.data.setGeometry(10, 10, 950, 250)
        self.data.setContentsMargins(5, 5, 5, 5)
        for i in range(32):
            self.channels[i] = QDoubleSpinBox()
            # self.channels[i].setGeometry(1, 1, 70, 20)
            self.channels[i].setDecimals(3)
            self.channels[i].setMinimum(-10.0)
            self.channels[i].setMaximum(10.0)
            self.channels[i].setSingleStep(0.001)
            groupbox = QGroupBox()
            layout = QHBoxLayout()
            label = QLabel(str(i+1))
            # label.setContentsMargins(1, 1, 1, 1)
            layout.addWidget(label, 0)
            layout.addWidget(self.channels[i], 1)
            layout.setContentsMargins(2, 2, 1, 1)
            # groupbox.setContentsMargins(10, 10, 10, 10)
            groupbox.setLayout(layout)
            gridLayout.addWidget(groupbox, i//8, i % 8, 1, 1)
        self.data.setLayout(gridLayout)

    def createShutters(self):
        self.shutterFrame = QGroupBox("Shutters")
        self.shutterFrame.setGeometry(10, 10, 950, 40)
        self.shutterFrame.setContentsMargins(1, 1, 1, 1)
        buttons = ["Flip Mirror", "Protection", "399"]
        nums = [13, 14, 15]
        self.shutterArray = [QSpinBox() for i in range(len(buttons))]
        self.shutters = [QPushButton(buttons[i]) for i in range(len(buttons))]
        layout = QHBoxLayout()
        for i in range(len(buttons)):
            self.shutterArray[i].setRange(1, 32)
            self.shutterArray[i].setValue(nums[i])
            self.shutters[i].setStyleSheet('background-color: red')
            group = QGroupBox()
            layoutT = QHBoxLayout()
            layoutT.addWidget(self.shutterArray[i], 0)
            layoutT.addWidget(self.shutters[i], 1)
            group.setLayout(layoutT)
            layout.addWidget(group)
        self.shutterFrame.setLayout(layout)

    def createConfig(self):
        self.pre = QGroupBox("Settings")
        self.pre.setGeometry(10, 10, 950, 30)
        # self.pre.setContentsMargins(5, 5, 2, 2)
        self.IP = QLabel("IP")
        self.ipInput = QLineEdit(IP)
        # self.getIP()
        self.update = QPushButton('Update')
        self.load = QPushButton('Load')
        self.save = QPushButton("Save")
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(5, 5, 1, 1)
        hlayout.addWidget(self.IP)
        hlayout.addWidget(self.ipInput)
        hlayout.addWidget(self.update)
        hlayout.addWidget(self.load)
        hlayout.addWidget(self.save)
        self.pre.setLayout(hlayout)

    def setupUI(self):
        self.setFixedSize(1000, 370)
        self.createConfig()
        self.createChannels()
        self.createShutters()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pre)
        self.layout.addWidget(self.data)
        self.layout.addWidget(self.shutterFrame)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)
        self.setWindowTitle("AD5372")

# File IO is quite slow so that I drop it out
    # def getIP(self):
        # with open(ipFile, 'w+') as file:
        #     ip = file.readline()
        #     if not ip == '':
        #         self.ipInput.setText(ip)
        #     else:
        #         self.ipInput.setText('192.168.32.154')
        # self.ipInput.setText('192.168.32.154')

    # def setIP(self):
    #     with open(ipFile, 'w+') as file:
    #         file.write(self.ipInput.text())
        

    def setConnect(self):
        self.update.clicked.connect(self.reset)
        self.load.clicked.connect(self.loadData)
        self.save.clicked.connect(self.saveData)
        for i in range(32):
            self.channels[i].valueChanged.connect(self.dataUpdate(i))
        for i in range(len(self.shutters)):
            self.shutters[i].clicked.connect(self.switch(self.shutterArray[i].value() - 1))
            self.shutters[i].clicked.connect(self.updateShutter(i))

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def dataUpdate(self, channel):
        def update():
            self.set_voltage(channel, self.channels[channel].value())
        return update

    def loadData(self):
        exists = os.path.isfile(dataFile)
        if exists:
            data = np.loadtxt(dataFile)
            # print(data.size)
            if not data.size == 32:
                print("data length is wrong!!!")
                
                # errorDialog = QErrorMessage()
                # errorDialog.showMessage("The data file is wrong!!!")
                # raise SystemExit
            for i in range(32):
                self.channels[i].setValue(data[i])
                # print(data[i])
                # self.set_voltage(i, data[i])
        else:
            np.savetxt(dataFile, np.zeros(32))
            self.reset()


    def saveData(self):
        data = np.array([self.channels[i].value() for i in range(32)])
        np.savetxt(dataFile, data)

    def reset(self):
        data = 100000000
        try:
            with requests.Session() as s:
                req = s.get('http://' + self.ipInput.text() +
                            '/data/' + str(data))
        except requests.exceptions.RequestException as e:
            print(type(e))
        # self.setIP()
        
    def updateShutter(self, num):
        def update():
            if abs(self.channels[self.shutterArray[num].value() - 1].value()) < 0.01:
                self.shutters[num].setStyleSheet("background-color: red")
                # print("red")
            elif abs(self.channels[self.shutterArray[num].value() - 1].value() - 5) < 0.01:
                self.shutters[num].setStyleSheet("background-color: green")
                # print("green")
            else:
                self.shutters[num].setStyleSheet("background-color: gray")
                # print("gray")
        return update

    
    def switch(self, ch):
        def update():
            if abs(self.channels[ch].value()) < 0.01 :
                self.channels[ch].setValue(5.0)

            elif abs(self.channels[ch].value() - 5) < 0.01:
                self.channels[ch].setValue(0.0)
            else:
                self.channels[ch].setValue(0.0)
        return update

    def set_voltage(self, channel, Vout):
        VREF = 5.0
        offset_code = 0x2000
        WRITE_X = 3  # Write to DAC data (X) register
        channels = [0x08+i for i in range(32)]
        if (abs(Vout) > 10.0):
            print("Voltage over range!")
            return
        dac_code = int(Vout * 2**16 / (4 * VREF) + offset_code * 4)
        input_code = dac_code
        mode_code = WRITE_X
        data = input_code + (channels[channel]<<16) + (mode_code<<22)
        try:
            with requests.Session() as s:
                req = s.get('http://' + self.ipInput.text() + '/data/' + str(data))
        except requests.exceptions.RequestException as e:
            print(type(e))
            
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ui = App()
    ui.center()
    ui.show()
    sys.exit(app.exec_())
