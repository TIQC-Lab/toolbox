# -*- coding: utf-8 -*-

import os
import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal,  QSize, QRect
import numpy as np
import time
import re # Pattern match
import serial

#gacutil.exe /i CyUSB.dll
from ctypes import *
dll = cdll.LoadLibrary('AD5372.dll')
dll.AD5372_Init()
#import clr
#sys.path.append(os.path.dirname(os.path.realpath(__file__)))
#clr.AddReference('AD5372')
#from ADI import AD5372
#AD5372.Init()
#AD5372.DAC(0, 1)
#AD5372.LDAC()

class LVSpinBox(QDoubleSpinBox):
    stepChanged = pyqtSignal()

    def stepBy(self, step):
        value = self.value()
        point = str(self.text()).find('.')
        if point < 0:
            point = len(str(self.text()))
        digit = point - self.lineEdit().cursorPosition()
        if digit < 0:
            digit += 1
        self.setValue(value + step*(10**digit))
        if self.value() != value:
            self.stepChanged.emit()

    def onValueChanged(self,func):
        self.editingFinished.connect(func)
        self.stepChanged.connect(func)
            
class DAC(QWidget):
    dataFile = "data.dat"
    channelOrder = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17, 16, 19, 18, 21, 20, 23, 22, 25, 24, 27, 26, 29, 28, 31, 30]
    def __init__(self):
        super().__init__()
        self.createConfig()
        self.createChannels()
        self.create_compensation()
        self.createShutters()
        self.setupUI()
        self.loadData(True)
        self.setConnect()

    def createChannels(self):
        self.channels = [None]*32
        gridLayout = QGridLayout()
        gridLayout.setVerticalSpacing(0)
        self.data = QGroupBox("Channels(DC1:1-5, DC2:6-10, RF1:11, RF2:12,Shutters:13-16)")
        self.data.setGeometry(10, 10, 950, 250)
        self.data.setContentsMargins(5, 5, 5, 5)
        # Data entries
        for i in range(32):
            self.channels[i] = LVSpinBox()
            # self.channels[i].setGeometry(1, 1, 70, 20)
            self.channels[i].setDecimals(4)
            # self.channels[i].setMinimum(-10.0)
            # self.channels[i].setMaximum(10.0)
            self.channels[i].setRange(-10.0, 10.0)
            self.channels[i].setSingleStep(0.0001)
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
    def create_compensation(self):
        '''This part is used to compensate the DC null to RF null'''
        names = ["Horizontal", "Vertical", "Axial", "DCs", "RFs"]
        self.compensationFrame = QGroupBox("Compensation Combinations")
        self.compensationFrame.setGeometry(10, 10, 950, 40)
        self.compensationFrame.setContentsMargins(1, 1, 1, 1)
        self.compensate = [[LVSpinBox(), QPushButton('GO')], [LVSpinBox(), QPushButton('GO')], [LVSpinBox(), QPushButton('GO')], [LVSpinBox(), QPushButton('GO')], [LVSpinBox(), QPushButton('GO')]]
        layout = QHBoxLayout()
        for i in range(len(self.compensate)):
            groupbox = QGroupBox()
            # groupbox.setContentsMargins(1, 1, 1, 1)
            ly = QHBoxLayout()
            self.compensate[i][0].setRange(-1.0, 1.0)
            self.compensate[i][0].setDecimals(4)
            self.compensate[i][0].setSingleStep(0.0001)
            ly.addWidget(QLabel(names[i]))
            ly.addWidget(self.compensate[i][0], 1)
            # self.compensate[i][1].resize(20, 30)
            # self.compensate[i][1].setMinimumWidth(1)
            ly.addWidget(self.compensate[i][1], 0)
            groupbox.setLayout(ly)
            layout.addWidget(groupbox)
        self.compensationFrame.setLayout(layout)

    def applyComp(self, num):
        def update():
            if num == 0:
                for i in range(5):
                    self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
                self.channels[10].setValue(self.channels[10].value() + self.compensate[num][0].value())
            elif num == 1:
                for i in range(5):
                    self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value() )
                self.channels[11].setValue(self.channels[11].value() + self.compensate[num][0].value())
            elif num == 2:
                for i in (1, 6):
                    self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
            elif num == 3:
                for i in range(10):
                    self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
            elif num == 4:
                for i in (10, 11):
                    self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
        return update

    def createShutters(self):
        self.shutterFrame = QGroupBox("Shutters")
        self.shutterFrame.setGeometry(10, 10, 950, 40)
        self.shutterFrame.setContentsMargins(1, 1, 1, 1)
        buttons = ["Flip Mirror", "Protection", "399", "935"]
        nums = [13, 14, 15, 16]
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
        self.update = QPushButton('Update')
        self.load = QPushButton('Load')
        self.save = QPushButton("Save")
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(5, 5, 1, 1)
        hlayout.addWidget(self.update)
        hlayout.addWidget(self.load)
        hlayout.addWidget(self.save)
        self.pre.setLayout(hlayout)
    



    def setupUI(self):
        # self.setFixedSize(1000, 370)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.addWidget(self.pre)
        self.layout.addWidget(self.data)
        self.layout.addWidget(self.compensationFrame)
        self.layout.addWidget(self.shutterFrame)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)
        self.setWindowTitle("AD5372")

        

    def setConnect(self):
        self.update.clicked.connect(self.reset)
        self.load.clicked.connect(self.loadData)
        self.save.clicked.connect(self.saveData)
        for i in range(32):
            self.channels[i].valueChanged.connect(self.dataUpdate(i))
        for i in range(len(self.shutters)):
            self.shutters[i].clicked.connect(self.switch(self.shutterArray[i].value() - 1))
            self.shutters[i].clicked.connect(self.updateShutter(i))
        for i in range(len(self.compensate)):
            self.compensate[i][1].clicked.connect(self.applyComp(i))

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def dataUpdate(self, channel):
        def update():
            self.set_voltage(self.channelOrder[channel], self.channels[channel].value())
        return update

    def loadData(self, force_mode=False):
        """
            This function is used to load data from local data file, while the argument 'force_mode' is used to specify if all data will sent to the wifi server, otherwise we only change those whose value is different from the one imported from data file, which will generate a signal for the slot.
        """
        exists = os.path.isfile(self.dataFile)
        if exists:
            data = np.loadtxt(self.dataFile)
            # print(data.size)
            if not data.size == 32:
                print("data length is wrong!!!")
            for i in range(32):
                if not data[i] == self.channels[i].value():
                    self.channels[i].setValue(data[i])
                if force_mode:
                    self.set_voltage(self.channelOrder[i], data[i])
        else:
            np.savetxt(self.dataFile, np.zeros(32))
            self.reset()


    def saveData(self):
        data = np.array([self.channels[i].value() for i in range(32)])
        np.savetxt(self.dataFile, data)

    def reset(self):
        for i in range(32):
            self.channels[i].setValue(0.0)
        dll.AD5372_Reset()
        
    def updateShutter(self, num):
        def update():
            if abs(self.channels[self.shutterArray[num].value() - 1].value()) < 0.01:
                self.shutters[num].setStyleSheet("background-color: red")
            elif abs(self.channels[self.shutterArray[num].value() - 1].value() - 5) < 0.01:
                self.shutters[num].setStyleSheet("background-color: green")
            else:
                self.shutters[num].setStyleSheet("background-color: gray")
        return update

    
    def switch(self, ch):
        def update():
            if abs(self.channels[ch].value()) < 0.01:
                self.channels[ch].setValue(5)
            elif abs(self.channels[ch].value() - 5) < 0.01:
                self.channels[ch].setValue(0.0)
            else:
                self.channels[ch].setValue(0.0)
        return update

    def set_voltage(self, channel, Vout):
        if (abs(Vout) > 10.00001):
            print("Voltage over range!")
            return
        dll.AD5372_DAC(channel, c_double(Vout))
        dll.AD5372_LDAC()

class Supply(QWidget):
    '''This class is designed to implement a basic operation of power supply using pyqt5'''
    def __init__(self, name = "Supply", COM = "COM6", baudrate = 9600):
        self.name = name
        self.COM = COM
        self.baudrate = baudrate
        self.agent = serial.Serial()
        self.createUI()
        

# spinbox.lineEdit().setReadOnly(True)
    def createUI(self):
        self.supplies = QGroupBox("Supplies")
        self.supplies.setGeometry(5, 5, 950, 50)
        self.switch = QPushButton("ON/OFF")
        self.switch.setStyleSheet("background-color: red")
        layout = QGridLayout()
        layout.setContentsMargins(5, 5, 1, 1)

        # for i in range(len(sources)):
        #     supply = QGroupBox()
        #     supply.setGeometry(5, 5, 300, 50)
        #     ly = QGridLayout()
        #     ly.setContentsMargins(1, 1, 1, 1)
        #     ly.addWidget(QLabel(sources[i]), 0, 0, 1, 2)
        #     switch = QPushButton("Switch")
        #     ly.addWidget(switch, 0, 2, 1, 1)

    def connect(self):
        '''Connect to the serial port and flush all buffer'''
        try:
            self.agent.open()
            self.agent.write(b'SYSTEM:REMOTE')
            time.sleep(0.01)
            self.agent.write(b'OUTPUT OFF')
            self.agent.flush()
        except serial.SerialException as e:
            print(type(e), "Check your serial configuration of " + self.name)

    def query(self):
        '''query if the output is on or off when the port is already opened, return 0 for off and 1 for on'''
        if not self.agent.is_open:
            self.connect()
        self.agent.write(b"OUTPUT?")
        time.sleep(0.1)
        status = int(self.agent.read_until())
        return status

    def setVoltage(self, Vout):
        '''set the output voltage of the power supply'''
        if not self.agent.is_open:
            self.connect()
        self.agent.write(('SOURCE:VOLTAGE ' + str(Vout)).encode())
    def setCurrent(self, Iout):
        '''set the output current of the power supply'''
        if not self.agent.is_open:
            self.connect()
        self.agent.write(('SOURCE:CURRENT ' + str(Iout)).encode())

    def supplySwitch(self):
        '''swith the power supply and update the background color of the switch button'''
        if not self.agent.is_open:
            self.connect()
        if self.query() == 0:
            self.agent.write(b"OUTPUT ON")
            self.switch.setStyleSheet('background-color: green')
        else:
            self.agent.write(b"OUTPUT OFF")
            self.switch.setStyleSheet('background-color: red')
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ui = DAC()
    ui.center()
    ui.show()
    sys.exit(app.exec_())
