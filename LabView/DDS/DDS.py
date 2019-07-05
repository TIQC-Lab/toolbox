import sys
from PyQt4 import QtCore, QtGui, QtNetwork
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from AD9910 import ad9910

# ID start from START
START = 6
config = [
        ['Horn',0.5,(0,0,0),(170.4,0.5,0),(170.7,0.5,0),(0,0,0),(173.045,0.5,0)],
        ['Raman',1,(200,1,0)],
        ['Horn2',0.5,(193.027,0.1,0),(193.027,0.1,0.5)],
        ]
for i in range(len(config)):
    config[i] += [(0,0,0)]*(10-len(config[i]))
    
PORT = 9999
        
dds = ad9910()

class LVSpinBox(QDoubleSpinBox):
    stepChanged = QtCore.pyqtSignal()

    def stepBy(self, step):
        value = self.value()
        digit = str(self.text()).find('.') - self.lineEdit().cursorPosition()
        if digit < 0:
            digit += 1
        self.setValue(value + step*(10**digit))
        if self.value() != value:
            self.stepChanged.emit()

    def onValueChanged(self,func):
        self.editingFinished.connect(func)
        self.stepChanged.connect(func)

class LVNumCtrl:
    def __init__(self, parent = None):
        if isinstance(parent, QLayout):
            self.hbox = QHBoxLayout()
            parent.addLayout(self.hbox)
        else:
            self.hbox = QHBoxLayout(parent)
        self.label = QLabel()
        self.spin = LVSpinBox()
        
        self.label.setFont(QFont("Microsoft YaHei", 14))
        self.spin.setFont(QFont("Microsoft YaHei", 16))
        
        self.hbox.addWidget(self.label)
        self.hbox.addWidget(self.spin)

    def setLabel(self, text):
        self.label.setText(text)

    def value(self):
        return self.spin.value()

    def setValue(self, val):
        self.spin.setValue(val)

class DDSCtrl:
    def __init__(self, parent = None):
        self.group = QGroupBox(parent)
        self.group.setFont(QFont("Microsoft YaHei", 12))
        
        self.vbox = QVBoxLayout(self.group)
        self.freq = LVNumCtrl(self.vbox)
        
        self.hbox0 = QHBoxLayout()
        self.amp = LVNumCtrl(self.hbox0)
        self.pll = QCheckBox('PLL',self.group)
        self.pll.setLayoutDirection(Qt.RightToLeft)
        self.pll.setFont(QFont("Microsoft YaHei", 12))
        self.hbox0.addWidget(self.pll)
        self.vbox.addLayout(self.hbox0)
        
        self.hbox1 = QHBoxLayout()
        self.phase = LVNumCtrl(self.hbox1)
        self.profile = QComboBox(self.group)
        self.profile.addItems([str(i) for i in range(8)])
        self.hbox1.addWidget(self.profile)
        self.vbox.addLayout(self.hbox1)
        
        self.freq.setLabel('Freq')
        #self.freq.spin.setSuffix(' MHz')
        self.freq.spin.setDecimals(4)
        self.freq.spin.setRange(0,1000)
        self.freq.spin.onValueChanged(self.setFreq)

        self.amp.setLabel('Amp')
        self.amp.spin.setRange(0,1)
        self.amp.spin.onValueChanged(self.setAmp)
        
        self.phase.setLabel('Phase')
        self.phase.spin.setRange(0,2)
        self.phase.spin.onValueChanged(self.setPhase)
        
        self.profile.currentIndexChanged.connect(self.changeProfile)
        
        self.dut = None
        self.timer = None
    
    def setLabel(self, text):
        self.group.setTitle(text)
    
    def setEnabled(self, state):
        self.group.setEnabled(state)
        if state:
            self.timer = QTimer()
            self.timer.timeout.connect(self.checkPLL)
            self.timer.start(1000)
        elif self.timer != None:
            self.timer.stop()
    
    def setMaxAmp(self, amp):
        self.amp.spin.setRange(0,amp)
        
    def setID(self, dut):
        self.dut = dut
    
    def setProfile(self):
        profile = int(self.profile.currentText())
        freq = self.freq.value()
        amp = self.amp.value()
        phase = self.phase.value()
        config[self.dut - START][profile + 2] = (freq,amp,phase)
        dds.parameter(self.dut, 1e6*freq, amp, phase, profile)
        #dds.change_profile(self.dut, profile)
        
    def setFreq(self, freq = None):
        if freq == None:
            freq = self.freq.value()
        else:
            self.freq.setValue(freq)
        self.setProfile()

    def setAmp(self, amp = None):
        if amp == None:
            amp = self.amp.value()
        else:
            self.amp.setValue(amp)
        self.setProfile()
    
    def setPhase(self, phase = None):
        if phase == None:
            phase = self.phase.value()
        else:
            self.phase.setValue(phase)
        self.setProfile()
        
    def checkPLL(self):
        state = dds.pll_lock(self.dut)
        self.pll.setCheckState(state)
        if not state:
            dds.ConfigPort(self.dut)
            self.setProfile()
    
    def changeProfile(self, profile = None):
        if profile == None:
            profile = int(self.profile.currentText())
        else:
            self.profile.setCurrentIndex(profile)
        freq,amp,phase = config[self.dut - START][profile + 2]
        #freq,amp,phase = dds.parameter(self.dut, profile = profile)
        #print(freq,amp,phase)
        self.freq.setValue(freq)
        self.amp.setValue(amp)
        self.phase.setValue(phase)
        self.setProfile()        
            
class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('DDS')
        
        self.box = QVBoxLayout()
        self.setLayout(self.box)
        
        self.ctrls = QHBoxLayout()
        self.box.addLayout(self.ctrls)
        
        self.btnReload = QPushButton('Reload')
        self.btnReload.setFont(QFont("Microsoft YaHei", 12))
        self.ctrls.addWidget(self.btnReload)
        
        self.dds = []
        for i in range(len(config)):
            self.dds.append(DDSCtrl(self))
            self.dds[i].setLabel(config[i][0])
            self.dds[i].setMaxAmp(config[i][1])
            self.box.addWidget(self.dds[i].group)
            
        self.btnReload.clicked.connect(self.reload)
        self.server = QTcpServer()
        self.server.listen(QHostAddress("0.0.0.0"), PORT)
        self.server.newConnection.connect(self.accept)
        self.clients = []
    
    def reload(self):
        dds.reload()
        for i in range(len(config)):
            self.dds[i].setEnabled(False)
        for k in dds._handle:
            i = k - START
            self.dds[i].setID(k)
            profile = int(self.dds[i].profile.currentText())
            for j in range(START,len(config[i])):
                self.dds[i].changeProfile(j - START)
            self.dds[i].changeProfile(profile)
            self.dds[i].setEnabled(True)
    
    def accept(self):
        client = self.server.nextPendingConnection()
        self.clients.append(client)
        client.readyRead.connect(self.receive)
        client.disconnected.connect(self.close)
    
    def receive(self):
        for c in self.clients:
            if c.bytesAvailable() > 0:
                s = str(c.readAll()).split()
                cmd = s[0]
                dds = self.dds[int(s[1]) - START]
                if cmd.endswith('?'):
                    val = 0
                    if cmd.startswith('FREQ'):
                        val = dds.freq.value()
                    elif cmd.startswith('AMP'):
                        val = dds.amp.value()
                    elif cmd.startswith('PHASE'):
                        val = dds.phase.value()
                    elif cmd.startswith('PROFILE'):
                        val = int(dds.profile.currentText())
                    c.write('{0}\r\n'.format(val,'%lf'))
                elif cmd.startswith('FREQ'):
                    dds.setFreq(float(s[2]))
                elif cmd.startswith('AMP'):
                    dds.setAmp(float(s[2]))
                elif cmd.startswith('PHASE'):
                    dds.setPhase(float(s[2]))
                elif cmd.startswith('PROFILE'):
                    dds.changeProfile(int(s[2]))
    
    def close(self):
        for c in self.clients:
            if c.state() == 0:
                self.clients.remove(c)
                
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    window.reload()
    sys.exit(app.exec_())