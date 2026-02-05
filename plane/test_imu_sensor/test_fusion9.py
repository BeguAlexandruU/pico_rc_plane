# fusiontest6.py Simple test program for 6DOF sensor fusion on Pyboard
# Author Peter Hinch
# Released under the MIT License (MIT)
# Copyright (c) 2017 Peter Hinch
# V0.8 14th May 2017 Option for external switch for cal test. Make platform independent.
# V0.7 25th June 2015 Adapted for new MPU9x50 interface

from machine import Pin, I2C
import utime as time
from lib.imu import MPU6050  
from lib.ssd1306 import SSD1306_I2C
from lib.fusion import Fusion 
from lib.QMC5883L import QMC5883L

i2c = I2C(1, sda=Pin(14), scl=Pin(15))
imu = MPU6050(i2c)
qmc = QMC5883L(i2c)
qmc.initialize(mode=1, rate=200, range=8, oversampling=128)

switch = Pin(24, Pin.IN, pull=Pin.PULL_UP) # Switch to ground on Y7
def sw():
    return not switch.value()

# oled = SSD1306_I2C(width=128, height=64, i2c=i2c, addr=0x3C)

fuse = Fusion()

# Choose test to run
Calibrate = True
Timing = True

def getmag():                               # Return (x, y, z) tuple (blocking read)
    return qmc.read()

if Calibrate:
    print("Calibrating. Press switch when done.")
    fuse.calibrate(getmag, sw, 100)
    print(fuse.magbias)

if Timing:
    mag = qmc.read()
    accel = imu.accel.xyz
    gyro = imu.gyro.xyz
    start = time.ticks_us()  # Measure computation time only
    fuse.update(accel, gyro, mag) # 979μs on Pyboard
    t = time.ticks_diff(time.ticks_us(), start)
    print("Update time (uS):", t)

count = 0
while True:
    fuse.update(imu.accel.xyz, imu.gyro.xyz, qmc.read())
    if count % 5 == 0:
        print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format(fuse.heading, fuse.pitch, fuse.roll), end="\r")
        # oled.fill(0)
        # oled.text("H:{:7.2f}".format(fuse.heading), 0, 0)
        # oled.text("P:{:7.2f}".format(fuse.pitch), 0, 16)
        # oled.text("R:{:7.2f}".format(fuse.roll), 0, 32)
        # oled.show()
    time.sleep_ms(40)
    count += 1