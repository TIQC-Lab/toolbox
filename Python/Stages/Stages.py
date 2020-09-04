# import serial
# from PyQt5.QtGui import *
# from PyQt5.QtWidgets import *
# from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
from ctypes import *
import sys
from utils import *

from ESP301 import ESPCtrl
from picomotor import PicomotorCtrl


class Window(Widget):
    def __init__(self):
        super().__init__('Stages')
        self.setWindowIcon(QIcon("esp.jpg"))
        self.stage = [None]*3
        self.stage[0] = ESPCtrl("COM3", ["Objective X", "Objective Y", "370 Vertical"])
        self.stage[1] = ESPCtrl("COM7", ["Objective Tilt X", "Objective Tilt Y", "Objective Focus"])
        self.stage[2] = PicomotorCtrl(0x4000, 0x104D, ('EIT Focus', 'EIT Horizontal', 'EIT Vertical', 'Raman',
                                                       'Raman', 'Raman', 'Raman', 'Raman', 'Raman', 'Raman', 'Raman', 'Raman'))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.stage[0])
        layout.addWidget(self.stage[1])
        layout.addWidget(self.stage[2])
        self.center()
        self.show()


    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())


if __name__ == "__main__":
    myappid = u'Stages'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    app.setFont(QFont("Vollkorn", 10))
    app.setStyle('Fusion')
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ui = Window()
    sys.exit(app.exec_())
