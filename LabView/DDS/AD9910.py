import sys, time
from ctypes import *

def chunks(seq, n):
    return (seq[i:i+n] for i in xrange(0, len(seq), n))

def bits2byte(bits):
    out = 0
    for bit in bits:
        out = (out << 1) | bit
    return out

def byte2bits(byte):
    return [int(x) for x in list('{0:08b}'.format(byte))]

def int2arr(val,length):
    val = int(val+0.5)
    arr = []
    for i in range(length):
        mask=0xFF<<(8*i)
        arr.append(int((val&mask)>>(8*i)))
    return arr[::-1]

def arr2int(arr):
    arr = arr[::-1]
    val = 0
    for i in range(len(arr)):
        val |= arr[i] << (8*i)
    return val
    
class ad9910:
    _dll=windll.adiclockeval
    _portValue = [0x02, 0x00, 0x03, 0x00, 0x80]
    _portConfig = [0xFF, 0x00, 0xFF, 0x00, 0xFF]
    _regSize = [32, 32, 32, 32, 32, 48, 48, 32, 16, 32, 32, 64, 64, 32, 64, 64, 64, 64, 64, 64, 64, 64, 32, 0, 0, 0, 0, 0, 0, 0, 0, 40]
    _vid = 0x0456
    _pid = 0xEE25
    _fs = 1000000000

    def __init__(self,reload=False):
        if reload:
            reload()
    
    def reload(self):
        self._handle = {}
        self.FindHardware()
        self.GetHandle()
        self.IsReady()
        self.ConfigPorts()       
        for dut in range(self._NUMduts):
            self.reset(dut)

    def reset(self,dut):
        #self.SetPortValue('a',0x7,dut)
        #time.sleep(0.01)
        #self.SetPortValue('a',0x3,dut)
        #time.sleep(0.3)
        pass
    
    def FindHardware(self):
        vidArry=c_int*1
        pidArry=c_int*1
        vid=vidArry(self._vid)
        pid=pidArry(self._pid)
        length=c_int(1)
        hard_instances = self._dll.FindHardware(byref(vid),byref(pid),length)
        if hard_instances == 0:
            raise RuntimeError("AD9910 instance not found!")
        else:
            self._NUMduts = hard_instances
            #print(self._dll.GetHardwareCount())
    
    def GetHandle(self):
        handleArry=c_int*self._NUMduts
        handle=handleArry(0)
        self._dll.GetHardwareHandles(byref(handle))
        for dut in range(self._NUMduts):
            #print(map(lambda x: '%04X' % x,  (self._dll.GetVendorID(handle[dut]),self._dll.GetProductID(handle[dut]))))
            infoLen = c_int(22)
            infoArry=c_ubyte*22
            info=infoArry(0)
            self._dll.GetEvbdInfo(handle[dut], byref(info), byref(infoLen))
            print 'ID =',256*info[2]+info[1]
            #hostID = c_int(1)
            #self._dll.GetHostID(handle[dut], byref(hostID))
            #print(hostID)
            boardID = ''.join(['%02X' % x for x in info[10:2:-1]])
            if '0000000000AD9910' == boardID:
                self._handle[256*info[2]+info[1]] = c_int(handle[dut])
                major = c_int(0)
                minor = c_int(0)
                self._dll.GetFirmwareVersion(handle[dut], byref(major), byref(minor))
                #print(major, minor)
                self._dll.SetCtlValue(handle[dut], 3)
    
    def IsReady(self):
        for dut in self._handle:
            ready=self._dll.IsConnected(self._handle[dut])
            if ready != 1:
                raise RuntimeError("AD9910 USB not ready")
            else:
                self._dll.DownloadFirmware(self._handle[dut], 'AD9910FWNR.hex')
    
    def ConfigPort(self,dut=1):
        for index in range(5):
            port=c_int(index)
            value = c_ubyte(self._portValue[index])
            self._dll.SetPortValue(self._handle[dut],port,value)
            config = c_ubyte(self._portConfig[index])
            self._dll.SetPortConfig(self._handle[dut],port,config)
        self._dll.SetHostID(self._handle[dut], id(self))
        
        #self._dll.SetLedBlink(self._handle[dut],1)
        #print(self._dll.GetLedBlink(self._handle[dut]))
        
        #self._dll.SetPortValue(self._handle[dut],0,0x02)
        #self._dll.SetPortValue(self._handle[dut],4,0x80)
        #self._dll.SetPortValue(self._handle[dut],0,0x0A)
        #self._dll.SetPortValue(self._handle[dut],4,0x80)
        #self._dll.SetPortValue(self._handle[dut],0,0x02)
        
        #self._dll.SetPortValue(self._handle[dut],0,0x02)
        #self._dll.SetPortValue(self._handle[dut],2,0x03)
        #self._dll.SetPortValue(self._handle[dut],2,0x23)
        #self._dll.SetPortValue(self._handle[dut],2,0x00)
        #self._dll.SetPortValue(self._handle[dut],2,0x10)
        #self._dll.SetPortValue(self._handle[dut],2,0x00)
        #self._dll.SetPortValue(self._handle[dut],2,0x03)
        
        self.write(dut,0,[0x00,0x00,0x00,0x00])
        self.write(dut,1,[0x01,0x40,0x08,0x20])
        self.write(dut,2,[0x1D,0x3F,0x41,0xC8])
        self.write(dut,3,[0x00,0x00,0x00,0x7F])
            
    def ConfigPorts(self):
        for dut in self._handle:
            self.ConfigPort(dut)
    
    def pll_lock(self,dut=1):
        value = c_ubyte(0)
        self._dll.GetPortValue(self._handle[dut],3,byref(value))
        return bool(value.value & 64)
        
    @staticmethod
    def instruction(rw,reg):
        instr = [rw, 0, 0] + [int(x) for x in list('{0:05b}'.format(reg))]     
        return instr
    
    def write(self,dut,reg,data):
        self._dll.SetAutoCSB(self._handle[dut],0)
        self._dll.SetCtlValue(self._handle[dut],2)
        self._dll.SetPortValue(self._handle[dut],0,0x00)
        instr = self.instruction(0,reg)
        for i in data:
            instr += byte2bits(i)
        #print ' '.join(['%02X' % bits2byte(x) for x in chunks(instr,8)])
        writeDataArry = c_ushort*len(instr)
        writeData = writeDataArry(0)
        for i in range(len(instr)):
            writeData[i] = instr[i]
        writeLen=c_int(2*len(instr))
        self._dll.WriteParallelData(self._handle[dut],byref(writeData),writeLen)
        self._dll.SetAutoCSB(self._handle[dut],1)
        self._dll.SetPortValue(self._handle[dut],0,0x02)
        if reg > 0xD:
            self.update(dut)
    
    def update(self,dut=0):
        self._dll.SetPortValue(self._handle[dut],4,0x90)
        self._dll.SetPortValue(self._handle[dut],4,0x80)
    
    def read(self,dut,reg):
        self._dll.SetAutoCSB(self._handle[dut],0)
        self._dll.SetCtlValue(self._handle[dut],2)
        self._dll.SetPortValue(self._handle[dut],0,0x00)
        returnData=[]
        instr = self.instruction(1,reg)
        writeDataArry = c_ushort*8
        writeData = writeDataArry(0)
        for i in range(8):
            writeData[i] = instr[i]
        writeLen=c_int(16)
        readDataArry=c_ubyte*(2*self._regSize[reg])
        readData=readDataArry(0)
        readLen=c_int(2*self._regSize[reg])
        self._dll.WriteParallelData(self._handle[dut],byref(writeData),writeLen)
        self._dll.ReadParallelData(self._handle[dut],byref(readData),readLen)
        returnData = [bits2byte(x) for x in chunks(readData[0:-1:2], 8)]
        #print '[%02X]' % reg, ' '.join(['%02X' % x for x in returnData])
        self._dll.SetAutoCSB(self._handle[dut],1)
        self._dll.SetPortValue(self._handle[dut],0,0x02)
        return returnData
    
    def change_profile(self, dut, profile):
        value = c_ubyte(0)
        self._dll.GetPortValue(self._handle[dut],4,byref(value))
        value.value = (value.value & 0b11111000) + profile
        #print(value.value)
        self._dll.SetPortValue(self._handle[dut],4,value)
        
    def parameter(self, dut, frequency = None, amplitude = 1, phase = 0, profile = 0):
        reg = 0xE + profile
        fb = 4294967296.
        ab = 16383.
        pb = 65535.
        if frequency == None:
            param = self.read(dut,reg)
            return self._fs*(arr2int(param[4:]) / fb), arr2int(param[0:2]) / ab, 2*arr2int(param[2:4]) / pb
        else:
            param = int2arr(ab*amplitude,2) + int2arr(0.5*pb*phase,2) + int2arr(fb*frequency/float(self._fs),4)
            self.write(dut,reg,param)
            #self.change_profile(dut,profile)

if __name__ == '__main__':
    dds=ad9910(True)
    dds.parameter(2,270e6,0.3)
    dds.parameter(3,260e6,0.4)
    dds.parameter(4,270e6,0.4)
    #dds.parameter(4,180e6,0.7)
    #dds.parameter(5,200e6,1)
    #dds.parameter(6,238.462e6,1)
    