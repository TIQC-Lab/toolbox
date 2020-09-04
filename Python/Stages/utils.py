from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

class GroupCtrl(QGroupBox):
    def __init__(self, label='', parent=None):
        super().__init__(parent)
        self.setTitle(label)
        self.setStyleSheet('''GroupCtrl{font-weight: bold; font-size:14pt}''')
        self.setContentsMargins(2, 2, 2, 2)


class Widget(QWidget):
    def __init__(self, label='', parent=None):
        super().__init__(parent)
        self.setContentsMargins(2, 2, 2, 2)
        # if not label:
        #     self.setWindowTitle(label)
        self.setWindowTitle(label)


class LVSpinBox(QDoubleSpinBox):
    """ Custom SpinBox with similar properties as LabView number controls """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setKeyboardTracking(False)
        self.setStyleSheet(
            '''LVSpinBox{qproperty-alignment:AlignCenter; font-size:10pt}''')

    def stepBy(self, step):
        value = self.value()
        minus = str(self.text()).find('-')
        cursor = self.lineEdit().cursorPosition()
        text = str(self.text())
        length = len(text)
        if minus > -1 and cursor == 0:
            return None
        point = text.find('.')
        if point < 0:
            point = length
        digit = point - cursor
        if cursor == minus + 1:
            digit -= 1
        if digit < -1:
            digit += 1
        self.setValue(value + step*(10**digit))
        # update the cursor position when the value changes
        newlength = len(str(self.text()))
        newcursor = cursor
        if newlength > length:
            if cursor == minus+1:
                newcursor = cursor + 2
            else:
                newcursor = cursor + 1
        elif newlength < length:
            if not cursor == minus+1:
                newcursor = cursor - 1
        else:
            return None
        self.lineEdit().setCursorPosition(newcursor)


class LVNumCtrl(Widget):
    """ Column alignment """
    valueChanged = pyqtSignal(float)

    def __init__(self, label='', func=None, horizontal=False, parent=None):
        super().__init__('', parent)
        if horizontal:
            layout = QHBoxLayout(self)
        else:
            layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addStretch()
        if label != '':
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
            layout.addWidget(self.label, 0)
        self.spin = LVSpinBox()
        layout.addWidget(self.spin, 1)
        layout.addStretch()
        self.spin.valueChanged.connect(self.valueChanged.emit)
        if func:
            self.valueChanged.connect(func)

    def setDecimals(self, decimals=0):
        self.spin.setDecimals(decimals)

    def setRange(self, low=0, high=100):
        self.spin.setRange(low, high)

    def value(self):
        if self.spin.decimals() == 0:
            return int(self.spin.value())
        else:
            return self.spin.value()

    def setValue(self, val):
        self.spin.setValue(val)

    def setSignalValue(self, val):
        if val == self.spin.value():
            self.valueChanged.emit(val)
        else:
            self.spin.setValue(val)

    def setReadOnly(self, state):
        self.spin.setReadOnly(state)


class Button(Widget):
    """ Clickable button with label """
    clicked = pyqtSignal(bool)

    def __init__(self, label='', func=None, horizontal=False, parent=None):
        super().__init__('', parent)
        if horizontal:
            layout = QHBoxLayout(self)
        else:
            layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addStretch()
        if label != '':
            self.label = QLabel(label)
            layout.addWidget(self.label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
        self.button = QPushButton()
        layout.addWidget(self.button)
        layout.addStretch()
        self.button.clicked.connect(self.clicked.emit)
        if func:
            self.clicked.connect(func)

    def setButtonText(self, text):
        self.button.setText(text)

    def setSize(self, width, height):
        self.button.resize(width, height)


class ButtonCtrl(Widget):
    """ Implemented button control with label and checkable property """
    toggled = pyqtSignal(bool)

    def __init__(self,  label='', func=None, default=False, horizontal=False, parent=None):
        super().__init__('', parent)
        if horizontal:
            layout = QHBoxLayout(self)
        else:
            layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addStretch()
        self.text = ('ON', 'OFF')
        if label != '':
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
            layout.addWidget(self.label, 0)
        self.button = QPushButton('ON')
        layout.addWidget(self.button, 1)
        layout.addStretch()
        # Defaultly False
        self.button.setCheckable(True)
        self.button.setChecked(default)
        self.button.setStyleSheet(
            '''QPushButton{background-color:red; font-weight:bold; font-size: 10pt} QPushButton:checked{background-color: green}''')
        self.button.toggled.connect(self.toggled.emit)
        self.toggled.connect(self.updateStatus)
        if func:
            self.toggled.connect(func)
        self.updateStatus(default)

    def setChecked(self, state):
        self.button.setChecked(state)

    def setStatusText(self, on='ON', off='OFF'):
        self.text = (on, off)
        self.updateStatus(self.button.isChecked())

    def isChecked(self):
        return self.button.isChecked()

    def updateStatus(self, state):
        if state:
            self.button.setText(self.text[0])
        else:
            self.button.setText(self.text[-1])
