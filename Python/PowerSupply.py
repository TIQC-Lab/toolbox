
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
