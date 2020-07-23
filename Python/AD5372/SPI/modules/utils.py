# -*- coding: utf-8 -*-
from ctypes import alignment
import sys
import time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QFont, QIcon, QPen
from PyQt5.QtWidgets import (
    QAbstractSpinBox,
    QAction,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy
)

class EnumCtrl(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, label='', func=None, parent=None):
        super().__init__(parent)
        col = QVBoxLayout(self)
        col.addStretch()
        if label:
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{font-size:14pt; font-family: Microsoft YaHei}''')
            col.addWidget(self.label)
        self.enum = QComboBox()
        self.enum.setStyleSheet(
            '''QComboBox{font-family:Microsoft YaHei; font-size:12pt}''')
        col.addWidget(self.enum)
        col.addStretch()
        self.enum.currentIndexChanged.connect(self.valueChanged.emit)
        if func:
            self.valueChanged.connect(func)

    def count(self):
        return self.enum.count()

    def setItems(self, items):
        self.enum.clear()
        self.enum.addItems(items)

    def value(self):
        return int(self.enum.currentIndex())

    def setValue(self, value):
        if isinstance(value, str):
            value = self.enum.findText(value)
        self.enum.setCurrentIndex(value)

    def text(self):
        return str(self.enum.currentText())

    def textAt(self, index=None):
        if index:
            return str(self.enum.itemText(index))
        else:
            return str(self.enum.currentText())


class GroupCtrl(QGroupBox):
    def __init__(self, label='', parent=None):
        super().__init__(parent)
        self.setTitle(label)
        self.setStyleSheet(
            '''GroupCtrl{font-weight: bold; font-size:14pt}''')


class LVSpinBox(QDoubleSpinBox):
    ''' Custom SpinBox with similar properties as LabView number controls '''

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


class LVNumCtrl(QWidget):
    ''' Column alignment '''
    valueChanged = pyqtSignal(float)

    def __init__(self, label='', func=None, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        self.label = QLabel(label)
        self.spin = LVSpinBox()
        self.spin.valueChanged.connect(self.valueChanged.emit)
        if func:
            self.valueChanged.connect(func)

        self.label.setStyleSheet(
            '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
        row.addStretch()
        row.addWidget(self.label, 0)
        row.addWidget(self.spin, 1)
        row.addStretch()

    def setDecimals(self, decimals=0):
        self.spin.setDecimals(decimals)
        self.spin.adjustSize()

    def setRange(self, low=0, high=100):
        self.spin.setRange(low, high)
        self.spin.adjustSize()

    def value(self):
        if self.spin.decimals() == 0:
            return int(self.spin.value())
        else:
            return self.spin.value()

    def setValue(self, val):
        if val == self.spin.value():
            self.valueChanged.emit(val)
        else:
            self.spin.setValue(val)

    def setReadOnly(self, state):
        self.spin.setReadOnly(state)


class Button(QWidget):
    ''' Clickable button with label '''
    clicked = pyqtSignal(bool)

    def __init__(self, label='', func=None, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.addStretch()
        if not label == '':
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
            row.addWidget(self.label, 0)
        self.button = QPushButton()
        row.addWidget(self.button, 1)
        row.addStretch()
        self.button.setFont(QFont('Microsoft YaHei', 10, True))
        self.button.clicked.connect(self.clicked.emit)
        if func:
            self.clicked.connect(func)


class ButtonCtrl(QWidget):
    ''' Implemented button control with label and checkable property '''
    toggled = pyqtSignal(bool)

    def __init__(self,  label='', func=None, default=False, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.addStretch()
        self.text = ['ON', 'OFF']
        if not label == '':
            self.label = QLabel(label)
            self.label.setStyleSheet(
                '''QLabel{qproperty-alignment:AlignCenter; font-size:12pt}''')
            row.addWidget(self.label, 0)
        self.button = QPushButton('ON')
        row.addWidget(self.button, 1)
        row.addStretch()
        # Defaultly False
        self.button.setCheckable(True)
        self.button.setStyleSheet(
            '''QPushButton{background-color:red; font-weight:bold; font-size: 10pt} QPushButton:checked{background-color: green}''')
        self.button.toggled.connect(self.toggled.emit)
        self.toggled.connect(self.updateStatus)
        if func:
            self.toggled.connect(func)
        self.button.setChecked(default)
        self.updateStatus(default)

    def setLabel(self, label=''):
        self.label.setText(label)

    def setChecked(self, state):
        self.button.setChecked(state)

    def setStatusText(self, on='ON', off='OFF'):
        self.text = [on, off]
        self.updateStatus(self.button.isChecked())

    def status(self):
        return self.button.isChecked()

    def updateStatus(self, state):
        if state:
            self.button.setText(self.text[0])
        else:
            self.button.setText(self.text[-1])

