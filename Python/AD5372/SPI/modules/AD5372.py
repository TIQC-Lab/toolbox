# -*- coding: utf-8 -*-

import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
import numpy as np
from LVSpinBox import *
from ctypes import *


class AD5372(object):
    """This class is designed to control AD5372, and I have set the LDAC at the Low level which enable Synchronous DAC Update 
 at the rising edge of SYNC with the DGND pin of sub2spi module."""

    def __init__(self, ser="BSPT002144", dll="usb2uis.dll"):
        self.VREF = 5.0
        self.offset_code = 0x2000
        self.channels = [0x08+i for i in range(32)]
        self.serial_num = ser
        self.dll = cdll.LoadLibrary(dll)
        self.connect()
        self.SPI_Init()
        self.device_start()

    def SPI_Init(self, frequency=8, mode=1, timeout_read=100, timeout_write=100):
        """SPI settings, frequency upto 8 selections, representing 200kHz 400kHz, 600kHz, 800kHz, 1MHz, 2MHz, 4MHz, 6MHz and 12MHz. Mode is specified to the clock signal, and the timeout is used to specify the timeout of read and write, occupying 16-bit data respectively"""
        self.dll.USBIO_SPISetConfig(
            self.device_num, (mode << 4)+frequency, (timeout_write << 16)+timeout_read)

    def data(self, Vout):
        return int(Vout * 2**16 / (4 * self.VREF) + self.offset_code * 4)

    def device_start(self):
        """Set the both offset DACs"""
        self.enable_output()
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x022000).to_bytes(3, byteorder="big"), 3)
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x032000).to_bytes(3, byteorder="big"), 3)

    def set_voltage(self, channel, Vout):
        """The Vout set to the DAC should exceed \pm 10V"""
        if abs(Vout) > 10.00001:
            print("Voltage over range!")
        else:
            self.dll.USBIO_SPIWrite(self.device_num, None, 0, ((self.channels[channel] << 16) + (
                0x03 << 22) + self.data(Vout)).to_bytes(3, byteorder="big"), 3)

    def read_voltage(self, channel):
        out = b'\x00'*3
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x50000 + self.channels[channel] << 7).to_bytes(3, byteorder="big"), 3)
        self.dll.USBIO_SPIRead(self.device_num, None, 0, out, 3)
        data = int.from_bytes(out, byteorder="big")
        data = data & 0xFFFF
        return float(self.VREF*4.0*(data-4*self.offset_code)/2**16)

    def reset(self):
        self.connect()
        self.SPI_Init()
        self.device_start()

    def disable_output(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x10001).to_bytes(3, byteorder="big"), 3)
    def enable_output(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x10000).to_bytes(3, byteorder="big"), 3)

    def connect(self):
        # Close the connections if already exist
        self.dll.USBIO_CloseDeviceByNumber(self.serial_num)
        self.device_num = self.dll.USBIO_OpenDeviceByNumber(self.serial_num)
        if self.device_num == 0xFF:
            print("No USB2UIS can be connected!")
            exit()

    def __del__(self):
        self.dll.USBIO_CloseDeviceByNumber(self.serial_num)

class AD5372Ctrl(QGroupBox):
    '''The class DAC is a basic family for AD5732, which can be used to implement a shutter switch, a DC supply with \pm 10V, and a combination of multiple channnels'''
    dataFile = "data.dat"
    channelOrder = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15,
                    14, 17, 16, 19, 18, 21, 20, 23, 22, 25, 24, 27, 26, 29, 28, 31, 30]
    dataNum = 32

    def __init__(self):
        super().__init__()
        self.device = AD5372()
        self.createConfig()
        self.createChannels()
        self.init()
        self.create_compensation()
        self.createShutters()
        self.setupUI()
        self.setConnect()
        self.loadData(True)

    def createChannels(self):
        self.channels = [LVSpinBox() for i in range(self.dataNum)]
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

    def init(self):
        for i in range(self.dataNum):
            self.channels[i].setValue(self.device.read_voltage(self.channelOrder[i]))

    # def create_compensation(self):
    #     '''This part is used to compensate the DC null to RF null'''
    #     names = ["Horizontal", "Vertical", "Axial", "DC1", "DC2", "RFs", "All"]
    #     self.compensationFrame = QGroupBox(
    #         "Compensation Combinations: DC1 RF11 DC1-2 DC2-2")
    #     self.compensationFrame.setContentsMargins(1, 1, 1, 1)
    #     self.compensate = [[LVSpinBox(), QPushButton('GO')] for i in range(len(names))]
    #     layout = QGridLayout()
    #     layout.setContentsMargins(0, 0, 0, 0)
    #     layout.setSpacing(0)
    #     self.ratio = LVSpinBox()
    #     self.ratio.setDecimals(2)
    #     self.ratio.setRange(0, 50)
    #     self.ratio.setValue(1)
    #     groupbox = QGroupBox()
    #     ly = QHBoxLayout()
    #     ly.setContentsMargins(0, 0, 0, 0)
    #     ly.addWidget(QLabel("DC1:RF1= "))
    #     ly.addWidget(self.ratio, 1)
    #     groupbox.setLayout(ly)
    #     layout.addWidget(groupbox, 0, 0, 1, 1)
    #     for i in range(len(self.compensate)):
    #         groupbox = QGroupBox()
    #         ly = QHBoxLayout()
    #         self.compensate[i][0].setRange(-1.0, 1.0)
    #         self.compensate[i][0].setDecimals(4)
    #         self.compensate[i][0].setSingleStep(0.0001)
    #         label = QLabel(names[i])
    #         label.setFont(myfont)
    #         ly.addWidget(label)
    #         ly.addWidget(self.compensate[i][0], 1)
    #         ly.addWidget(self.compensate[i][1], 1)
    #         ly.setContentsMargins(0, 0, 0, 0)
    #         groupbox.setLayout(ly)
    #         layout.addWidget(groupbox, (i+1)//4, (i+1) % 4, 1, 1)
    #     self.compensationFrame.setLayout(layout)

    # def applyComp(self, num):
    #     if num == 0:
    #         for i in range(5):
    #             self.channels[i].setValue(
    #                 self.channels[i].value() + self.compensate[num][0].value())
    #         self.channels[10].setValue(self.channels[10].value(
    #         ) + self.ratio.value()*self.compensate[num][0].value())
    #     elif num == 1:
    #         for i in range(5):
    #             self.channels[i].setValue(
    #                 self.channels[i].value() + self.compensate[num][0].value())
    #         self.channels[10].setValue(self.channels[10].value(
    #         ) - self.ratio.value()*self.compensate[num][0].value())
    #     elif num == 2:
    #         for i in (0, 5):
    #             self.channels[i].setValue(
    #                 self.channels[i].value() + self.compensate[num][0].value())
    #     elif num == 3:
    #         for i in range(5):
    #             self.channels[i].setValue(
    #                 self.channels[i].value() + self.compensate[num][0].value())
    #     elif num == 4:
    #         for i in range(5, 10):
    #             self.channels[i].setValue(
    #                 self.channels[i].value() + self.compensate[num][0].value())
    #     elif num == 5:
    #         for i in (10, 11):
    #             self.channels[i].setValue(
    #                 self.channels[i].value() + self.compensate[num][0].value())
    #     elif num == 6:
    #         for i in range(12):
    #             self.channels[i].setValue(
    #                 self.channels[i].value() + self.compensate[num][0].value())

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
        # self.connection = QPushButton('Connect')
        # self.connection.setFont(myfont)
        self.status = QPushButton('ON')
        self.status.setFont(myfont)
        self.status.setCheckable(True)
        self.status.setChecked(True)
        self.status.setStyleSheet('background-color: green')
        self.update = QPushButton('Reset Board')
        self.update.setFont(myfont)
        self.load = QPushButton('Load Data')
        self.load.setFont(myfont)
        self.save = QPushButton("Save Data")
        self.save.setFont(myfont)
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        # hlayout.addWidget(self.connection)
        hlayout.addWidget(self.status)
        hlayout.addWidget(self.update)
        hlayout.addWidget(self.load)
        hlayout.addWidget(self.save)
        self.pre.setLayout(hlayout)

    def setupUI(self):
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.pre)
        self.layout.addWidget(self.data)
        # self.layout.addWidget(self.compensationFrame)
        self.layout.addWidget(self.shutterFrame)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setContentsMargins(1, 1, 1, 1)
        # self.setWindowTitle("AD5372")

    def setConnect(self):
        # self.connection.clicked.connect(self.device.connect)
        self.status.toggled.connect(self.On)
        self.update.clicked.connect(self.reset)
        self.load.clicked.connect(self.loadData)
        self.save.clicked.connect(self.saveData)
        for i in range(self.dataNum):
            self.channels[i].valueChanged.connect(
                lambda chk, i=i: self.dataUpdate(i))
        for i in range(len(self.shutters)):
            self.shutters[i].toggled.connect(
                lambda chk, key=i: self.switch(key))
        # for i in range(len(self.compensate)):
        #     self.compensate[i][1].clicked.connect(
        #         lambda chk, key=i: self.applyComp(key))

    def On(self):
        if self.status.isChecked():
            self.device.enable_output()
            self.status.setFont('ON')
            self.status.setStyleSheet('background-color: green')
        else:
            self.device.disable_output()
            self.status.setFont('OFF')
            self.status.setStyleSheet('background-color: red')

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

    def loadData(self):
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
            for i in range(len(self.shutters)):
                self.updateShutter(i)
        else:
            np.savetxt(self.dataFile, np.zeros(self.dataNum))
            self.reset()

    def saveData(self):
        data = np.array([self.channels[i].value() for i in range(self.dataNum)])
        np.savetxt(self.dataFile, data)

    def reset(self):
        self.device.reset()
        self.init()

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
        self.device.set_voltage(channel, float(Vout))
