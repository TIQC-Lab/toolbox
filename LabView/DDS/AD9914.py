import sys, time
from ctypes import *

class ad9914():
    _dll=windll.adiddseval
    _portConfig=[0x7F,0xFF,0x00,0xFF]
    _portLookUp={'a':0,'b':1,'c':2,'d':3,'e':4,0:0,1:1,2:2,3:3,4:4}

    def __init__(self,reset=None):
        self.FindHardware()
        self.GetHandle()
        self.IsReady()
        self.ConfigPorts()
        if reset:
            for dut in range(self._NUMduts):
                self.reset(ss,dut)
        pass

    def reset(self,ss=0,dut=1):
        self.SetPortValue('a',0x7,dut)
        time.sleep(0.01)
        self.SetPortValue('a',0x3,dut)
        time.sleep(0.3)
        if ss:
            SSauce=self.GetSSload(ss)
            for (reg,arry) in SSauce:
                self.write(reg,arry,1)
        pass

    def FindHardware(self):
        vidArry=c_int*1
        pidArry=c_int*1
        vid=vidArry(self._vid)
        pid=pidArry(self._pid)
        length=c_int(1)
        hard_instances=self._dll.FindHardware(byref(vid),byref(pid),length)
        if hard_instances == 0:
            raise RuntimeError("AD9914 instance not found!")
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
                raise RuntimeError("AD9914 USB not ready!")
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
    
    def write(self,reg=None,data=None,update=None,dut=1):
        length=4
        if reg ==0x37: update=0
        addr=c_int(reg)
        instructionLen=c_int(1)
        instruction=c_ubyte(0x00)
        rw=c_int(0)
        self._dll.GetSpiInstruction(rw,addr,byref(instruction),instructionLen)
        writeDataArry=c_ubyte*(length+1)
        writeData=writeDataArry(0)
        writeLen=c_int(length+1)
        writeData[length]=instruction.value
        fourwire=c_int(0)
        readData=self.read(reg,dut)
        if type(data)==type([]):
            time.sleep(0.01)
            if len(data)!= length: raise RuntimeError("More Data Needed!")
            for i in range(length):
                if data[i]==None: writeData[i]=readData[i]
                else: writeData[i]=data[i]
        else:
            for i in range(length):
                mask=0xFF<<(8*i)
                writeData[i]=(data&mask)>>(8*i)
        self._dll.SpiWrite(self._handle[dut-1],byref(writeData),writeLen,fourwire)
        if update:
            self.SetPortValue('b',0xF8,dut)
            time.sleep(0.01)
            self.SetPortValue('b',0xF0,dut)
            time.sleep(0.01)
        pass
    
    def IOupdate(self,dut):
        self.SetPortValue('b',0xF8,dut)
        time.sleep(0.01)
        self.SetPortValue('b',0xF0,dut)
        time.sleep(0.01)
        pass

    def read(self,reg,dut=1):
        returnData=[]
        if reg in [0x37,0x3D,0x3E]: length=self._lenLookUp[reg]
        else: length=4
        addr=c_int(reg)
        instructionLen=c_int(1)
        instruction=c_ubyte(0x00)
        rw=c_int(1)
        self._dll.GetSpiInstruction(rw,addr,byref(instruction),instructionLen)
        writeDataArry=c_ubyte*1
        writeData=writeDataArry(0)
        writeData[0]=instruction.value
        writeLen=c_int(1)
        readDataArry=c_ubyte*(length)
        readData=readDataArry(0)
        readLen=c_int(length)
        fourwire=c_int(0)
        self._dll.SpiRead(self._handle[dut-1],byref(writeData),writeLen,byref(readData),readLen,fourwire)
        for i in range(len(readData)):
            returnData.append(readData[i])
        return returnData

    def CAL(self,dut=1):
        reg03=self.read(0x03,dut)
        reg03[3]|=0x01
        self.write(0x03,reg03,1,dut)
        reg03[3]&=0xFE
        time.sleep(0.4)
        self.write(0x03,reg03,1,dut)
        time.sleep(0.1)
        pass
    
    def sync(self,dut=1,delay=0):
        reg1B=self.read(0x1B,dut)
        reg1B[0]= reg1B[0] | 0x80
        self.write(0x1B,reg1B,1)
        time.sleep(delay)
        reg1B[0]= reg1B[0] & 0x7F
        self.write(0x1B,reg1B,1)
        pass
    
    def setFTW(self, FTW=0, profile=0, dut=1):
        reg=0xB+(2*profile)
        readFTW=self.read(reg,dut)
        FTWarry=[]
        if type(FTW)==type([]):
            time.sleep(0.01)
            if len(FTW)!= 4: raise RuntimeError("More Data Needed!")
            for i in range(4):
                if FTW[i]==None: FTWarry.append(readFTW[i])
                else: FTWarry.append(FTW[i])
        else:
            for i in range(4):
                mask=0xFF<<(8*i)
                FTWarry.append(int((FTW&mask)>>(8*i)))
        self.write(reg,FTWarry,1,dut)
        pass
    
    def setAMP(self, AMP=0, profile=0, dut=1):
        reg=0xC+(2*profile)
        readAMP=self.read(reg,dut)
        AMParry=[]
        if type(AMP)==type([]):
            time.sleep(0.01)
            if len(AMP)!= 2: raise RuntimeError("More Data Needed!")
            for i in range(2):
                if AMP[i]==None: AMParry.append(readAMP[i])
                else: AMParry.append(AMP[i])
        else:
            for i in range(2):
                mask=0xFF<<(8*i)
                AMParry.append(int((AMP&mask)>>(8*i)))
        self.write(reg,AMParry,1,dut)
        pass
    
    def calcFTW(self, sysclk=4e9, DACout=500e6, profile=0, dut=1):
        reg=0xB+(2*profile)
        FTW=int(mpq(DACout,sysclk)*mpf(2**32))
        FTWarry=[]
        for i in range(4):
            mask=0xFF<<(8*i)
            FTWarry.append(int((FTW&mask)>>(8*i)))
        self.write(reg,FTWarry,1,dut)
        return hex(FTW)
    
    def setPOW(self, POW=0,profile=0,dut=1):
        reg=0xC+(2*profile)
        POWarry=self.read(reg,dut)
        if type(POW)==type([]):
            time.sleep(0.01)
            if len(POW)< 2: raise RuntimeError("More Data Needed!")
            for i in range(2):
                if POW[i]==None: POWarry[i]=(POWarry[i])
                else: POWarry[i]=(POW[i])
        else:
            for i in range(2):
                mask=0xFF<<(8*i)
                POWarry[i]=(int((POW&mask)>>(8*i)))
        self.write(reg,POWarry,1,dut)
        pass