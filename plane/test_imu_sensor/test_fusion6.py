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

i2c = I2C(1, sda=Pin(14), scl=Pin(15))
i2c2 = I2C(0, sda=Pin(0), scl=Pin(1))
imu = MPU6050(i2c)


oled = SSD1306_I2C(width=128, height=64, i2c=i2c2, addr=0x3C)

fuse = Fusion()

# Choose test to run
Timing = True

if Timing:
    accel = imu.accel.xyz
    gyro = imu.gyro.xyz
    start = time.ticks_us()  # Measure computation time only
    fuse.update_nomag(accel, gyro) # 979μs on Pyboard
    t = time.ticks_diff(time.ticks_us(), start)
    print("Update time (uS):", t)

count = 0
while True:
    fuse.update_nomag(imu.accel.xyz, imu.gyro.xyz)
    if count % 5 == 0:
        print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format(fuse.heading, fuse.pitch, fuse.roll), end="\r")
        oled.fill(0)
        oled.text("H:{:7.2f}".format(fuse.heading), 0, 0)
        oled.text("P:{:7.2f}".format(fuse.pitch), 0, 16)
        oled.text("R:{:7.2f}".format(fuse.roll), 0, 32)
        oled.show()
    time.sleep_ms(20)
    count += 1