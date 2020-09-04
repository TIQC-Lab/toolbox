"""Python Driver for NewFocus controllers
Requirements:
    python (version > 2.7)
    re
    pyusb: $ pip install pyusb
    libusb-compat (USB backend): $ brew install libusb-compat
Notes:
 1. This module is not tested yet
 2. It will be combined with ESP301 module within a GUI
"""
import sys
import usb.core
import usb.util
import re
import time
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from utils import *


NEWFOCUS_COMMAND_REGEX = re.compile("([0-9]{0,1})([a-zA-Z*]{2,})([0-9+.?-]*)")

MOTOR_TYPE = {
    "0": "No motor connected",
    "1": "Motor Unknown",
    "2": "'Tiny' Motor",
    "3": "'Standard' Motor"
}


class Controller(object):
    """Picomotor Controller
    Example:
        >>> controller = Controller(idProduct=0x4000, idVendor=0x104d)
        >>> controller.command('VE?')
        
        >>> controller.start_console()
    """

    def __init__(self, idProduct, idVendor, slaves):
        """Initialize the Picomotor class with the spec's of the attached device
        Call self._connect to set up communication with usb device and endpoints 
        
        Args:
            idProduct (hex): Product ID of picomotor controller
            idVendor (hex): Vendor ID of picomotor controller
        """
        self.idProduct = idProduct
        self.idVendor = idVendor
        self.slaves = slaves
        self._connect()

    def _connect(self):
        """Connect class to USB device 
        Find device from Vendor ID and Product ID
        Setup taken from [1]
        Raises:
            ValueError: if the device cannot be found by the Vendor ID and Product
                ID
            Assert False: if the input and outgoing endpoints can't be established
        """
        # find the device
        self.dev = usb.core.find(
            idProduct=self.idProduct,
            idVendor=self.idVendor
        )

        if self.dev is None:
            raise ValueError('Device not found')

        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        self.dev.set_configuration()

        # get an endpoint instance
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0, 0)]

        self.ep_out = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match=lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_OUT)

        self.ep_in = usb.util.find_descriptor(
            intf,
            # match the first IN endpoint
            custom_match=lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_IN)

        assert (self.ep_out and self.ep_in) is not None
        # Confirm connection to user
        for slave in range(1, self.slaves+1):
            resp = self.command(slave, 'VE?')
            print("Connected to Motor Controller Model {}. Firmware {} {} {}\n".format(*resp.split(' ')))
            for m in range(1, 5):
                resp = self.command(slave, "{}QM?".format(m))
                print("Motor #{motor_number}: {status}".format(
                    motor_number=m,
                    status=MOTOR_TYPE[resp[-1]]
                ))

    def send_command(self, usb_command, get_reply=False):
        """Send command to USB device endpoint
        
        Args:
            usb_command (str): Correctly formated command for USB driver
            get_reply (bool): query the IN endpoint after sending command, to 
                get controller's reply
        Returns:
            Character representation of returned hex values if a reply is 
                requested
        """
        self.ep_out.write(usb_command)
        if get_reply:
            return self.ep_in.read(100)

    def parse_command(self, slave, newfocus_command):
        """Convert a NewFocus style command into a USB command
        Args:
            newfocus_command (str): of the form xxAAnn
                > The general format of a command is a two character mnemonic (AA). 
                Both upper and lower case are accepted. Depending on the command, 
                it could also have optional or required preceding (xx) and/or 
                following (nn) parameters.
                cite [2 - 6.1.2]
        """
        m = NEWFOCUS_COMMAND_REGEX.match(newfocus_command)

        # Check to see if a regex match was found in the user submitted command
        if m:

            # Extract matched components of the command
            driver_number, command, parameter = m.groups()

            usb_command = command

            # Construct USB safe command
            if driver_number:
                usb_command = '{driver_number} {command}'.format(
                    driver_number=driver_number,
                    command=usb_command
                )
            if parameter:
                usb_command = '{command} {parameter}'.format(
                    command=usb_command,
                    parameter=parameter
                )
            usb_command = str(slave) + '>' + usb_command + '\r'

            return usb_command
        else:
            print("ERROR! Command {} was not a valid format".format(
                newfocus_command
            ))

    def parse_reply(self, reply):
        """Take controller's reply and make human readable
        Args:
            reply (list): list of bytes returns from controller in hex format
        Returns:
            reply (str): Cleaned string of controller reply
        """

        # convert hex to characters
        reply = ''.join([chr(x) for x in reply])
        parse = reply.rstrip()
        if '>' in parse:
            return parse[2:]
        else:
            return parse

    def command(self, slave, newfocus_command):
        """Send NewFocus formated command
        Args:
            newfocus_command (str): Legal command listed in usermanual [2 - 6.2] 
        Returns:
            reply (str): Human readable reply from controller
        """
        usb_command = self.parse_command(slave, newfocus_command)
        # if there is a '?' in the command, the user expects a response from
        # the driver
        if '?' in newfocus_command:
            get_reply = True
        else:
            get_reply = False

        reply = self.send_command(usb_command, get_reply)

        # if a reply is expected, parse it
        if get_reply:
            return self.parse_reply(reply)

    def setPos(self, slave, axis, position):
        '''axis of the slave should be in range(1, 5)'''
        self.command(slave, str(axis)+'PA'+str(position))
        while True:
            time.sleep(0.05)
            if self.command(slave, str(axis)+'MD?'):
                break
        return float(self.command(slave, str(axis)+'PA?'))

    def getPos(self, slave, axis):
        return float(self.command(slave, str(axis)+'PA?'))

    def move(self, slave, axis, relative):
        self.command(slave, f'{axis}PR{relative}')
        while True:
            time.sleep(0.1)
            if self.command(slave, str(axis)+'MD?'):
                break
        return float(self.command(slave, str(axis)+'PR?'))
    
    def abort(self, slave):
        self.command(slave, 'AB')
    
    def stop(self, slave, axis):
        self.command(slave, str(axis)+'ST')
    
    def reset(self, slave):
        self.command(slave, '*RST')

    def start_console(self):
        """Continuously ask user for a command
        """
        print('''
        Picomotor Command Line
        ---------------------------
        Enter a valid NewFocus command, or 'quit' to exit the program.
        Common Commands:
            xMV[+-]: .....Indefinitely move motor 'x' in + or - direction
                 ST: .....Stop all motor movement
              xPRnn: .....Move motor 'x' 'nn' steps
        \n
        ''')

        while True:
            slave = input('Slave > ')
            command = input("Input > ")
            if command.lower() in ['q', 'quit', 'exit']:
                break
            else:
                rep = self.command(slave, command)
                if rep:
                    print("Output: {}".format(rep))


class Axis(GroupCtrl):
    def __init__(self, slave, axis, name, stage):
        super().__init__(name)
        self.slave = slave
        self.device = stage
        self.axis = axis
        
        self.relative = LVNumCtrl('Relative')
        self.relative.setRange(-500000, 500000)
        self.relative.setDecimals(0)
        self.go = Button('Move', self.move)
        
        self.target = LVNumCtrl('Target Pos', self.setPos)
        self.target.setDecimals(0)
        self.target.setRange(-500000, 500000)
        self.actual = LVNumCtrl('Actual Pos')
        self.actual.setDecimals(0)
        self.actual.setRange(-500000, 500000)
        self.actual.setReadOnly(True)
        position = self.device.getPos(slave, axis)
        self.target.setValue(position)
        self.actual.setValue(position)
        self.stop = Button("Stop", self.stopMotion)
        self.read = Button("Read", self.readPos)
        self.motor = ButtonCtrl("Motor", self.setMotor)

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
        
    def setPos(self, value):
        position = self.device.setPos(self.slave, self.axis, int(value))
        self.actual.setValue(position)

    def stopMotion(self):
        self.device.stop(self.slave, self.axis)

    def readPos(self):
        position = self.device.getPos(self.slave, self.axis)
        self.target.setValue(position)
        self.actual.setValue(position)

    def setMotor(self, state):
        if state:
            self.target.setReadOnly(False)
            self.go.setEnabled(True)
        else:
            self.target.setReadOnly(True)
            self.go.setDisabled(True)


class PicomotorCtrl(GroupCtrl):
    def __init__(self, idProduct, idVendor, names, slaves=3):
        super().__init__()
        self.dev = Controller(idProduct, idVendor, slaves)
        self.setTitle('Picomotor')
        self.axis = [None]*4*slaves
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(2, 2, 2, 2)
        for i in range(len(self.axis)):
            self.axis[i] = Axis(i//4+1, i%4+1, names[i], self.dev)
            layout.addWidget(self.axis[i], i//4, i%4, 1, 1)
        self.setLayout(layout)


class Window(Widget):
    def __init__(self, idProduct, idVendor):
        super().__init__()
        # self.setWindowIcon(QIcon("esp.jpg"))
        names = ('EIT Focus', 'EIT H', 'EIT V', 'Raman',
                 'Raman', 'Raman', 'Raman', 'Raman', 'Raman', 'Raman', 'Raman', 'Raman')
        self.stage = PicomotorCtrl(idProduct, idVendor, names, 3)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.addWidget(self.stage)
        self.setWindowTitle("Picomotor")
        self.show()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

if __name__ == '__main__':
    # print('\n\n')
    # print('#'*80)
    # print('#\tPython controller for NewFocus Picomotor Controller')
    # print('#'*80)
    # print('\n')

    # idProduct = None  # '0x4000'
    # idVendor = None  # '0x104d'

    # if not (idProduct or idVendor):
    #     print('Run the following command in a new terminal window:')
    #     print('\t$ system_profiler SPUSBDataType\n')
    #     print('Enter Product ID:')
    #     idProduct = input('> ')
    #     print('Enter Vendor ID:')
    #     idVendor = input('> ')
    #     print('\n')

    # # convert hex value in string to hex value
    # idProduct = int(idProduct, 16)
    # idVendor = int(idVendor, 16)

    # # Initialize controller and start console
    # controller = Controller(idProduct=idProduct, idVendor=idVendor, slaves=2)
    # controller.start_console()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = Window(0x4000, 0x104D)
    window.center()
    sys.exit(app.exec_())
