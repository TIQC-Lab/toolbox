# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QIcon
import serial

if __name__ == "__main__":
    ps = serial.Serial()
    ps.baudrate = 9600
    ps.port = "COM3"
    ps.open()
    if(ps.open):
        ps.write(b"SYSTEM:INTERFACE RS232")
        ps.write(b"SYSTEM:REMOTE")
        ps.write(b"VOLTAGE 2.0")
        ps.write(b"CURRENT 2.1")
        ps.write(b"OUTPUT ON")
