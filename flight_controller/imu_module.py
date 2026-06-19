from machine import Pin, I2C
import utime as time
from lib.imu import MPU6050  
from lib.fusion import Fusion 
import lib.bmp085 as bmp085
from lib.QMC5883L import QMC5883L


imu_sensor = None
mag_sensor = None
fusion = None
bmp = None

baseline = 0.0
relative_altitude = 0.0
_alt_counter = 0

start_cal_time = 0
mag_calibrated = False

def setup():
    global imu_sensor, mag_sensor, fusion, bmp, baseline, start_cal_time, mag_calibrated, _alt_counter, relative_altitude
    
    i2c = I2C(1, sda=Pin(14), scl=Pin(15))
    imu_sensor = MPU6050(i2c)
    mag_sensor = QMC5883L(i2c)

    fusion = Fusion()

    # calibrate magnetometer
    mag_calibrated = False
    calibrate_mag()  

    # BMP180 setup
    bmp = bmp085.BMP180(i2c)
    bmp.sealevel = 1016.0
    bmp.oversample = 2
    _alt_counter = 0
    relative_altitude = 0.0

    baseline:float = 0.0
    for i in range(0, 5):   
        baseline = baseline + bmp.altitude
        time.sleep(0.1)
    baseline = baseline / 5
    print("Baseline altitutde: " + str(baseline) + " meters")

def auto_stop():
    global start_cal_time
    return time.ticks_diff(time.ticks_ms(), start_cal_time) > 20000

def get_mag():
    global mag_sensor
    return mag_sensor.measure()

def calibrate_mag():
    global fusion, start_cal_time, mag_calibrated, imu_sensor, mag_sensor
    accel = imu_sensor.accel.xyz
    gyro = imu_sensor.gyro.xyz
    fusion.calibrate(get_mag, auto_stop, 100)
    fusion.update(accel, gyro, mag_sensor.measure())
    mag_calibrated = True
    print("Calibration complete.")

def update():
    global imu_sensor, mag_sensor, fusion, mag_calibrated, _alt_counter
    
    # 
    if mag_calibrated:
        fusion.update(imu_sensor.accel.xyz, imu_sensor.gyro.xyz, mag_sensor.measure())
    else:
        fusion.update_nomag(imu_sensor.accel.xyz, imu_sensor.gyro.xyz)

    # 
    _alt_counter += 1
    if _alt_counter % 5 == 0:   # ~20 Hz
        global relative_altitude, baseline, bmp
        relative_altitude = (relative_altitude * 0.9) + ((bmp.altitude - baseline) * 0.1)
        _alt_counter = 0





