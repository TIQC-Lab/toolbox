import nidaqmx
import numpy as np
import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect

myfont = QFont()
myfont.setBold(True)


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


class pcie6738(object):
    '''This class is designed to generate voltage outputs of PCI-e 6738 card, it is based on the nidaqmx python package. The basic idea is to create a task before generating a output'''

    def __init__(self, name, channels):
        super().__init__()
        self.name = name
        self.channels = channels

    def set_voltage(self, index, Vout):
        '''The channel is the number of the printed channel'''
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.name+'/ao'+str(self.channels[index]))
            task.write(float(Vout), auto_start=True)

    def read_voltage(self, index):
        '''The method is used to read voltage from the specified channel of PCI-e 6738 card'''
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(
                self.name+'/ao'+str(self.channels[index]))
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


class PCIe6738Ctrl(QGroupBox):
    '''The class DAC is a basic family for PCIe 6738, which can be used to implement , a DC supply with \pm 10V, and a combination of multiple channnels'''
    dataFile = "data_pcie6738.dat"
    dataNum = 12
    # channelOrder = [0, 2, 4, 6, 8, 11, 12, 14, 16, 18, 20, 22]

    def __init__(self, name='Dev1', channels=range(32)):
        super().__init__()
        self.pcie = pcie6738(name, channels)
        self.createConfig()
        self.createChannels()
        self.create_compensation()
        self.setupUI()
        self.setConnect()
        self.loadData()

    def createChannels(self):
        data = self.pcie.readAll()
        self.channels = [LVSpinBox()]*self.dataNum
        gridLayout = QGridLayout()
        self.data = QGroupBox(
            "Channels(DC1:1-5, DC2:6-10, RF1:11, RF2:12)")
        self.data.setContentsMargins(1, 1, 1, 1)
        # Data entries
        for i in range(self.dataNum):
            # self.channels[i] = LVSpinBox()
            self.channels[i].setValue(data[i])
            self.channels[i].setDecimals(4)
            self.channels[i].setRange(-10.0, 10.0)
            groupbox = QGroupBox()
            layout = QHBoxLayout()
            label = QLabel(str(i+1))
            layout.addWidget(label, 0)
            layout.addWidget(self.channels[i], 1)
            layout.setContentsMargins(1, 1, 1, 1)
            groupbox.setLayout(layout)
            gridLayout.addWidget(groupbox, i//6, i % 6, 1, 1)
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

    def createConfig(self):
        self.pre = QGroupBox('PCIe 6738')
        # self.pre.setGeometry(10, 10, 950, 30)
        # self.pre.setContentsMargins(1, 1, 1, 1)
        self.update = QPushButton('Reset')
        self.update.setFont(myfont)
        self.load = QPushButton('Load Data')
        self.load.setFont(myfont)
        self.save = QPushButton('Save Data')
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
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setContentsMargins(1, 1, 1, 1)

    def setConnect(self):
        self.update.clicked.connect(self.reset)
        self.load.clicked.connect(self.loadData)
        self.save.clicked.connect(self.saveData)
        for i in range(self.dataNum):
            self.channels[i].valueChanged.connect(
                lambda chk, i=i: self.dataUpdate(i))
        for i in range(len(self.compensate)):
            self.compensate[i][1].clicked.connect(
                lambda chk, key=i: self.applyComp(key))

    def dataUpdate(self, index):
        self.set_voltage(index, self.channels[index].value())

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
                if self.channels[i].value() == data[i]:
                    self.set_voltage(i, data[i])
                else:
                    self.channels[i].setValue(data[i])

        else:
            np.savetxt(self.dataFile, np.zeros(self.dataNum))
            self.reset()

    def saveData(self):
        data = np.array([self.channels[i].value() for i in range(self.dataNum)])
        np.savetxt(self.dataFile, data)

    def reset(self):
        for i in range(self.dataNum):
            self.channels[i].setValue(0.0)
        self.pcie.setAll(np.zeros(self.dataNum))

    def set_voltage(self, index, Vout):
        if (abs(Vout) > 10.00001):
            print("Voltage over range!")
            return
        self.pcie.set_voltage(index, Vout)
