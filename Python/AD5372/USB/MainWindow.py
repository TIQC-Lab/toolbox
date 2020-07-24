# -*- coding: utf-8 -*-

import nidaqmx
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
from functools import partial

from ctypes import *


# Open a resource manager of visa
rm = visa.ResourceManager('@py')


class GroupCtrl(QGroupBox):
    def __init__(self, label='', parent=None):
        super().__init__(parent)
        self.setTitle(label)
        self.setStyleSheet(
            '''GroupCtrl{font-weight: bold; font-size:14pt}''')


class LVSpinBox(QDoubleSpinBox):
    ''' Custom SpinBox with similar properties as LabView number controls '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setKeyboardTracking(False)
        self.setStyleSheet(
            '''LVSpinBox{qproperty-alignment:AlignCenter; font-size:10pt}''')

    def stepBy(self, step):
        value = self.value()
        minus = str(self.text()).find('-')
        cursor = self.lineEdit().cursorPosition()
        text = str(self.text())
        length = len(text)
        if minus > -1 and cursor == 0:
            return None
        point = text.find('.')
        if point < 0:
            point = length
        digit = point - cursor
        if cursor == minus + 1:
            digit -= 1
        if digit < -1:
            digit += 1
        self.setValue(value + step*(10**digit))
        # update the cursor position when the value changes
        newlength = len(str(self.text()))
        newcursor = cursor
        if newlength > length:
            if cursor == minus+1:
                newcursor = cursor + 2
            else:
                newcursor = cursor + 1
        elif newlength < length:
            if not cursor == minus+1:
                newcursor = cursor - 1
        else:
            return None
        self.lineEdit().setCursorPosition(newcursor)


class LVNumCtrl(QWidget):
    ''' Column alignment '''
    valueChanged = pyqtSignal(float)

    def __init__(self, label='', func=None, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.addStretch()
        if label != '':
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
            row.addWidget(self.label, 0)
        self.spin = LVSpinBox()
        self.spin.valueChanged.connect(self.valueChanged.emit)
        if func:
            self.valueChanged.connect(func)
        row.addWidget(self.spin, 1)
        row.addStretch()

    def setDecimals(self, decimals=0):
        self.spin.setDecimals(decimals)
        self.spin.adjustSize()

    def setRange(self, low=0, high=100):
        self.spin.setRange(low, high)
        self.spin.adjustSize()

    def value(self):
        if self.spin.decimals() == 0:
            return int(self.spin.value())
        else:
            return self.spin.value()

    def setValue(self, val):
        if val == self.spin.value():
            self.valueChanged.emit(val)
        else:
            self.spin.setValue(val)

    def setReadOnly(self, state):
        self.spin.setReadOnly(state)


class Button(QWidget):
    ''' Clickable button with label '''
    clicked = pyqtSignal(bool)

    def __init__(self, label='', func=None, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.addStretch()
        if label != '':
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
            row.addWidget(self.label, 0)
        self.button = QPushButton()
        row.addWidget(self.button, 1)
        row.addStretch()
        self.button.clicked.connect(self.clicked.emit)
        if func:
            self.clicked.connect(func)


class ButtonCtrl(QWidget):
    ''' Implemented button control with label and checkable property '''
    toggled = pyqtSignal(bool)

    def __init__(self, label='', func=None, default=False, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.addStretch()
        self.text = ('ON', 'OFF')
        if not label == '':
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
            row.addWidget(self.label, 0)
        self.button = QPushButton('ON')
        row.addWidget(self.button, 1)
        row.addStretch()
        # Defaultly False
        self.button.setCheckable(True)
        self.button.setStyleSheet(
            '''QPushButton{background-color:red; font-weight:bold; font-size: 10pt} QPushButton:checked{background-color: green}''')
        self.button.toggled.connect(self.toggled.emit)
        self.toggled.connect(self.updateStatus)
        if func:
            self.toggled.connect(func)
        self.button.setChecked(default)
        self.updateStatus(default)

    def setChecked(self, state):
        self.button.setChecked(state)

    def setStatusText(self, on='ON', off='OFF'):
        self.text = (on, off)
        self.updateStatus(self.button.isChecked())

    def isChecked(self):
        return self.button.isChecked()

    def updateStatus(self, state):
        if state:
            self.button.setText(self.text[0])
        else:
            self.button.setText(self.text[-1])



class PCIe6738(object):
    '''This class is designed to generate voltage outputs of PCI-e 6738 card, it is based on the nidaqmx python package. The basic idea is to create a task before generating a output'''

    def __init__(self, name, channels):
        super().__init__()
        self.name = name
        self.channels = channels

    def set_voltage(self, channel, Vout):
        '''The channel is the number of the printed channel'''
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.name+'/ao'+str(channel))
            task.write(float(Vout), auto_start=True)

    def read_voltage(self, channel):
        '''The method is used to read voltage from the specified channel of PCI-e 6738 card'''
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.name+'/ao'+str(channel))
            value = task.read()
        return value

    def readAll(self):
        '''This method is used to read out all voltages from the specified channels'''
        with nidaqmx.Task() as task:
            for channel in self.channels:
                task.ao_channels.add_ao_voltage_chan(
                    self.name+'/ao'+str(channel))
            values = task.read()
        return values

    def setAll(self, data):
        """
            This function is used to load data within one task instead of instancing multiple tasks
        """
        with nidaqmx.Task() as task:
            for channel in self.channels:
                task.ao_channels.add_ao_voltage_chan(
                    self.name+'/ao'+str(channel))
            task.write(data, auto_start=True)


class PCIe6738Ctrl(GroupCtrl):
    '''The class DAC is a basic family for PCIe 6738, which can be used to implement , a DC supply with \pm 10V, and a combination of multiple channnels'''

    # channelOrder = [0, 2, 4, 6, 8, 11, 12, 14, 16, 18, 20, 22]

    def __init__(self, name='PCIe-6738', channels=range(32)):
        super().__init__(name)
        self.dataFile = 'pcie6738_data.dat'
        self.channelOrder = channels
        self.dataNum = len(channels)
        self.pcie = PCIe6738(name, channels)
        self.createConfig()
        self.createChannels()
        self.create_compensation()
        self.setupUI()
        self.loadData()

    def createChannels(self):
        self.channels = [None]*self.dataNum
        self.data = GroupCtrl(
            "Channels(DC1:1-5, DC2:6-10, RF1:11, RF2:12)")
        self.data.setContentsMargins(1, 1, 1, 1)
        gridLayout = QGridLayout(self.data)
        # Data entries
        for i in range(self.dataNum):
            self.channels[i] = LVNumCtrl(str(i+1), partial(self.dataUpdate, i))
            self.channels[i].setDecimals(4)
            self.channels[i].setRange(-10.0, 10.0)

            gridLayout.addWidget(self.channels[i], i//8, i % 8, 1, 1)
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setSpacing(0)
        gridLayout.setVerticalSpacing(0)

    def create_compensation(self):
        '''This part is used to compensate the DC null to RF null'''
        names = ["Horizontal", "Vertical", "Axial", "DC1", "DC2", "RFs", "All"]
        self.compensationFrame = GroupCtrl(
            "Compensation Combinations: DC1 RF11 DC1-2 DC2-2")
        self.compensate = [[LVNumCtrl(names[i]), Button(
            'GO', partial(self.applyComp, num=i))] for i in range(len(names))]
        layout = QGridLayout(self.compensationFrame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.ratio = LVNumCtrl('Ratio')
        self.ratio.setDecimals(2)
        self.ratio.setRange(0, 50)
        self.ratio.setValue(1)
        layout.addWidget(self.ratio, 0, 0, 1, 1)
        for i in range(len(self.compensate)):
            group = QWidget()
            ly = QHBoxLayout(group)
            self.compensate[i][0].setRange(-1.0, 1.0)
            self.compensate[i][0].setDecimals(4)
            ly.addWidget(self.compensate[i][0], 1)
            ly.addWidget(self.compensate[i][1], 1)
            ly.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(group, (i+1)//4, (i+1) % 4, 1, 1)

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

    def createConfig(self):
        self.pre = QWidget()
        self.update = Button('Reset Board', self.reset)
        self.load = Button('Load Data', self.loadData)
        self.save = Button('Save Data', self.saveData)
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
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setContentsMargins(1, 1, 1, 1)

    def dataUpdate(self, index, value):
        self.set_voltage(self.channelOrder[index], value)

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

        else:
            np.savetxt(self.dataFile, np.zeros(self.dataNum))
            self.reset()

    def saveData(self):
        data = np.array([self.channels[i].value()
                         for i in range(self.dataNum)])
        np.savetxt(self.dataFile, data)

    def reset(self):
        for i in range(self.dataNum):
            self.channels[i].setValue(0.0)
        self.pcie.setAll(np.zeros(self.dataNum))

    def set_voltage(self, channel, Vout):
        if (abs(Vout) > 10.00001):
            print("Voltage over range!")
            return
        self.pcie.set_voltage(channel, Vout)


class AD5372Ctrl(GroupCtrl):
    '''The class DAC is a basic family for AD5732, which can be used to implement a shutter switch, a DC supply with \pm 10V, and a combination of multiple channnels'''

    def __init__(self, title='', parent=None):
        super().__init__(title, parent)
        self.dataFile = 'ad5731_data.dat'
        self.channelOrder = [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15,
                             14, 17, 16, 19, 18, 21, 20, 23, 22, 25, 24, 27, 26, 29, 28, 31, 30]
        self.dll = cdll.LoadLibrary('AD5372.dll')
        self.dataNum = 32
        self.dll.AD5372_Open()
        self.createConfig()
        self.createChannels()
        # self.create_compensation()
        self.createShutters()
        self.setupUI()
        self.loadData()

    def createChannels(self):
        self.channels = [LVNumCtrl(
            str(i+1), partial(self.dataUpdate, index=i)) for i in range(self.dataNum)]
        self.data = GroupCtrl(
            'Channels(DC1:1-5, DC2:6-10, RF1:11, RF2:12,Shutters:13-16)')
        gridLayout = QGridLayout(self.data)
        self.data.setContentsMargins(1, 1, 1, 1)
        # Data entries
        for i in range(self.dataNum):
            self.channels[i].setDecimals(4)
            self.channels[i].setRange(-10.0, 10.0)
            gridLayout.addWidget(self.channels[i], i//8, i % 8, 1, 1)
        gridLayout.setContentsMargins(0, 0, 0, 0)
        gridLayout.setSpacing(0)
        gridLayout.setVerticalSpacing(0)

    # def create_compensation(self):
    #     '''This part is used to compensate the DC null to RF null'''
    #     names = ['Horizontal', 'Vertical', 'Axial', 'DC1', 'DC2', 'RFs', 'All']
    #     self.compensationFrame = GroupCtrl(
    #         'Compensation Combinations: DC1 RF11 DC1-2 DC2-2')
    #     self.compensationFrame.setContentsMargins(1, 1, 1, 1)
    #     self.compensate = [[LVSpinBox(), QPushButton('GO')]]*self.dataNum
    #     layout = QGridLayout()
    #     layout.setContentsMargins(0, 0, 0, 0)
    #     layout.setSpacing(0)
    #     self.ratio = LVSpinBox()
    #     self.ratio.setDecimals(2)
    #     self.ratio.setRange(0, 50)
    #     self.ratio.setValue(1)
    #     groupbox = GroupCtrl()
    #     ly = QHBoxLayout()
    #     ly.setContentsMargins(0, 0, 0, 0)
    #     ly.addWidget(QLabel('DC1:RF1= '))
    #     ly.addWidget(self.ratio, 1)
    #     groupbox.setLayout(ly)
    #     layout.addWidget(groupbox, 0, 0, 1, 1)
    #     for i in range(len(self.compensate)):
    #         groupbox = GroupCtrl()
    #         ly = QHBoxLayout()
    #         self.compensate[i][0].setRange(-1.0, 1.0)
    #         self.compensate[i][0].setDecimals(4)
    #         self.compensate[i][0].setSingleStep(0.0001)
    #         label = QLabel(names[i])
    #         label.setFont(QFont('Microsoft YaHei', 12, 100))
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
        self.shutterFrame = GroupCtrl('Shutters')
        buttons = ['PMT', 'Protection', '399', '935', 'Unlock RF', 'Trap RF']
        self.shutterArray = [13, 14, 15, 16, 17, 19]
        self.shutters = [ButtonCtrl(buttons[i], partial(
            self.switch, i)) for i in range(len(buttons))]
        layout = QHBoxLayout(self.shutterFrame)
        layout.setContentsMargins(0, 0, 0, 0)
        for i in range(len(buttons)):
            self.channels[self.shutterArray[i]-1].setReadOnly(True)
            layout.addWidget(self.shutters[i])

    def createConfig(self):
        self.pre = QWidget()
        self.update = Button('Reset Board', self.reset)
        self.load = Button('Load Data', self.loadData)
        self.save = Button('Save Data', self.saveData)
        hlayout = QHBoxLayout(self.pre)
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.addWidget(self.update)
        hlayout.addWidget(self.load)
        hlayout.addWidget(self.save)

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.pre)
        layout.addWidget(self.data)
        # layout.addWidget(self.compensationFrame)
        layout.addWidget(self.shutterFrame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setContentsMargins(1, 1, 1, 1)

    def set_shutter(self, num, state):
        '''API for shutter'''
        if num < len(self.shutters):
            self.shutters[num].setChecked(state)
        else:
            print('Shutter index over range!')
            exit()

    def dataUpdate(self, value, index):
        self.set_voltage(
            self.channelOrder[index], value)

    def loadData(self):
        '''
            This function is used to load data from local data file, while the argument 'force_mode' is used to specify if all data will sent to the wifi server, otherwise we only change those whose value is different from the one imported from data file, which will generate a signal for the slot.
        '''
        exists = os.path.isfile(self.dataFile)
        if exists:
            data = np.loadtxt(self.dataFile)
            if not data.size == self.dataNum:
                print('data length is wrong!!!')
            for i in range(self.dataNum):
                self.channels[i].setValue(data[i])
            for i in range(len(self.shutters)):
                self.updateShutter(i)
        else:
            np.savetxt(self.dataFile, np.zeros(self.dataNum))
            self.reset()

    def saveData(self):
        data = np.array([self.channels[i].value()
                         for i in range(self.dataNum)])
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

    def switch(self, index, state):
        if state:
            self.channels[self.shutterArray[index]-1].setValue(5)
        else:
            self.channels[self.shutterArray[index]-1].setValue(0.0)

    def set_voltage(self, channel, Vout):
        if (abs(Vout) > 10.00001):
            print('Voltage over range!')
            return
        self.dll.AD5372_DAC(channel, c_double(Vout))
        self.dll.AD5372_LDAC()


class RS(object):
    '''Class used to send commands and acquire data from the Rohde & Schwarz SMA100A & SMB100A
    Signal Generator using PyVisa. Frequency is in unit MHz.
    '''

    def __init__(self, ip):
        '''Class constructor. Here the socket connection to the instrument is initialized. The
        argument required, a string, is the IP adress of the instrument.'''
        # rm = visa.ResourceManager('@py')
        self.sig_gen_ip = ip
        self.sig_gen_socket = rm.open_resource(
            'TCPIP::' + ip + '::inst0::INSTR')

    def query(self, text):
        '''Return the output of the query on text'''
        return self.sig_gen_socket.query(text)

    def write(self, text):
        '''Sends a command to the instrument.'''
        self.sig_gen_socket.write(text)

    def set_frequency(self, freq):
        '''set the frequency value'''
        self.sig_gen_socket.write('SOURCE:FREQUENCY:CW ' + str(freq*10**6))

    def set_amplitude(self, level):
        '''set the amplitude value'''
        self.sig_gen_socket.write(
            'SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE ' + str(level))

    def set_output(self, state):
        if state:
            self.sig_gen_socket.write('OUTPUT:STATE ON')
        else:
            self.sig_gen_socket.write('OUTPUT:STATE OFF')

    def read_frequency(self):
        return (float(self.query('SOURCE:FREQUENCY:CW?'))/10**6)

    def read_amplitude(self):
        return float(self.query('SOURCE:POWER:LEVEL:IMMEDIATE:AMPLITUDE?'))

    def read_status(self):
        # return int(self.query('SENSe:POWer:STATus?'))
        return int(self.query('OUTPUT:STATE?'))

    def set_lfo(self, freq):
        '''set the low frequency output'''
        self.sig_gen_socket.write(':LFO:FREQ ' + str(freq))
        self.sig_gen_socket.write(':LFO:FREQ:MODE FIXED')
        self.sig_gen_socket.write(':LFO:STAT ON')

    def set_am(self, stat):
        '''set the amplitude modulation output'''
        if stat != 0 and stat != 1 and stat != 'ON' and stat != 'OFF':
            print('State should be 1, 0, \'ON\' or \'OFF\'')
            exit()
        self.sig_gen_socket.write(':AM:STAT ' + str(stat))
        self.sig_gen_socket.write(':AM:SOUR INT')
        self.sig_gen_socket.write(':MOD:STAT ON')

    def set_fm(self, stat):
        '''set the frequency modulation output'''
        if stat != 0 and stat != 1 and stat != 'ON' and stat != 'OFF':
            print('State should be 1, 0, \'ON\' or \'OFF\'')
            exit()
        self.sig_gen_socket.write(':FM:STAT ' + str(stat))
        self.sig_gen_socket.write(':FM:SOUR INT')
        self.sig_gen_socket.write(':MOD:STAT ON')

    def set_clk_syn(self, state, freq):
        ''' Set the Clock Synthesis'''
        self.sig_gen_socket.write('CSYN:STAT ' + str(state))
        self.sig_gen_socket.write('CSYN:FREQ ' + str(freq))

    def close_connection(self):
        '''Close the socket connection to the instrument.'''
        self.sig_gen_socket.close()

    def __del__(self):
        self.sig_gen_socket.close()


class RSCtrl(GroupCtrl):
    def __init__(self, ip, title=''):
        super().__init__(title)
        self.device = RS(ip)
        self.freq = LVNumCtrl('Freq', self.set_freq)
        self.freq.setRange(0, 1000)
        self.freq.setDecimals(6)
        freq = self.device.read_frequency()
        if freq > 1000:
            self.freq.setRange(0, 12750)
        self.freq.setValue(freq)
        self.amplitude = LVNumCtrl('Amp', self.set_amp)
        self.amplitude.setRange(-80, 20)
        self.amplitude.setDecimals(2)
        self.amplitude.setValue(self.device.read_amplitude())
        self.switch = ButtonCtrl('', self.set_output)
        if self.device.read_status():
            self.switch.setChecked(True)
        else:
            self.switch.setChecked(False)
        self.create_UI()

    def setRange(self, low=-80, upper=20):
        self.amplitude.setRange(low, upper)

    def create_UI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.freq)
        layout.addWidget(self.amplitude)
        layout.addWidget(self.switch)

    def set_freq(self, value):
        self.device.set_frequency(value)

    def set_amp(self, value):
        self.device.set_amplitude(value)

    def set_output(self, state):
        self.device.set_output(state)


class Power(object):
    def __init__(self, COM, baudrate=9600):
        self.device = rm.open_resource(COM, baud_rate=baudrate)

    def set_voltage(self, Vout):
        self.device.write('SOURCE:VOLTAGE ' + str(Vout))

    def set_current(self, Iout):
        self.device.write('SOURCE:CURRENT ' + str(Iout))

    def set_output(self, state):
        if state:
            self.device.write('OUTPUT ON')
        else:
            self.device.write('OUTPUT OFF')

    def read_voltage(self):
        vol = self.device.query('SOURCE:VOLTAGE?')
        return float(vol)

    def read_current(self):
        cur = self.device.query('SOURCE:CURRENT?')
        return float(cur)

    def read_status(self):
        '''The results returned are "ON" and "OFF" with linebreak'''
        if self.device.query('OUTPUT?') == 'ON\n':
            return True
        else:
            return False

    def close_connection(self):
        '''Close the connection to the instrument.'''
        self.device.close()

    def __del__(self):
        self.device.close()


class PowerCtrl(GroupCtrl):
    def __init__(self, COM, baudrate=9600, title=''):
        super().__init__(title)
        self.device = Power(COM, baudrate)
        self.voltage = LVNumCtrl('Vout', self.set_voltage)
        self.current = LVNumCtrl('Iout', self.set_current)
        self.voltage.setRange(0, 2)
        self.voltage.setDecimals(2)
        voltage = self.device.read_voltage()
        self.voltage.setValue(voltage)
        self.current.setRange(0, 2.2)
        self.current.setDecimals(2)
        time.sleep(0.05)  # avoid writing and reading too fast
        current = self.device.read_current()
        self.current.setValue(current)
        time.sleep(0.05)
        self.switch = ButtonCtrl('', self.set_output)
        if self.device.read_status():
            self.switch.setChecked(True)
        else:
            self.switch.setChecked(False)
        self.create_UI()

    def create_UI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.voltage)
        layout.addWidget(self.current)
        layout.addWidget(self.switch)

    def set_voltage(self, value):
        self.device.set_voltage(value)

    def set_current(self, value):
        self.device.set_current(value)

    def set_output(self, state):
        self.device.set_output(state)

    def set_switch(self, state):
        self.switch.setChecked(state)


class AD5791(object):
    '''This class is designed to control AD5791, and I have set the LDAC at the Low level which enable Synchronous DAC Update 
 at the rising edge of SYNC.'''

    def __init__(self, ser='BSPT002144', dll='usb2uis.dll'):
        self.VREF = 10.0
        self.serial_num = ser
        self.dll = cdll.LoadLibrary(dll)
        # Close the connections if already exist
        self.dll.USBIO_CloseDeviceByNumber(ser)
        self.device_num = self.dll.USBIO_OpenDeviceByNumber(ser)
        if self.device_num == 0xFF:
            print('No USB2UIS can be connected!')
            exit()
        self.SPI_Init()
        self.device_start()

    def SPI_Init(self, frequency=8, mode=1, timeout_read=100, timeout_write=100):
        '''SPI settings, frequency upto 8 selections, representing 200kHz 400kHz, 600kHz, 800kHz, 1MHz, 2MHz, 4MHz, 6MHz and 12MHz. Mode is specified to the clock signal, and the timeout is used to specify the timeout of read and write, occupying 16-bit data respectively'''
        self.dll.USBIO_SPISetConfig(
            self.device_num, (mode << 4)+frequency, (timeout_write << 16)+timeout_read)

    def data(self, Vout):
        return int((Vout+self.VREF)*(2**20-1)/2/self.VREF)

    def device_start(self):
        '''Set the control register to enable the dac into a normal operation mode and offset code style'''
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x200012).to_bytes(3, byteorder='big'), 3)

    def set_voltage(self, Vout):
        '''The Vout set to the DAC should exceed \pm 10V'''
        if abs(Vout) > 10.0000000001:
            print('Voltage over range!')
        else:
            self.dll.USBIO_SPIWrite(self.device_num, None, 0, ((
                0x01 << 20) + self.data(Vout)).to_bytes(3, byteorder='big'), 3)

    def read_voltage(self):
        out = b'\x00'*3
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x900000).to_bytes(3, byteorder='big'), 3)
        self.dll.USBIO_SPIRead(self.device_num, None, 0, out, 3)
        data = int.from_bytes(out, byteorder='big')
        data = data & 0x0FFFFF
        return data*2*self.VREF/(2**20 - 1) - self.VREF

    def LDAC(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x400001).to_bytes(3, byteorder='big'), 3)

    def clear(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x400002).to_bytes(3, byteorder='big'), 3)

    def reset(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x400004).to_bytes(3, byteorder='big'), 3)

    def disable_output(self):
        self.dll.USBIO_SPIWrite(self.device_num, None,
                                0, (0x20001E).to_bytes(3, byteorder='big'), 3)

    def __del__(self):
        self.dll.USBIO_CloseDeviceByNumber(self.serial_num)


class AD5791Ctrl(GroupCtrl):
    def __init__(self, title='', ser='BSPT002144', dll='usb2uis.dll'):
        super().__init__(title)
        self.device = AD5791(ser, dll)
        self.value = LVNumCtrl('Value', self.set_voltage)
        self.value.setDecimals(5)
        self.value.setRange(-10, 10)
        self.value.setValue(self.device.read_voltage())
        self.level = ButtonCtrl('Level', self.changeLevel)
        self.level.setStatusText('High', 'Low')
        self.switch = ButtonCtrl('', self.set_switch, True)
        self.reset = Button('Reset', self.resetAll)

        layout = QHBoxLayout(self)
        layout.addWidget(self.value)
        layout.addWidget(self.level)
        layout.addWidget(self.switch)
        layout.addWidget(self.reset)
        self.setLayout(layout)
        self.setTitle(title)

    def setRange(self, low=0.5, upper=2.0):
        self.value.setRange(low, upper)

    def set_connect(self):
        self.value.valueChanged.connect(self.set_voltage)
        self.switch.toggled.connect(self.set_switch)
        self.reset.clicked.connect(self.resetAll)
        self.level.toggled.connect(self.changeLevel)

    def set_voltage(self, value):
        self.device.set_voltage(value)

    def set_switch(self, state):
        if state:
            self.device.device_start()
            self.level.setChecked(False)
        else:
            self.device.disable_output()

    def resetAll(self):
        self.device.SPI_Init()
        self.device.reset()
        self.switch.setChecked(False)
        self.value.setValue(self.device.read_voltage())

    def changeLevel(self, state):
        if state:
            self.value.setValue(1.5)
        else:
            self.value.setValue(0.7)

    def setHighLevel(self, state):
        if state:
            self.level.setChecked(True)
        else:
            self.level.setChecked(False)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('control-panel.png'))
        self.setWindowIconText('Control Panel')
        self.pcie = PCIe6738Ctrl('PCIe-6738')
        self.dac = AD5372Ctrl('AD5732')
        self.rf = RSCtrl('192.168.32.145', title='RF')
        self.rf.setRange(-80, -2)
        self.raman = RSCtrl('192.168.32.148', title='Raman 173')
        self.raman.setRange(-80, -11.5)
        self.raman_pll = RSCtrl('192.168.32.14', title='Raman 230')
        self.raman_pll.setRange(-80, 10.5)
        self.microwave = RSCtrl('192.168.32.103', title='Microwave')
        self.microwave.setRange(-80, 10)
        self.oven = PowerCtrl('ASRLCOM6::INSTR', 9600, 'Oven')
        self.vref = AD5791Ctrl(title='RF Reference')
        self.vref.setRange(0.5, 2.0)
        self.create_func()
        col = QVBoxLayout(self)
        col.setSpacing(0)
        row = QHBoxLayout()
        col.addLayout(row)
        row.addWidget(self.load_ion)
        row.addWidget(self.monitor)
        row.addWidget(self.laser)

        col.addWidget(self.pcie)
        col.addWidget(self.dac)

        row = QHBoxLayout()
        col.addLayout(row)

        row.addWidget(self.rf)
        row.addWidget(self.raman)
        row.addWidget(self.raman_pll)

        row = QHBoxLayout()
        col.addLayout(row)

        row.addWidget(self.vref)
        row.addWidget(self.oven)
        row.addWidget(self.microwave)

        self.setContentsMargins(1, 1, 1, 1)
        self.setWindowTitle('Control Panel')

    def create_func(self):
        # One button for loading ions with some combined shutter controls
        self.load_ion = ButtonCtrl('Load Ions', self.loading)
        self.monitor = ButtonCtrl('Ions Feedback', self.ion_status_feedback)
        self.laser = ButtonCtrl('Laser Switch', self.laser_switch)

    def laser_switch(self, state):
        # main lasers to control
        laser_ips = ['192.168.32.5', '192.168.32.7', '192.168.32.116']
        if state:
            for ip in laser_ips:
                laser = Laser(ip)
                laser.enable_emission(True)
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

    def loading(self, state):
        if state:
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
        else:
            self.dac.set_shutter(2, False)
            self.oven.set_switch(False)

    def ion_status_feedback(self, state):
        if state:
            self.dac.set_shutter(1, True)
            # One way to switch the level of RF by closing the RF switch
            # self.dac.set_shutter(4, True)
            # The other way to switch the level of RF by changing the setpoint
            self.dac.set_shutter(4, False)  # Keep the RF stabilization on
            self.vref.setHighLevel(False)

        else:
            self.dac.set_shutter(1, False)
            # One way to switch the level of RF by closing the RF switch
            # self.dac.set_shutter(4, False)
            # The other way to switch the level of RF by changing the setpoint
            self.vref.setHighLevel(True)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())


if __name__ == '__main__':
    myappid = u'PyControl'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    app.setFont(QFont('Vollkorn', 10))
    app.setStyle('Fusion')
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ui = Window()
    ui.center()
    ui.show()
    sys.exit(app.exec_())
