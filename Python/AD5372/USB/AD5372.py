# -*- coding: utf-8 -*-

import os
import sys
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal,  QSize, QRect
import numpy as np
import time
import visa
# import re # Pattern match
# import serial
# import pyrpl
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
    '''This class is a reimplemented double spinbox with the same function as LabView number control'''
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

    def onValueChanged(self, func):
        self.editingFinished.connect(func)
        self.stepChanged.connect(func)
            
class DAC(QWidget):
    '''The class DAC is a basic family for AD5732, which can be used to implement a shutter switch, a DC supply with \pm 10V, and a combination of multiple channnels'''
    dataFile = "data.dat"
    channelOrder = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14, 17, 16, 19, 18, 21, 20, 23, 22, 25, 24, 27, 26, 29, 28, 31, 30]
    def __init__(self):
        super().__init__()
        self.createConfig()
        self.createChannels()
        self.create_compensation()
        self.createShutters()
        self.setupUI()
        self.setConnect()
        self.loadData(True)
        

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
            self.channels[i].setRange(-10.0, 10.0)
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
        names = ["Horizontal", "Vertical", "Axial", "DC1","DC2", "RFs"]
        self.compensationFrame = QGroupBox("Compensation Combinations: DC1 RF11 DC1-2 DC2-2")
        self.compensationFrame.setGeometry(10, 10, 950, 40)
        self.compensationFrame.setContentsMargins(1, 1, 1, 1)
        self.compensate = [[LVSpinBox(), QPushButton('GO')] for i in range(len(names))]
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
            ly.addWidget(self.compensate[i][1], 0)
            groupbox.setLayout(ly)
            layout.addWidget(groupbox)
        self.compensationFrame.setLayout(layout)

    def applyComp(self, num):
        if num == 0:
            for i in range(5):
                self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
                self.channels[10].setValue(self.channels[10].value() + self.compensate[num][0].value())
        elif num == 1:
            for i in range(5):
                self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
            self.channels[10].setValue(self.channels[10].value() - self.compensate[num][0].value())
        elif num == 2:
            for i in (1, 6):
                self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
        elif num == 3:
            for i in range(5):
                self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
        elif num == 4:
            for i in range(5,10):
                self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())
        elif num == 5:
            for i in (10, 11):
                self.channels[i].setValue(self.channels[i].value() + self.compensate[num][0].value())

    def createShutters(self):
        self.shutterFrame = QGroupBox("Shutters")
        self.shutterFrame.setGeometry(10, 10, 950, 40)
        # self.shutterFrame.setContentsMargins(1, 1, 1, 1)
        buttons = ["Flip Mirror", "Protection", "399", "935", "Unlock RF"]
        self.shutterArray = [13, 14, 15, 16, 17]
        # nums = [13, 14, 15, 16]
        # self.shutterArray = [QSpinBox() for i in range(len(buttons))]
        self.shutters = [QPushButton(buttons[i]) for i in range(len(buttons))]
        layout = QHBoxLayout()
        for i in range(len(buttons)):
            # make the button with a bool value
            self.shutters[i].setCheckable(True)
            self.shutters[i].setStyleSheet('background-color: red')
            myfont = QFont()
            myfont.setBold(True)
            self.shutters[i].setFont(myfont)
            # group = QGroupBox()
            # layoutT = QHBoxLayout()
            # layoutT.addWidget(QLabel(str(self.shutterArray[i])), 0)
            # layoutT.addWidget(self.shutters[i], 1)
            # group.setLayout(layoutT)
            layout.addWidget(self.shutters[i], 1)
        self.shutterFrame.setLayout(layout)

    def createConfig(self):
        self.pre = QGroupBox("Settings")
        self.pre.setGeometry(10, 10, 950, 30)
        # self.pre.setContentsMargins(5, 5, 2, 2)
        myfont = QFont()
        myfont.setBold(True)
        self.update = QPushButton('Update')
        self.update.setFont(myfont)
        self.load = QPushButton('Load')
        self.load.setFont(myfont)
        self.save = QPushButton("Save")
        self.save.setFont(myfont)
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(5, 5, 1, 1)
        hlayout.addWidget(self.update)
        hlayout.addWidget(self.load)
        hlayout.addWidget(self.save)
        self.pre.setLayout(hlayout)
    
    def setupUI(self):
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
            self.channels[i].valueChanged.connect(lambda chk, i=i: self.dataUpdate(i))
        for i in range(len(self.shutters)):
            self.shutters[i].toggled.connect(lambda chk, key=i: self.switch(key))
        for i in range(len(self.shutters)):
            self.channels[self.shutterArray[i]-1].valueChanged.connect(lambda chk, key=i: self.updateShutter(key))
        for i in range(len(self.compensate)):
            self.compensate[i][1].clicked.connect(lambda chk, key=i: self.applyComp(key))
    def set_shutter(self, num, state):
        """API for shutter"""
        if num < len(self.shutters):
            self.shutters[num].setChecked(state)
        else:
            print("Shutter index over range!")
            exit()


    def dataUpdate(self, channel):
        self.set_voltage(self.channelOrder[channel], self.channels[channel].value())

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
                if force_mode:
                    self.channels[i].setValue(data[i])
                    self.set_voltage(self.channelOrder[i], data[i])
                else:
                    if not data[i] == self.channels[i].value():
                        self.channels[i].setValue(data[i])
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
        if abs(self.channels[self.shutterArray[num] - 1].value()) < 0.1:
            self.shutters[num].setChecked(False)
        elif abs(self.channels[self.shutterArray[num] - 1].value() - 5) < 0.1:
            self.shutters[num].setChecked(True)
        else:
            if self.shutters[num].isChecked():
                self.shutters[num].setChecked(False)
            else:
                self.channels[self.shutterArray[num]-1].setValue(0)

    def switch(self, num):
        if self.shutters[num].isChecked():
            self.channels[self.shutterArray[num]-1].setValue(5)
            self.shutters[num].setStyleSheet("background-color: green")
        else:
            self.channels[self.shutterArray[num]-1].setValue(0.0)
            self.shutters[num].setStyleSheet("background-color: red")

    def set_voltage(self, channel, Vout):
        if (abs(Vout) > 10.00001):
            print("Voltage over range!")
            return
        dll.AD5372_DAC(channel, c_double(Vout))
        dll.AD5372_LDAC()

class RS:
    """Class used to send commands and acquire data from the Rohde & Schwarz SMA100A & SMB100A
    Signal Generator using PyVisa.
    """
    def __init__(self, ip):
        """Class constructor. Here the socket connection to the instrument is initialized. The
        argument required, a string, is the IP adress of the instrument."""
        rm = visa.ResourceManager("@py")
        sig_gen_ip = ip
        self.sig_gen_socket = rm.open_resource("TCPIP::" + sig_gen_ip + "::inst0::INSTR")

    def query(self, text):
        """Return the output of the query on text"""
        return self.sig_gen_socket.query(text)

    def write(self, text):
        """Sends a command to the instrument."""
        self.sig_gen_socket.write(text)

    def set_frequency(self, freq):
        """set the frequency value"""
        self.sig_gen_socket.write("SOURCE:FREQUENCY:CW " + str(freq))
        
    def set_amplitude(self, level):
        """set the amplitude value"""
        self.sig_gen_socket.write("SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE "+ str(level))

    def set_output(self, state):
        if state:
            self.sig_gen_socket.write("OUTPUT:STATE ON")
        else:
            self.sig_gen_socket.write("OUTPUT:STATE OFF")

    def read_frequency(self):
        return float(self.query("SOURCE:FREQUENCY:CW?"))
    
    def read_amplitude(self):
        return float(self.query("SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE?"))

    def read_status(self):
        # return int(self.query("SENSe:POWer:STATus?"))
        return int(self.query("OUTPUT:STATE?"))

    def set_lfo(self, freq):
        """set the low frequency output"""
        self.sig_gen_socket.write(":LFO:FREQ " + str(freq))
        self.sig_gen_socket.write(":LFO:FREQ:MODE FIXED")
        self.sig_gen_socket.write(":LFO:STAT ON")


    def set_am(self, stat):
        """set the amplitude modulation output"""
        if stat != 0 and stat != 1 and stat != "ON" and stat != "OFF":
            print('State should be 1, 0, \"ON\" or \"OFF\"')
            exit()
        self.sig_gen_socket.write(":AM:STAT " + str(stat))
        self.sig_gen_socket.write(":AM:SOUR INT")
        self.sig_gen_socket.write(":MOD:STAT ON")

    def set_fm(self, stat):
        """set the frequency modulation output"""
        if stat != 0 and stat != 1 and stat != "ON" and stat != "OFF":
            print('State should be 1, 0, \"ON\" or \"OFF\"')
            exit()
        self.sig_gen_socket.write(":FM:STAT " + str(stat))
        self.sig_gen_socket.write(":FM:SOUR INT")
        self.sig_gen_socket.write(":MOD:STAT ON")

    def set_clk_syn(self, state, freq):
        """ Set the Clock Synthesis"""
        self.sig_gen_socket.write("CSYN:STAT " + str(state))
        self.sig_gen_socket.write("CSYN:FREQ " + str(freq))

    def close_connection(self):
       """Close the socket connection to the instrument."""
       self.sig_gen_socket.close()

class RSCtrl(QGroupBox):
    def __init__(self, ip):
        super().__init__()
        self.device = RS(ip)
        self.freq = LVSpinBox()
        self.freq.setRange(0, 1000000000)
        self.freq.setDecimals(1)
        self.freq.setValue(self.device.read_frequency())
        self.amplitude = LVSpinBox()
        self.amplitude.setRange(-80, 20)
        self.amplitude.setDecimals(2)
        self.amplitude.setValue(self.device.read_amplitude())
        self.switch = QPushButton("OFF")
        myfont = QFont()
        myfont.setBold(True)
        self.switch.setFont(myfont)
        self.switch.setCheckable(True)
        if self.device.read_status():
            self.switch.setChecked(True)
            self.switch.setStyleSheet("background-color: green")
            self.switch.setText("ON")
        else:
            self.switch.setChecked(False)
            self.switch.setStyleSheet("background-color: red")
            self.switch.setText("OFF")
        self.set_connect()
        self.create_UI()

        
    def set_upper(self, upper):
        self.amplitude.setMaximum(upper)
    def create_UI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(QLabel("Freq"), 0)
        layout.addWidget(self.freq, 1)
        layout.addWidget(QLabel("Amp"), 0)
        layout.addWidget(self.amplitude, 1)
        layout.addWidget(self.switch, 1)
        self.setLayout(layout)
    def set_freq(self):
        self.device.set_frequency(self.freq.value())
    def set_amp(self):
        self.device.set_amplitude(self.amplitude.value())
    def set_output(self):
        self.device.set_output(self.switch.isChecked())
        if self.switch.isChecked():
            self.switch.setStyleSheet("background-color: green")
            self.switch.setText("ON")
        else:
            self.switch.setStyleSheet("background-color: red")
            self.switch.setText("OFF")

    def set_connect(self):
        self.freq.valueChanged.connect(self.set_freq)
        self.amplitude.valueChanged.connect(self.set_amp)
        self.switch.toggled.connect(self.set_output)


class Power:
    def __init__(self, COM, baudrate=9600):
        rm = visa.ResourceManager()
        self.device = rm.open_resource(COM, baud_rate=baudrate)
    def set_voltage(self, Vout):
        self.device.write('SOURCE:VOLTAGE ' + str(Vout))
    def set_current(self, Iout):
        self.device.write('SOURCE:CURRENT ' + str(Iout))
    def set_output(self, state):
        if state:
            self.device.write("OUTPUT ON")
        else:
            self.device.write("OUTPUT OFF")
    def read_voltage(self):
        return float(self.device.query("SOURCE:VOLTAGE?"))
    def read_current(self):
        return float(self.device.query("SOURCE:CURRENT?"))
    def read_status(self):
        '''The results returned are "ON\n" and "OFF\n"'''
        if self.device.query("OUTPUT?") == "ON\n":
            return True
        else:
            return False
    def close_connection(self):
       """Close the connection to the instrument."""
       self.device.close()
class PowerCtrl(QGroupBox):
    def __init__(self, COM, baudrate=9600):
        super().__init__()
        self.device = Power(COM, baudrate)
        self.voltage = LVSpinBox()
        self.voltage.setRange(0, 2)
        self.voltage.setSingleStep(0.01)
        self.voltage.setValue(self.device.read_voltage())
        self.current = LVSpinBox()
        self.current.setRange(0, 2.2)
        self.current.setSingleStep(0.01)
        self.current.setValue(self.device.read_current())
        self.switch = QPushButton("OFF")
        myfont = QFont()
        myfont.setBold(True)
        self.switch.setFont(myfont)
        self.switch.setCheckable(True)
        if self.device.read_status():
            self.switch.setChecked(True)
            self.switch.setStyleSheet("background-color: green")
            self.switch.setText("ON")
        else:
            self.switch.setChecked(False)
            self.switch.setStyleSheet("background-color: red")
            self.switch.setText("OFF")
        self.set_connect()
        self.create_UI()
        
    def create_UI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(QLabel("Vout"), 0)
        layout.addWidget(self.voltage, 1)
        layout.addWidget(QLabel("Iout"), 0)
        layout.addWidget(self.current, 1)
        layout.addWidget(self.switch, 1)
        self.setLayout(layout)
        
    def set_voltage(self):
        self.device.set_voltage(self.voltage.value())
    def set_current(self):
        self.device.set_current(self.current.value())
    def set_output(self):
        self.device.set_output(self.switch.isChecked())
        if self.switch.isChecked():
            self.switch.setStyleSheet("background-color: green")
            self.switch.setText("ON")
        else:
            self.switch.setStyleSheet("background-color: red")
            self.switch.setText("OFF")
    def set_switch(self, state):
        self.switch.setChecked(state)
    def set_connect(self):
        self.voltage.valueChanged.connect(self.set_voltage)
        self.current.valueChanged.connect(self.set_current)
        self.switch.toggled.connect(self.set_output)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.dac = DAC()
        self.rf = RSCtrl("192.168.32.145")
        self.rf.set_upper(3)
        self.rf.setTitle("RF")
        self.raman =RSCtrl("192.168.32.148")
        self.raman.set_upper(-4)
        self.raman.setTitle("Raman")
        self.oven = PowerCtrl("COM6")
        self.oven.setTitle("Oven")
        self.create_func()
        layout = QGridLayout()
        layout.addWidget(self.load_ion, 0, 0, 1, 1)
        layout.addWidget(self.monitor,0, 1, 1, 1)
        layout.addWidget(self.dac, 1, 0, 1, 3)
        layout.addWidget(self.rf, 2, 0, 1, 1)
        layout.addWidget(self.raman, 2, 1, 1, 1)
        layout.addWidget(self.oven, 2, 2, 1, 1)
        self.setLayout(layout)
        self.setWindowTitle("Control Panel")
    def create_func(self):
        # One button for loading ions with some combined shutter controls
        self.load_ion = QPushButton("Start Load Ion")
        myfont = QFont()
        myfont.setBold(True)
        self.load_ion.setFont(myfont)
        self.load_ion.setCheckable(True)
        self.load_ion.setChecked(False)
        self.load_ion.setStyleSheet("background-color: red")
        self.load_ion.toggled.connect(self.loading)
        self.monitor = QPushButton("Ion Status Monitor")
        self.monitor.setFont(myfont)
        self.monitor.setCheckable(True)
        self.monitor.setChecked(False)
        self.monitor.setStyleSheet("background-color: red")
        self.monitor.toggled.connect(self.ion_status_feedback)
    def loading(self):
        self.dac.set_shutter(2, self.load_ion.isChecked())
        self.oven.set_switch(self.load_ion.isChecked())
        if self.load_ion.isChecked():
            # Shine the protection beam when loading ions, but won't shut it down when completing loading
            self.dac.set_shutter(1, True)
            self.load_ion.setText("Loading Ion")
            self.load_ion.setStyleSheet("background-color: green")
        else:
            self.load_ion.setText("Start Load Ion")
            self.load_ion.setStyleSheet("background-color: red")
    def ion_status_feedback(self):
        pass
    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyle('Fusion')
    ui = Window()
    ui.center()
    ui.show()
    sys.exit(app.exec_())
