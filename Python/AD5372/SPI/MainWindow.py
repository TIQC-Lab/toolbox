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
from modules.utils import *



class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("control-panel.png"))
        self.setWindowIconText("Control Panel")
        self.pcie = PCIe6738Ctrl(
            'PCIe-6738', [0, 2, 4, 6, 8, 11, 12, 14, 16, 18, 20, 22])
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
