from machine import Pin, I2C
from imu import MPU6050
from time import sleep
import math as np

# Initialize LED
LED = machine.Pin("LED", machine.Pin.OUT)
LED.on()

# Initialize I2C
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)

# Scan for I2C devices
print("Scanning I2C bus...")
devices = i2c.scan()
if not devices:
    print("No I2C devices found!")
    LED.off()  # Indicate error
    while True: pass  # Halt
else:
    print("I2C devices found:", [hex(d) for d in devices]) # '0xd', '0x68', '0x77'

try:
    imu = MPU6050(i2c)
    print("MPU6050 initialized successfully!")
    LED.off()
    
    while True:
        ax = round(imu.accel.x, 2)
        ay = round(imu.accel.y, 2)
        az = round(imu.accel.z, 2)
        gx = round(imu.gyro.x)
        gy = round(imu.gyro.y)
        gz = round(imu.gyro.z)
        tem = round(imu.temperature, 2)
        #print("ax: ", ax, "ay: ", ay , "az: ", az )
        # print("gx: ", gx, "gy:W ", gy , "gz: ", gz )
        #print(f"ax:{ax}\tay:{ay}\taz:{az}\tgx:{gx}\tgy:{gy}\tgz:{gz}\tTemp:{tem}", end="\r")
        
         
        roll = np.atan2(ay, np.sqrt(ax**2 + az**2)) # or np.arcsin(ay)
        pitch = np.atan2(-ax, az)
        #yaw = np.arctan2(mx*np.cos(pitch) + mz*np.sin(pitch), mx*np.sin(pitch)*np.sin(roll) + my*np.cos(roll) - mz*np.cos(pitch)*np.sin(roll))
        
        print(f"Pitch: {np.degrees(pitch):.2f}°, Roll: {np.degrees(roll):.2f}°")

        sleep(0.1)
        
except Exception as e:
    print("Error initializing MPU6050:", e)
    LED.off()  # Indicate error
    while True: pass  # Halt


