
from machine import Pin, I2C
import utime as time
from lib.imu import MPU6050  
from lib.fusion import Fusion 
import lib.bmp085 as bmp085


imu_sensor = None
fusion = None
bmp = None

def setup():
    global imu_sensor, fusion, bmp
    
    i2c = I2C(1, sda=Pin(14), scl=Pin(15))
    imu_sensor = MPU6050(i2c)

    fusion = Fusion()

    bmp = bmp085.BMP180(i2c)
    bmp.sealevel = 1016.0
    bmp.oversample = 2

    # debug timing test
    accel = imu_sensor.accel.xyz
    gyro = imu_sensor.gyro.xyz
    start = time.ticks_us()  # Measure computation time only
    fusion.update_nomag(accel, gyro) # 979μs on Pyboard
    t = time.ticks_diff(time.ticks_us(), start)
    print("Update time (uS):", t)

def update():
    global imu_sensor, fusion
    
    fusion.update_nomag(imu_sensor.accel.xyz, imu_sensor.gyro.xyz)
    
    
# count = 0
# while True:
#     update()
#     if count % 5 == 0:
#         print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format(fusion.heading, fusion.pitch, fusion.roll), end="\r")
#         # oled.fill(0)
#         # oled.text("H:{:7.2f}".format(fusion.heading), 0, 0)
#         # oled.text("P:{:7.2f}".format(fusion.pitch), 0, 16)
#         # oled.text("R:{:7.2f}".format(fusion.roll), 0, 32)
#         # oled.show()
#     time.sleep_ms(20)
#     count += 1