# -*- coding: utf-8 -*-

import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
from modules.TopticaLaser import TopticaLaser as Laser
from ctypes import *
from modules.RS import *
from modules.Power import *
from modules.LVSpinBox import *
from modules.AD5372 import *
from modules.AD5791 import *
from modules.PCIe6738 import *



class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("control-panel.png"))
        self.setWindowIconText("Control Panel")
        self.dc = PCIe6738Ctrl(
            'PCIe-6738', [0, 2, 4, 6, 8, 11, 12, 14, 16, 18, 20, 22])
        self.dac = AD5372Ctrl()
        # self.dac = QPushButton('AD 5372')
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
        self.vref = AD5791Ctrl("BSPT002144", "usb2uis.dll")
        self.vref.setRange(0.5, 2.0)
        self.vref.setTitle("RF Reference")
        self.create_func()
        layout = QGridLayout()
        layout.addWidget(self.load_ion, 0, 0, 1, 1)
        layout.addWidget(self.monitor, 0, 1, 1, 1)
        layout.addWidget(self.laser, 0, 2, 1, 1)
        layout.addWidget(self.dc,1, 0, 1, 3)
        layout.addWidget(self.dac, 2, 0, 1, 3)
        layout.addWidget(self.rf, 3, 0, 1, 1)
        layout.addWidget(self.raman, 3, 1, 1, 1)
        layout.addWidget(self.raman_pll, 3, 2, 1, 1)
        layout.addWidget(self.vref, 4, 0, 1, 1)
        layout.addWidget(self.oven, 4, 1, 1, 1)
        layout.addWidget(self.microwave, 4, 2, 1, 1)
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
