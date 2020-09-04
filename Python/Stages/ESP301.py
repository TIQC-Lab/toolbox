import serial
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
from ctypes import *
import sys
from utils import *


class esp:
    def __init__(self, dev="COM3", b=921600):
        self.dev = serial.Serial(dev, b)
        for i in range(1, 4):
            self.motor(i, False)

    def reset(self, axis):
        if axis in range(1, 4):
            self.dev.write(b"%dOR;%dWS0\r" % (axis, axis))

    def check_errors(self):
        self.dev.write(b"TE?\r")
        return float(self.dev.readline())

    def getpos(self, axis):
        if axis in range(1, 4):
            a = axis
        self.dev.write(b"%dTP\r" % a)
        return float(self.dev.readline())

    def setpos(self, pos, axis):
        if(axis in range(1, 4) and isinstance(pos, (int, float))):
            self.dev.write(b"%dPA%.4f;%dWS1;%dTP\r" % (axis, pos, axis, axis))
        return float(self.dev.readline())

    def position(self, pos, axis):
        if(axis in range(1, 4) and isinstance(pos, (int, float))):
            self.setpos(pos, axis)
        return self.getpos(axis)

    def stop(self, axis):
        if axis in range(1, 4):
            self.dev.write(b"%dST" % (axis))

    def abort(self):
        self.dev.write(b"AB\r")

    def status(self, axis):
        if axis in range(1, 4):
            self.dev.write(b"%dMO?\r" % (axis))
        return int(self.dev.readline())

    def motor(self, axis, state):
        if axis in range(1, 4):
            if state:
                self.dev.write(b"%dMO\r" % (axis))
                return True
            else:
                self.dev.write(b"%dMF\r" % (axis))
                return False

    def close(self):
        for i in range(1, 4):
            self.motor(i, False)
        self.dev.close()


class Axis(GroupCtrl):
    def __init__(self, axis, name, stage):
        super().__init__(name)
        self.device = stage
        self.axis = axis

        self.relative = LVNumCtrl('Relative')
        self.relative.setRange(-13, 13)
        self.relative.setDecimals(5)
        self.go = Button('Move', self.move)

        self.target = LVNumCtrl('Target Pos', self.setPos)
        self.target.setDecimals(5)
        self.target.setRange(-13, 13)
        self.actual = LVNumCtrl('Actual Pos')
        self.actual.setDecimals(5)
        self.actual.setRange(-13, 13)
        self.actual.setReadOnly(True)
        position = self.device.getpos(axis)
        self.target.setValue(position)
        self.actual.setValue(position)

        self.stop = Button("Stop", self.stopMotion)
        self.read = Button("Read", self.readPos)
        self.motor = ButtonCtrl('Motor', self.setMotor)

        layout = QGridLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.relative, 0, 0, 1, 1)
        layout.addWidget(self.go, 0, 1, 1, 2)
        layout.addWidget(self.target, 1, 0, 1, 1)
        layout.addWidget(self.stop, 1, 1, 1, 1)
        layout.addWidget(self.read, 1, 2, 1, 1)
        layout.addWidget(self.actual, 2, 0, 1, 1)
        layout.addWidget(self.motor, 2, 1, 1, 2)
        self.setMotor(False)

    def move(self):
        value = self.relative.value()
        ori = self.target.value()
        self.target.setValue(value+ori)

    def setPos(self):
        position = self.device.setpos(self.target.value(), self.axis)
        self.actual.setValue(position)

    def stopMotion(self):
        self.device.stop(self.axis)

    def readPos(self):
        position = self.device.getpos(self.axis)
        self.target.setValue(position)
        self.actual.setValue(position)

    def setMotor(self, state):
        if state:
            self.device.motor(self.axis, True)
            self.go.setEnabled(True)
            self.target.setReadOnly(False)
        else:
            self.device.motor(self.axis, False)
            self.go.setDisabled(True)
            self.target.setReadOnly(True)



class ESPCtrl(GroupCtrl):
    def __init__(self, COM, names, baudrate=921600):
        super().__init__(COM)
        self.dev = esp(COM, baudrate)
        self.axis = [None]*3
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            self.axis[i] = Axis(i+1, names[i], self.dev)
            layout.addWidget(self.axis[i])
        self.setLayout(layout)


class Window(Widget):
    def __init__(self):
        super().__init__('Newport ESP301')
        self.setWindowIcon(QIcon("esp.jpg"))
        self.stage = [None]*2
        self.stage[0] = ESPCtrl("COM3", ["Axis X", "Axis Y", "Axis 370"])
        self.stage[1] = ESPCtrl("COM7", ["Tilt X", "Tilt Y", "Focus"])
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.stage[0])
        layout.addWidget(self.stage[1])


    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())


if __name__ == "__main__":
    myappid = u'ESP301'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    app.setFont(QFont("Vollkorn", 10))
    app.setStyle('Fusion')
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ui = Window()
    ui.center()
    ui.show()
    sys.exit(app.exec_())
