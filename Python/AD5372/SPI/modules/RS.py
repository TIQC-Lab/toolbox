# -*- coding: utf-8 -*-
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
import visa
from utils import *

rm = visa.ResourceManager("@py")


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
