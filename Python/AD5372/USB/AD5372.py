# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
import numpy as np
import time
import visa
from TopticaLaser import TopticaLaser as Laser
# import qdarkstyle
# import re # Pattern match
# import serial
# import pyrpl
# gacutil.exe /i CyUSB.dll
from ctypes import *

#import clr
# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
# clr.AddReference('AD5372')
#from ADI import AD5372
# AD5372.Init()
#AD5372.DAC(0, 1)
# AD5372.LDAC()
myfont = QFont()
myfont.setBold(True)
# Open a resource manager of visa
rm = visa.ResourceManager("@py")


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


class DAC(QGroupBox):
    '''The class DAC is a basic family for AD5732, which can be used to implement a shutter switch, a DC supply with \pm 10V, and a combination of multiple channnels'''
    dataFile = "data.dat"
    channelOrder = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15,
                    14, 17, 16, 19, 18, 21, 20, 23, 22, 25, 24, 27, 26, 29, 28, 31, 30]
    dll = cdll.LoadLibrary('AD5372.dll')
    dataNum = 32

    def __init__(self):
        super().__init__()
        self.dll.AD5372_Open()
        self.createConfig()
        self.createChannels()
        self.create_compensation()
        self.createShutters()
        self.setupUI()
        self.setConnect()
        self.loadData(True)

    def createChannels(self):
        self.channels = [LVSpinBox()]*self.dataNum
        gridLayout = QGridLayout()
        self.data = QGroupBox(
            "Channels(DC1:1-5, DC2:6-10, RF1:11, RF2:12,Shutters:13-16)")
        self.data.setContentsMargins(1, 1, 1, 1)
        # Data entries
        for i in range(self.dataNum):
            self.channels[i].setDecimals(4)
            self.channels[i].setRange(-10.0, 10.0)
            groupbox = QGroupBox()
            layout = QHBoxLayout()
            label = QLabel(str(i+1))
            layout.addWidget(label, 0)
            layout.addWidget(self.channels[i], 1)
            layout.setContentsMargins(1, 1, 1, 1)
            groupbox.setLayout(layout)
            gridLayout.addWidget(groupbox, i//8, i % 8, 1, 1)
        # vspacer = QSpacerItem(QSizePolicy.Minimum, QSizePolicy.Expanding)
        # gridLayout.addItem(vspacer, 3, 0, 1, -1)
        # hspacer = QSpacerItem(QSizePolicy.Expanding, QSizePolicy.Minimum)
        # gridLayout.addItem(hspacer, 0, 7, -1, 1)
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setSpacing(0)
        gridLayout.setVerticalSpacing(0)
        self.data.setLayout(gridLayout)

    def create_compensation(self):
        '''This part is used to compensate the DC null to RF null'''
        names = ["Horizontal", "Vertical", "Axial", "DC1", "DC2", "RFs", "All"]
        self.compensationFrame = QGroupBox(
            "Compensation Combinations: DC1 RF11 DC1-2 DC2-2")
        self.compensationFrame.setContentsMargins(1, 1, 1, 1)
        self.compensate = [[LVSpinBox(), QPushButton('GO')]]*self.dataNum
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.ratio = LVSpinBox()
        self.ratio.setDecimals(2)
        self.ratio.setRange(0, 50)
        self.ratio.setValue(1)
        groupbox = QGroupBox()
        ly = QHBoxLayout()
        ly.setContentsMargins(0, 0, 0, 0)
        ly.addWidget(QLabel("DC1:RF1= "))
        ly.addWidget(self.ratio, 1)
        groupbox.setLayout(ly)
        layout.addWidget(groupbox, 0, 0, 1, 1)
        for i in range(len(self.compensate)):
            groupbox = QGroupBox()
            ly = QHBoxLayout()
            self.compensate[i][0].setRange(-1.0, 1.0)
            self.compensate[i][0].setDecimals(4)
            self.compensate[i][0].setSingleStep(0.0001)
            label = QLabel(names[i])
            label.setFont(myfont)
            ly.addWidget(label)
            ly.addWidget(self.compensate[i][0], 1)
            ly.addWidget(self.compensate[i][1], 1)
            ly.setContentsMargins(0, 0, 0, 0)
            groupbox.setLayout(ly)
            layout.addWidget(groupbox, (i+1)//4, (i+1) % 4, 1, 1)
        self.compensationFrame.setLayout(layout)

    def applyComp(self, num):
        if num == 0:
            for i in range(5):
                self.channels[i].setValue(
                    self.channels[i].value() + self.compensate[num][0].value())
            self.channels[10].setValue(self.channels[10].value(
            ) + self.ratio.value()*self.compensate[num][0].value())
        elif num == 1:
            for i in range(5):
                self.channels[i].setValue(
                    self.channels[i].value() + self.compensate[num][0].value())
            self.channels[10].setValue(self.channels[10].value(
            ) - self.ratio.value()*self.compensate[num][0].value())
        elif num == 2:
            for i in (0, 5):
                self.channels[i].setValue(
                    self.channels[i].value() + self.compensate[num][0].value())
        elif num == 3:
            for i in range(5):
                self.channels[i].setValue(
                    self.channels[i].value() + self.compensate[num][0].value())
        elif num == 4:
            for i in range(5, 10):
                self.channels[i].setValue(
                    self.channels[i].value() + self.compensate[num][0].value())
        elif num == 5:
            for i in (10, 11):
                self.channels[i].setValue(
                    self.channels[i].value() + self.compensate[num][0].value())
        elif num == 6:
            for i in range(12):
                self.channels[i].setValue(
                    self.channels[i].value() + self.compensate[num][0].value())

    def createShutters(self):
        self.shutterFrame = QGroupBox("Shutters")
        buttons = ["PMT", "Protection", "399", "935", "Unlock RF", "Trap RF"]
        self.shutterArray = [13, 14, 15, 16, 17, 19]
        self.shutters = [QPushButton(buttons[i]) for i in range(len(buttons))]
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        for i in range(len(buttons)):
            # make the button with a bool value
            self.shutters[i].setCheckable(True)
            self.shutters[i].setStyleSheet('background-color: red')
            self.shutters[i].setFont(myfont)
            self.channels[self.shutterArray[i]-1].setReadOnly(True)
            layout.addWidget(self.shutters[i], 1)
        self.shutterFrame.setLayout(layout)

    def createConfig(self):
        self.pre = QGroupBox("AD5372")
        self.update = QPushButton('Reset Board')
        self.update.setFont(myfont)
        self.load = QPushButton('Load Data')
        self.load.setFont(myfont)
        self.save = QPushButton("Save Data")
        self.save.setFont(myfont)
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.addWidget(self.update)
        hlayout.addWidget(self.load)
        hlayout.addWidget(self.save)
        self.pre.setLayout(hlayout)

    def setupUI(self):
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pre)
        self.layout.addWidget(self.data)
        self.layout.addWidget(self.compensationFrame)
        self.layout.addWidget(self.shutterFrame)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setContentsMargins(1, 1, 1, 1)
        # self.setWindowTitle("AD5372")

    def setConnect(self):
        self.update.clicked.connect(self.reset)
        self.load.clicked.connect(self.loadData)
        self.save.clicked.connect(self.saveData)
        for i in range(self.dataNum):
            self.channels[i].valueChanged.connect(
                lambda chk, i=i: self.dataUpdate(i))
        for i in range(len(self.shutters)):
            self.shutters[i].toggled.connect(
                lambda chk, key=i: self.switch(key))
        for i in range(len(self.compensate)):
            self.compensate[i][1].clicked.connect(
                lambda chk, key=i: self.applyComp(key))

    def set_shutter(self, num, state):
        """API for shutter"""
        if num < len(self.shutters):
            self.shutters[num].setChecked(state)
        else:
            print("Shutter index over range!")
            exit()

    def dataUpdate(self, channel):
        self.set_voltage(
            self.channelOrder[channel], self.channels[channel].value())

    def loadData(self, force_mode=False):
        """
            This function is used to load data from local data file, while the argument 'force_mode' is used to specify if all data will sent to the wifi server, otherwise we only change those whose value is different from the one imported from data file, which will generate a signal for the slot.
        """
        exists = os.path.isfile(self.dataFile)
        if exists:
            data = np.loadtxt(self.dataFile)
            if not data.size == self.dataNum:
                print("data length is wrong!!!")
            for i in range(self.dataNum):
                self.channels[i].setValue(data[i])
                if force_mode:
                    self.set_voltage(self.channelOrder[i], data[i])
            for i in range(len(self.shutters)):
                self.updateShutter(i)
        else:
            np.savetxt(self.dataFile, np.zeros(self.dataNum))
            self.reset()

    def saveData(self):
        data = np.array([self.channels[i].value() for i in range(self.dataNum)])
        np.savetxt(self.dataFile, data)

    def reset(self):
        for i in range(self.dataNum):
            self.channels[i].setValue(0.0)
        self.dll.AD5372_Init()
        self.dll.AD5372_Reset()

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
        self.dll.AD5372_DAC(channel, c_double(Vout))
        self.dll.AD5372_LDAC()



class RS:
    """Class used to send commands and acquire data from the Rohde & Schwarz SMA100A & SMB100A
    Signal Generator using PyVisa. Frequency is in unit MHz.
    """

    def __init__(self, ip):
        """Class constructor. Here the socket connection to the instrument is initialized. The
        argument required, a string, is the IP adress of the instrument."""
        # rm = visa.ResourceManager("@py")
        self.sig_gen_ip = ip
        self.sig_gen_socket = rm.open_resource(
            "TCPIP::" + ip + "::inst0::INSTR")

    def query(self, text):
        """Return the output of the query on text"""
        return self.sig_gen_socket.query(text)

    def write(self, text):
        """Sends a command to the instrument."""
        self.sig_gen_socket.write(text)

    def set_frequency(self, freq):
        """set the frequency value"""
        self.sig_gen_socket.write("SOURCE:FREQUENCY:CW " + str(freq*10**6))

    def set_amplitude(self, level):
        """set the amplitude value"""
        self.sig_gen_socket.write(
            "SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE " + str(level))

    def set_output(self, state):
        if state:
            self.sig_gen_socket.write("OUTPUT:STATE ON")
        else:
            self.sig_gen_socket.write("OUTPUT:STATE OFF")

    def read_frequency(self):
        return (float(self.query("SOURCE:FREQUENCY:CW?"))/10**6)

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

    def __del__(self):
        self.sig_gen_socket.close()


class RSCtrl(QGroupBox):
    def __init__(self, ip):
        super().__init__()
        self.device = RS(ip)
        self.freq = LVSpinBox()
        self.freq.setRange(0, 1000)
        self.freq.setDecimals(6)
        freq = self.device.read_frequency()
        if freq > 1000:
            self.freq.setRange(0, 12750)
        self.freq.setValue(freq)
        self.amplitude = LVSpinBox()
        self.amplitude.setRange(-80, 20)
        self.amplitude.setDecimals(2)
        self.amplitude.setValue(self.device.read_amplitude())
        self.switch = QPushButton("OFF")
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

    def setRange(self, low=-80, upper=20):
        self.amplitude.setRange(low, upper)

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
        # rm = visa.ResourceManager("@py")
        # print(rm.list_resources())
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

    def __del__(self):
        self.device.close()


class PowerCtrl(QGroupBox):
    def __init__(self, COM, baudrate=9600):
        super().__init__()
        self.device = Power(COM, baudrate)
        self.voltage = LVSpinBox()
        self.voltage.setRange(0, 2)
        self.voltage.setDecimals(2)
        self.voltage.setValue(self.device.read_voltage())
        self.current = LVSpinBox()
        self.current.setRange(0, 2.2)
        self.current.setDecimals(2)
        self.current.setValue(self.device.read_current())
        self.switch = QPushButton("OFF")
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


class AD5791:
    """This class is designed to control AD5791, and I have set the LDAC at the Low level which enable Synchronous DAC Update 
 at the rising edge of SYNC."""

    def __init__(self, ser="BSPT002144", dll="usb2uis.dll"):
        self.VREF = 10.0
        self.serial_num = ser
        self.dll = cdll.LoadLibrary(dll)
        # Close the connections if already exist
        self.dll.USBIO_CloseDeviceByNumber(ser)
        self.device_num = self.dll.USBIO_OpenDeviceByNumber(ser)
        if self.device_num == 0xFF:
            print("No USB2UIS can be connected!")
            exit()
        self.SPI_Init()
        self.device_start()

    def SPI_Init(self, frequency=8, mode=1, timeout_read=100, timeout_write=100):
        """SPI settings, frequency upto 8 selections, representing 200kHz 400kHz, 600kHz, 800kHz, 1MHz, 2MHz, 4MHz, 6MHz and 12MHz. Mode is specified to the clock signal, and the timeout is used to specify the timeout of read and write, occupying 16-bit data respectively"""
        self.dll.USBIO_SPISetConfig(
            self.device_num, (mode << 4)+frequency, (timeout_write << 16)+timeout_read)

    def data(self, Vout):
        return int((Vout+self.VREF)*(2**20-1)/2/self.VREF)

    def device_start(self):
        """Set the control register to enable the dac into a normal operation mode and offset code style"""
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x200012).to_bytes(3, byteorder="big"), 3)

    def set_voltage(self, Vout):
        """The Vout set to the DAC should exceed \pm 10V"""
        if abs(Vout) > 10.0000000001:
            print("Voltage over range!")
        else:
            self.dll.USBIO_SPIWrite(self.device_num, None, 0, ((
                0x01 << 20) + self.data(Vout)).to_bytes(3, byteorder="big"), 3)

    def read_voltage(self):
        out = b'\x00'*3
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x900000).to_bytes(3, byteorder="big"), 3)
        self.dll.USBIO_SPIRead(self.device_num, None, 0, out, 3)
        data = int.from_bytes(out, byteorder="big")
        data = data & 0x0FFFFF
        return data*2*self.VREF/(2**20 - 1) - self.VREF

    def LDAC(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x400001).to_bytes(3, byteorder="big"), 3)

    def clear(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x400002).to_bytes(3, byteorder="big"), 3)

    def reset(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x400004).to_bytes(3, byteorder="big"), 3)

    def disable_output(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x20001E).to_bytes(3, byteorder="big"), 3)

    def __del__(self):
        self.dll.USBIO_CloseDeviceByNumber(self.serial_num)


class AD5791Ctrl(QGroupBox):
    def __init__(self, ser="BSPT002144", dll="usb2uis.dll"):
        super().__init__()
        self.device = AD5791(ser, dll)
        self.value = LVSpinBox()
        self.value.setDecimals(5)
        self.value.setValue(self.device.read_voltage())
        self.switch = QPushButton("ON")
        self.switch.setCheckable(True)
        self.switch.setChecked(True)
        self.switch.setStyleSheet("background-color: green")
        self.switch.setFont(myfont)
        self.reset = QPushButton("Reset")
        self.reset.setFont(myfont)
        self.level = QPushButton("High")
        self.level.setCheckable(True)
        self.level.setChecked(True)
        self.level.setFont(myfont)
        self.level.setStyleSheet("background-color: green")
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Vref"), 0)
        layout.addWidget(self.value, 1)
        layout.addWidget(self.level, 1)
        layout.addWidget(self.switch, 1)
        layout.addWidget(self.reset, 1)
        self.setLayout(layout)
        self.set_connect()
        # self.level.setChecked(False)

    def setRange(self, low=0.5, upper=2.0):
        self.value.setRange(low, upper)

    def set_connect(self):
        self.value.valueChanged.connect(self.set_voltage)
        self.switch.toggled.connect(self.set_switch)
        self.reset.clicked.connect(self.resetAll)
        self.level.toggled.connect(self.changeLevel)

    def set_voltage(self):
        self.device.set_voltage(self.value.value())

    def set_switch(self):
        if self.switch.isChecked():
            self.device.device_start()
            self.level.setChecked(False)
            self.switch.setStyleSheet("background-color: green")
            self.switch.setText("ON")
        else:
            self.device.disable_output()
            self.switch.setStyleSheet("background-color: red")
            self.switch.setText("OFF")

    def resetAll(self):
        self.device.SPI_Init()
        self.device.reset()
        self.switch.setChecked(False)
        self.value.setValue(self.device.read_voltage())

    def changeLevel(self):
        if self.level.isChecked():
            self.value.setValue(1.5)
            self.level.setStyleSheet("background-color: green")
            self.level.setText("High")
        else:
            self.value.setValue(0.7)
            self.level.setStyleSheet("background-color: red")
            self.level.setText("Low")

    def setHighLevel(self, state):
        if state:
            self.level.setChecked(True)
        else:
            self.level.setChecked(False)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("control-panel.png"))
        self.setWindowIconText("Control Panel")
        self.dac = DAC()
        self.rf = RSCtrl("192.168.32.145")
        self.rf.setRange(-80, -2)
        self.rf.setTitle("RF")
        self.raman = RSCtrl("192.168.32.148")
        self.raman.setRange(-80, -11.5)
        self.raman.setTitle("Raman 173")
        self.raman_pll = RSCtrl("192.168.32.38")
        self.raman_pll.setRange(-80, 10.5)
        self.raman_pll.setTitle("Raman 230")
        self.microwave = RSCtrl("192.168.32.103")
        self.microwave.setRange(-80, 10)
        self.microwave.setTitle("Microwave")
        self.oven = PowerCtrl("ASRLCOM6::INSTR")
        self.oven.setTitle("Oven")
        self.vref = AD5791Ctrl()
        self.vref.setRange(0.5, 2.0)
        self.vref.setTitle("RF Reference")
        self.create_func()
        layout = QGridLayout()
        layout.addWidget(self.load_ion, 0, 0, 1, 1)
        layout.addWidget(self.monitor, 0, 1, 1, 1)
        layout.addWidget(self.laser, 0, 2, 1, 1)
        layout.addWidget(self.dac, 1, 0, 1, 3)
        layout.addWidget(self.rf, 2, 0, 1, 1)
        layout.addWidget(self.raman, 2, 1, 1, 1)
        layout.addWidget(self.raman_pll, 2, 2, 1, 1)
        layout.addWidget(self.vref, 3, 0, 1, 1)
        layout.addWidget(self.oven, 3, 1, 1, 1)
        layout.addWidget(self.microwave, 3, 2, 1, 1)
        self.setContentsMargins(1, 1, 1, 1)
        vspacer = QSpacerItem(QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(vspacer, 3, 0, 1, -1)
        hspacer = QSpacerItem(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(hspacer, 0, 2, -1, 1)
        self.setLayout(layout)
        self.setWindowTitle("Control Panel")

    def create_func(self):
        # One button for loading ions with some combined shutter controls
        self.load_ion = QPushButton("Start Load Ions")
        self.load_ion.setFont(myfont)
        self.load_ion.setCheckable(True)
        self.load_ion.toggled.connect(self.loading)
        self.load_ion.setChecked(False)
        self.load_ion.setStyleSheet("background-color: red")
        self.monitor = QPushButton("Drive Ions Back")
        self.monitor.setFont(myfont)
        self.monitor.setCheckable(True)
        self.monitor.setChecked(False)
        self.monitor.setStyleSheet("background-color: red")
        self.monitor.toggled.connect(self.ion_status_feedback)
        self.laser = QPushButton("Laser OFF")
        self.laser.setCheckable(True)
        self.laser.setFont(myfont)
        self.laser.setStyleSheet("background-color: red")
        self.laser.toggled.connect(self.laser_switch)

    def laser_switch(self):
        # main lasers to control
        laser_ips = ['192.168.32.5', '192.168.32.7', '192.168.32.116']
        if self.laser.isChecked():
            for ip in laser_ips:
                laser = Laser(ip)
                laser.enable_emission(True)
            self.laser.setStyleSheet("background-color: green")
            self.laser.setText("Laser ON")
        else:
            laser = Laser(laser_ips[2])
            laser.enable_emission(False)
            # other lasers share the same 935
            lasers_935 = ['192.168.32.4', '192.168.32.101']
            flag_935 = True
            for ip in lasers_935:
                laser = Laser(ip)
                status = laser.get_status()
                if status:
                    flag_935 = False
                    break
            if flag_935:
                laser = Laser(laser_ips[1])
                laser.enable_emission(False) 
                # other lasers share the same 399
                lasers_399 = ['192.168.32.152', '192.168.32.122']
                flag_399 = True
                for ip in lasers_399:
                    laser = Laser(ip)
                    status = laser.get_status()
                    if status:
                        flag_399 = False
                        break
                if flag_399:
                    laser = Laser(laser_ips[0])
                    laser.enable_emission(False)
            self.laser.setStyleSheet("background-color: red")
            self.laser.setText("Laser OFF")

    def loading(self):
        if self.load_ion.isChecked():
            self.dac.set_shutter(2, True)
            self.oven.set_switch(True)
            # Shine the protection beam when loading ions, but won't shut it down when completing loading
            # One way to set the low RF
            # self.dac.set_shutter(4, True) # Turn the RF to the low level
            # The other way to set low RF
            self.dac.set_shutter(4, False)
            self.vref.setHighLevel(False)
            self.dac.set_shutter(1, True)  # Turn on the protection beam
            self.dac.set_shutter(3, True)  # keep 935 on just in case
            self.load_ion.setText("Loading Ions")
            self.load_ion.setStyleSheet("background-color: green")
        else:
            self.dac.set_shutter(2, False)
            self.oven.set_switch(False)
            self.load_ion.setText("Start Load Ions")
            self.load_ion.setStyleSheet("background-color: red")

    def ion_status_feedback(self):
        if self.monitor.isChecked():
            self.dac.set_shutter(1, True)
            # One way to switch the level of RF by closing the RF switch
            # self.dac.set_shutter(4, True)
            # The other way to switch the level of RF by changing the setpoint
            self.dac.set_shutter(4, False)  # Keep the RF stabilization on
            self.vref.setHighLevel(False)
            self.monitor.setStyleSheet("background-color: green")
            self.monitor.setText("Ions Coming Back")
        else:
            self.dac.set_shutter(1, False)
            # One way to switch the level of RF by closing the RF switch
            # self.dac.set_shutter(4, False)
            # The other way to switch the level of RF by changing the setpoint
            self.vref.setHighLevel(True)
            self.monitor.setStyleSheet("background-color: red")
            self.monitor.setText("Drive Ions Back")

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())


if __name__ == "__main__":
    myappid = u'PyControl'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    app.setFont(QFont("Vollkorn", 10))
    app.setStyle('Fusion')
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ui = Window()
    ui.center()
    ui.show()
    sys.exit(app.exec_())
