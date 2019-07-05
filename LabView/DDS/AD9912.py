import sys, time
from ctypes import *

def int2arr(val,length):
    arr = []
    for i in range(length):
        mask=0xFF<<(8*i)
        arr.append(int((val&mask)>>(8*i)))
    return arr

def arr2int(arr):
    val = 0
    for i in range(len(arr)):
        val |= arr[i] << (8*i)
    return val

class ad9912():
    _dll=windll.adiclockeval
    _portConfig=[0x7F,0xFF,0x00,0xFF]
    _portLookUp={'a':0,'b':1,'c':2,'d':3,'e':4,0:0,1:1,2:2,3:3,4:4}
    _vid = 0x0456
    _pid = 0xEE25
    _handle = []
    _fs = 25000000

    def __init__(self,reset=None):
        self.FindHardware()
        self.GetHandle()
        self.IsReady()
        self.ConfigPorts()
        if reset:
            for dut in range(self._NUMduts):
                self.reset(dut)
        pass

    def reset(self,dut=1):
        self.SetPortValue('a',0x7,dut)
        time.sleep(0.01)
        self.SetPortValue('a',0x3,dut)
        time.sleep(0.3)
        pass
    
    def FindHardware(self):
        vidArry=c_int*1
        pidArry=c_int*1
        vid=vidArry(self._vid)
        pid=pidArry(self._pid)
        length=c_int(1)
        hard_instances=self._dll.FindHardware(byref(vid),byref(pid),length)
        if hard_instances == 0:
            raise RuntimeError("AD9912 instance not found!")
        else: self._NUMduts=hard_instances
        pass
    
    def GetHandle(self):
        handleArry=c_int*self._NUMduts
        handle=handleArry(0)
        self._dll.GetHardwareHandles(byref(handle))
        for dut in range(self._NUMduts):
            self._handle.append(c_int(handle[dut]))
        pass
    
    def IsReady(self):
        for dut in range(self._NUMduts):
            ready=self._dll.IsConnected(self._handle[dut])
            if ready != 1:
                raise RuntimeError("AD9912 USB not ready!")
        pass
    
    def ConfigPorts(self):
        for dut in range(self._NUMduts):
            for index in [0,1,2,3]:
                port=c_int(index)
                config=c_ubyte(self._portConfig[index])
                self._dll.SetPortConfig(self._handle[dut],port,config)
        pass
    
    def GetPortValue(self,port,dut=1):
        port=c_int(self._portLookUp[port])
        value=c_ubyte(0x00)
        self._dll.GetPortValue(self._handle[dut-1],port,byref(value))
        return value.value
    
    def SetPortValue(self,port,value,dut=1):
        port=c_int(self._portLookUp[port])
        value=c_ubyte(value)
        self._dll.SetPortValue(self._handle[dut-1],port,value)
        pass

    @staticmethod
    def instruction(rw,reg,length):
        if length > 3:
            instr = 3 << 13
        else:
            instr = (length - 1) << 13
        instr |= rw << 15
        instr |= reg & 0x7FF
        return instr
          
    def write(self,reg,data,length=None,dut=1):
        if type(data) == type([]): length = len(data)
        #addr=c_int(reg)
        #instructionLen=c_int(2)
        #instruction=c_ushort(0x00)
        #rw=c_int(0)
        #self._dll.GetSpiInstruction(rw,addr,length,byref(instruction),instructionLen)
        instr=self.instruction(0,reg,length)
        writeDataArry=c_ubyte*(length+2)
        writeData=writeDataArry(0)
        writeLen=c_int(length+2)
        writeData[length]=instr&0xFF
        writeData[length+1]=instr>>8
        if type(data)==type([]):
            for i in range(length):
                writeData[i]=data[i]
        else:
            data=int(data)
            for i in range(length):
                mask=0xFF<<(8*i)
                writeData[i]=(data&mask)>>(8*i)
        self._dll.SpiWrite(self._handle[dut-1],byref(writeData),writeLen)
        if reg != 0x5: self.update(dut)
        pass
    
    def update(self,dut=1):
        self.write(0x5,[0xFF],None,dut)
        pass
    
    def read(self,reg,length,dut=1):
        returnData=[]
        #addr=c_int(reg)
        #instructionLen=c_int(2)
        #instruction=c_ushort(0x00)
        #rw=c_int(1)
        #self._dll.GetSpiInstruction(rw,addr,length,byref(instruction),instructionLen)
        instr = self.instruction(1,reg,length)
        writeDataArry=c_ushort*1
        writeData=writeDataArry(0)
        writeData[0]=instr #instruction.value
        writeLen=c_int(2)
        readDataArry=c_ubyte*(length)
        readData=readDataArry(0)
        readLen=c_int(length)
        fourwire=c_int(0)
        self._dll.SpiRead(self._handle[dut-1],byref(writeData),writeLen,byref(readData),readLen,fourwire)
        for i in range(len(readData)):
            returnData.append(readData[i])
        return returnData

    def part_id(self,dut=1):
        return arr2int(self.read(0x03,2,dut))

    def frequency(self, freq=None, dut=1):
        reg = 0x1AB
        if freq == None:
            FTW = arr2int(self.read(reg,6,dut))
            return (FTW / float(281474976710656)) * self._fs
        else:
            FTW = 281474976710656 * (freq / float(self._fs))
            self.write(reg,FTW,6,dut)
        pass

if __name__ == '__main__':
    #dds=ad9912(reset=True)
    dds=ad9912()
    print(dds.part_id())
    print(dds.frequency())
    dds.write(0x1AB,[0x33,0x33,0x33,0x33,0x33,0x33])
    time.sleep(0.01)
    print(dds.frequency())
    dds.frequency(6e6)
    time.sleep(0.01)
    print(dds.read(0x1AB,6))
    print(dds.frequency())
