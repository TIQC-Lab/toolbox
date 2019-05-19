<<<<<<< HEAD

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
=======

import serial

if __name__ == "__main__":
    ps = serial.Serial()
    ps.baudrate = 9600
    ps.port = "COM17"
    ps.timeout = 0.01
    ps.open()
    print(ps.is_open)
    if(ps.open):
        ps.write(b"SYSTEM:INTERFACE RS232\r")
        ps.write(b"system:remote\r")
        ps.write(b"source:voltage 1.0\r")
        ps.write(b"source:current 1.1\r")
        ps.write(b"OUTPUT off\r")
>>>>>>> e053c279b0795550de400633c243b13a7367e24a
