# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
import visa
from utils import *

rm = visa.ResourceManager("@py")


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
