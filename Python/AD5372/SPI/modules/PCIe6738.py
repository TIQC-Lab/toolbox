import nidaqmx
import numpy as np
import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
from functools import partial
import sys
from utils import *


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


if __name__ == "__main__":
    # myappid = u'PyControl'  # arbitrary string
    # windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    app.setFont(QFont("Vollkorn", 10))
    app.setStyle('Fusion')
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ui = PCIe6738Ctrl()
    # ui.center()
    ui.show()
    sys.exit(app.exec_())
