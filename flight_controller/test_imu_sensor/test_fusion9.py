# fusiontest6.py Simple test program for 6DOF sensor fusion on Pyboard
# Author Peter Hinch
# Released under the MIT License (MIT)
# Copyright (c) 2017 Peter Hinch
# V0.8 14th May 2017 Option for external switch for cal test. Make platform independent.
# V0.7 25th June 2015 Adapted for new MPU9x50 interface

from machine import Pin, I2C
import utime as time
from lib.imu import MPU6050  
from lib.fusion import Fusion 
from lib.QMC5883L import QMC5883L

i2c = I2C(0, sda=Pin(0), scl=Pin(1))
imu = MPU6050(i2c)
qmc = QMC5883L(i2c)
#qmc.initialize(mode=1, rate=200, range=8, oversampling=128)

# --- Timer-based Calibration Setup ---
start_cal_time = 0

def auto_stop():
    # Returns True if 10,000ms (10s) have passed since start_cal_time was set
    return time.ticks_diff(time.ticks_ms(), start_cal_time) > 20000

# oled = SSD1306_I2C(width=128, height=64, i2c=i2c, addr=0x3C)

fuse = Fusion()

# Choose test to run
Calibrate = True
Timing = True

def getmag():                               # Return (x, y, z) tuple (blocking read)
    return qmc.measure()

if Calibrate:
    print("Calibrating for 10 seconds... Please rotate the sensor in all directions.")
    start_cal_time = time.ticks_ms()        # Capture the start time right before calibrating
    fuse.calibrate(getmag, auto_stop, 100)  # Uses auto_stop instead of sw
    print("Calibration complete. Magbias:")
    print(fuse.magbias)

if Timing:
    mag = qmc.measure()
    accel = imu.accel.xyz
    gyro = imu.gyro.xyz
    start = time.ticks_us()  # Measure computation time only
    fuse.update(accel, gyro, mag) # 979μs on Pyboard
    t = time.ticks_diff(time.ticks_us(), start)
    print("Update time (uS):", t)

count = 0
while True:
    fuse.update(imu.accel.xyz, imu.gyro.xyz, qmc.measure())
    
    print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format((fuse.heading-180)*-1, fuse.pitch, fuse.roll), end="\r")
    
