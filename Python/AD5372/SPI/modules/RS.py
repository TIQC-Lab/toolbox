# -*- coding: utf-8 -*-
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
import visa
from .LVSpinBox import *

rm = visa.ResourceManager("@py")

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
