# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
import visa
from .LVSpinBox import *

rm = visa.ResourceManager("@py")

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
