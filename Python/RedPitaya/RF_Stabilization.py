import time
from pyrpl import Pyrpl
from matplotlib import pyplot as plt

HOSTNAME = "192.168.32.24"
CONFIG = "RF_Stabilization"

p = Pyrpl(config=CONFIG, hostname=HOSTNAME)
r = p.rp

print(r.pid0.help())
