import serial
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize, QRect
from ctypes import *
import sys

class LVSpinBox(QDoubleSpinBox):
    stepChanged = pyqtSignal()

    def stepBy(self, step):
        value = self.value()
        point = str(self.text()).find('.')
        if point < 0:
            point = len(str(self.text()))
        digit = point - self.lineEdit().cursorPosition()
        if digit < 0:
            digit += 1
        self.setValue(value + step*(10**digit))
        if self.value() != value:
            self.stepChanged.emit()

    def onValueChanged(self, func):
        self.editingFinished.connect(func)
        self.stepChanged.connect(func)


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


class Axis(QGroupBox):
    def __init__(self, axis, name, stage):
        super().__init__()
        self.device = stage
        self.setTitle(name)
        self.axis = axis
        self.target = LVSpinBox()
        self.target.setDecimals(5)
        self.target.setRange(-13, 13)
        self.actual = LVSpinBox()
        self.actual.setDecimals(5)
        self.actual.setRange(-13, 13)
        self.target.setReadOnly(True)
        self.actual.setReadOnly(True)
        position = self.device.getpos(axis)
        self.target.setValue(position)
        self.actual.setValue(position)
        self.stop = QPushButton("Stop")
        self.read = QPushButton("Read")
        self.motor = QPushButton("Motor Off")
        self.motor.setCheckable(True)
        if self.device.status(axis):
            self.motor.setChecked(True)
            self.motor.setText("Motor On")
            self.motor.setStyleSheet("background-color: green")
        else:
            self.motor.setChecked(False)
            self.motor.setText("Motor Off")
            self.motor.setStyleSheet("background-color: red")
        layout = QGridLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(QLabel("Target Pos"), 0, 0, 1, 1)
        layout.addWidget(self.target, 0, 1, 1, 1)
        layout.addWidget(self.stop, 0, 2, 1, 1)
        layout.addWidget(self.read, 0, 3, 1, 1)
        layout.addWidget(QLabel("Actual Pos"), 1, 0, 1, 1)
        layout.addWidget(self.actual, 1, 1, 1, 1)
        layout.addWidget(self.motor, 1, 2, 1, 2)
        self.setLayout(layout)
        self.setConnect()

    def setPos(self):
        position = self.device.setpos(self.target.value(), self.axis)
        self.actual.setValue(position)


    def stopMotion(self):
        self.device.stop(self.axis)

    def readPos(self):
        position = self.device.getpos(self.axis)
        self.target.setValue(position)
        self.actual.setValue(position)

    def setMotor(self):
        if self.motor.isChecked():
            self.device.motor(self.axis, True)
            self.motor.setText("Motor On")
            self.motor.setStyleSheet("background-color: green")
            self.target.setReadOnly(False)
        else:
            self.device.motor(self.axis, False)
            self.motor.setText("Motor Off")
            self.motor.setStyleSheet("background-color: red")
            self.target.setReadOnly(True)

    def setConnect(self):
        self.target.valueChanged.connect(self.setPos)
        self.stop.clicked.connect(self.stopMotion)
        self.read.clicked.connect(self.readPos)
        self.motor.toggled.connect(self.setMotor)


class ESPCtrl(QGroupBox):
    def __init__(self, COM, names, baudrate=921600):
        super().__init__()
        self.dev = esp(COM, baudrate)
        self.setTitle(COM)
        self.axis = [None]*3
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            self.axis[i] = Axis(i+1, names[i], self.dev)
            layout.addWidget(self.axis[i])
        self.setLayout(layout)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("esp.jpg"))
        self.stage = [None]*2
        self.stage[0] = ESPCtrl("COM3", ["Axis X", "Axis Y", "Axis 370"])
        self.stage[1] = ESPCtrl("COM7", ["Tilt X", "Tilt Y", "Focus"])
        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.stage[0])
        layout.addWidget(self.stage[1])
        self.setLayout(layout)
        self.setWindowTitle("Newport ESP301")

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
