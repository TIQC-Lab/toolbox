from toptica.lasersdk.dlcpro.v2_2_0 import DLCpro, NetworkConnection, DeviceNotFoundError, DecopError, UserLevel


class TopticaLaser(object):
    '''Class for toptica laser with DLC pro controller using the official lasersdk'''

    def __init__(self, ip):
        self.ip = ip
        try:
            self.dlc = DLCpro(NetworkConnection(self.ip))
        except DeviceNotFoundError:
            print('Device not found!')
        self.dlc.__enter__()
        # print(ip)

    def get_voltage_set(self):
        return(self.dlc.laser1.dl.pc.voltage_set.get())
        
    def get_current_set(self):
        return(self.dlc.laser1.dl.cc.current_set.get())

    def get_voltage_act(self):
        return(self.dlc.laser1.dl.pc.voltage_act.get())

    def get_current_act(self):
        return(self.dlc.laser1.dl.cc.current_act.get())

    def get_max_current(self):
        return(self.dlc.laser1.dl.cc.current_clip.get())

    def get_status(self):
        return(self.dlc.emission.get())

    def set_voltage(self, value):
        self.dlc.laser1.dl.pc.voltage_set.set(float(value))

    def set_current(self, value):
        self.dlc.laser1.dl.cc.current_set.set(float(value))

    def userLevel(self):
        return(self.dlc.ul.get())

    def enable_emission(self, status):
        try:
            if status:
                self.dlc.laser1.dl.cc.enabled.set(True)
            else:
                self.dlc.laser1.dl.cc.enabled.set(False)
        except DecopError as error:
            print(error)
            
    def close(self):
        self.dlc.__exit__()

    def __del__(self):
        self.dlc.__exit__()
        # print(self.ip)


if __name__ == '__main__':
    laser = TopticaLaser("192.168.32.7")
    laser.enable_emission(True)
    print(laser.userLevel())
    print(laser.get_voltage_act())
    print(laser.get_max_current())
    laser.enable_emission(True)
    print(laser.get_status())
