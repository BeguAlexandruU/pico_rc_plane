from lib.ssd1306 import SSD1306_I2C
import math
import time

RAD_TO_DEG = 180 / math.pi

# Variables to store the previous filtered angles
pitch_old = 0
roll_old = 0
dt = 0.01  # Time interval in seconds
alpha = 0.02  # Filter coefficient

# Calibration offsets
roll_offset = 0
pitch_offset = 0

def complementary_filter(acc_data, gyr_data):
    global pitch_old, roll_old, dt, alpha

    # Calculate angle from accelerometer data
    angle_acc_pitch = math.atan2(acc_data[0], math.sqrt(acc_data[1]**2 + acc_data[2]**2)) * RAD_TO_DEG
    angle_acc_roll = math.atan2(acc_data[1], math.sqrt(acc_data[0]**2 + acc_data[2]**2)) * RAD_TO_DEG
    

    # Integrate the gyroscope rate
    pitch_gyro_delta = gyr_data[1] * dt
    roll_gyro_delta = gyr_data[0] * dt

    # Apply the complementary filter equation
    pitch = (1 - alpha) * (pitch_old + pitch_gyro_delta) + (alpha * angle_acc_pitch)
    roll = (1 - alpha) * (roll_old + roll_gyro_delta) + (alpha * angle_acc_roll)

    # Update previous values
    pitch_old = pitch
    roll_old = roll

    return roll, pitch


def calibrate_angles(imu):
    """Set the current angles as the zero reference point"""
    global roll_offset, pitch_offset
    
    print("Calibrating... Please keep the IMU still.")
    
    old_roll = -1
    old_pitch = -1
    roll, pitch = complementary_filter((imu.accel.x, imu.accel.y, imu.accel.z), (imu.gyro.x, imu.gyro.y, imu.gyro.z))
    stilness_counter = 0
    
    while True:
        if abs(roll - old_roll) < 0.005 and abs(pitch - old_pitch) < 0.005:
            stilness_counter += 1
            if stilness_counter >= 100:  # Require 100 consecutive stable readings
                break
        old_roll = roll
        old_pitch = pitch
        roll, pitch = complementary_filter((imu.accel.x, imu.accel.y, imu.accel.z), (imu.gyro.x, imu.gyro.y, imu.gyro.z))
        sleep(dt)
    
    roll_offset = roll
    pitch_offset = pitch
    print(f"Calibration complete! Offsets - Roll: {roll_offset:.2f}, Pitch: {pitch_offset:.2f}")


def apply_calibration(roll, pitch):
    """Apply calibration offsets to the measured angles"""
    return roll - roll_offset, pitch - pitch_offset
  
  
  
from machine import Pin, I2C
from imu import MPU6050  # type: ignore
from time import sleep

# Initialize LED
LED = machine.Pin("LED", machine.Pin.OUT) # type: ignore
LED.on()

# Initialize I2C
i2c = I2C(1, sda=Pin(14), scl=Pin(15))

# Scan for I2C devices
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    print("No I2C devices found!")
    LED.off()  # Indicate error
    while True: pass  # Halt
else:
    print("I2C devices found:", [hex(d) for d in devices]) # '0xd', '0x68', '0x77'
    # Sensors on board the GY87 are:
    # MPU6050 Accelerometer.  Address is 0x68
    # HMC5883L Digital Compass.  Address is 0x1E
    # BMP180 Barometer and Temperature Sensor.  Address is 0x77


try:
    imu = MPU6050(i2c)
    # Calibrate at startup
    #calibrate_angles(imu)

    oled = SSD1306_I2C(width=128, height=64, i2c=i2c, addr=0x3C)
    
    print("MPU6050 initialized successfully!")
    LED.off()
    
    while True:
        # ax = imu.accel.x
        # ay = imu.accel.y
        # az = imu.accel.z
        # gx = imu.gyro.x
        # gy = imu.gyro.y
        # gz = imu.gyro.z
        # tem = imu.temperature
        #print("ax: ", ax, "ay: ", ay , "az: ", az )
        # print("gx: ", gx, "gy:W ", gy , "gz: ", gz )
        #print(f"ax:{ax}\tay:{ay}\taz:{az}\tgx:{gx}\tgy:{gy}\tgz:{gz}\tTemp:{tem}", end="\r")
        roll, pitch = complementary_filter((imu.accel.x, imu.accel.y, imu.accel.z), (imu.gyro.x, imu.gyro.y, imu.gyro.z))
        roll_cal, pitch_cal = apply_calibration(roll, pitch)
        oled.fill(0)
        oled.text(f"roll: {roll_cal:.2f}", 0, 0) # Add text
        oled.text(f"pitch: {pitch_cal:.2f}", 0, 10) # Add text
        oled.show()
        # print(f"roll:{roll:.2f}\tpitch:{pitch:.2f}", end="\r")
        
        sleep(dt)
        
except Exception as e:
    print("Error initializing MPU6050:", e)
    LED.off()  # Indicate error
    while True: pass  # Halt

