# imu_gy91.py
"""
Module for interfacing with the GY-91 IMU sensor (accelerometer, gyroscope, barometer) on the Raspberry Pi Pico 2W using MicroPython.
"""
from machine import I2C, Pin
from time import sleep
import math

MPU_ADDR = 0x68
MPU_PWR_MGMT_1 = 0x6B
BMP_ADDR = 0x77
BMP_TEMP_MSB = 0xFA
BMP_PRESS_MSB = 0xF7
BMP_CTRL_MEAS = 0xF4
BMP_CONFIG = 0xF5

class Madgwick:
    def __init__(self, beta=0.1):
        self.beta = beta
        self.q = [1.0, 0.0, 0.0, 0.0]

    def update(self, gx, gy, gz, ax, ay, az, dt):
        q1, q2, q3, q4 = self.q
        norm = math.sqrt(ax * ax + ay * ay + az * az)
        if norm == 0:
            return
        ax /= norm
        ay /= norm
        az /= norm
        gx = math.radians(gx)
        gy = math.radians(gy)
        gz = math.radians(gz)
        qDot1 = 0.5 * (-q2 * gx - q3 * gy - q4 * gz)
        qDot2 = 0.5 * (q1 * gx + q3 * gz - q4 * gy)
        qDot3 = 0.5 * (q1 * gy - q2 * gz + q4 * gx)
        qDot4 = 0.5 * (q1 * gz + q2 * gy - q3 * gx)
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt
        q4 += qDot4 * dt
        norm = math.sqrt(q1 * q1 + q2 * q2 + q3 * q3 + q4 * q4)
        self.q = [q1 / norm, q2 / norm, q3 / norm, q4 / norm]

    def get_euler(self):
        q1, q2, q3, q4 = self.q
        roll = math.atan2(2.0 * (q1 * q2 + q3 * q4), 1.0 - 2.0 * (q2 * q2 + q3 * q3))
        pitch = math.asin(2.0 * (q1 * q3 - q4 * q2))
        return math.degrees(pitch), math.degrees(roll)

class ComplementaryFilter:
    """
    Complementary filter for pitch and roll estimation.
    Combines accelerometer (long-term accuracy) and gyroscope (short-term stability).
    """
    def __init__(self, alpha=0.98):
        """
        Initialize complementary filter.
        
        Args:
            alpha: Filter coefficient (0-1). Higher values give more weight to gyro.
                   Typical values: 0.95-0.98
        """
        self.alpha = alpha
        self.pitch = 0.0
        self.roll = 0.0
        self.initialized = False

    def update(self, ax, ay, az, gx, gy, gz, dt):
        """
        Update filter with new sensor data.
        
        Args:
            ax, ay, az: Accelerometer data (g)
            gx, gy, gz: Gyroscope data (°/s)
            dt: Time step (seconds)
        
        Returns:
            tuple: (pitch, roll) in degrees
        """
        # Calculate accelerometer-derived angles
        accel_pitch = math.degrees(math.atan2(-ax, math.sqrt(ay**2 + az**2)))
        accel_roll = math.degrees(math.atan2(ay, az))
        
        # Integrate gyroscope data
        self.pitch += gx * dt  # gx is already in °/s
        self.roll += gy * dt   # gy is already in °/s
        
        # Initialize on first run
        if not self.initialized:
            self.pitch = accel_pitch
            self.roll = accel_roll
            self.initialized = True
            return self.pitch, self.roll
        
        # Apply complementary filter
        # High-pass filter on gyro (removes drift)
        # Low-pass filter on accel (removes noise)
        self.pitch = self.alpha * (self.pitch + gx * dt) + (1 - self.alpha) * accel_pitch
        self.roll = self.alpha * (self.roll + gy * dt) + (1 - self.alpha) * accel_roll
        
        return self.pitch, self.roll

    def reset(self):
        """Reset filter state"""
        self.pitch = 0.0
        self.roll = 0.0
        self.initialized = False

class IMUGY91:
    def __init__(self, i2c):
        self.i2c = i2c
        self.madgwick = Madgwick()
        self.complementary = ComplementaryFilter(alpha=0.98)  # Add complementary filter
        self._init_sensors()

    def _init_sensors(self):
        self.i2c.writeto_mem(MPU_ADDR, MPU_PWR_MGMT_1, b'\x00')
        self.i2c.writeto_mem(BMP_ADDR, BMP_CTRL_MEAS, b'\x27')
        self.i2c.writeto_mem(BMP_ADDR, BMP_CONFIG, b'\xA0')

    def read_word(self, addr, reg):
        data = self.i2c.readfrom_mem(addr, reg, 2)
        val = data[0] << 8 | data[1]
        return val - 65536 if val > 32767 else val

    def read_accel(self):
        ax = self.read_word(MPU_ADDR, 0x3B) / 16384.0
        ay = self.read_word(MPU_ADDR, 0x3D) / 16384.0
        az = self.read_word(MPU_ADDR, 0x3F) / 16384.0
        return ax, ay, az

    def read_gyro(self):
        gx = self.read_word(MPU_ADDR, 0x43) / 131.0
        gy = self.read_word(MPU_ADDR, 0x45) / 131.0
        gz = self.read_word(MPU_ADDR, 0x47) / 131.0
        return gx, gy, gz

    def read_bmp280(self):
        data = self.i2c.readfrom_mem(BMP_ADDR, BMP_TEMP_MSB, 3)
        temp_raw = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
        data = self.i2c.readfrom_mem(BMP_ADDR, BMP_PRESS_MSB, 3)
        press_raw = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
        temperature = temp_raw / 5120.0
        pressure = press_raw / 256.0
        return temperature, pressure

    def pressure_to_altitude(self, pressure_pa, sea_level_pa=101325.0):
        return 44330.0 * (1.0 - (pressure_pa / sea_level_pa) ** 0.1903)

    def get_orientation(self, dt):
        ax, ay, az = self.read_accel()
        gx, gy, gz = self.read_gyro()
        self.madgwick.update(gx, gy, gz, ax, ay, az, dt)
        return self.madgwick.get_euler()

    def get_orientation_complementary(self, dt):
        """
        Get orientation using complementary filter.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            tuple: (pitch, roll) in degrees
        """
        ax, ay, az = self.read_accel()
        gx, gy, gz = self.read_gyro()
        return self.complementary.update(ax, ay, az, gx, gy, gz, dt)

    def read_all(self, dt):
        ax, ay, az = self.read_accel()
        gx, gy, gz = self.read_gyro()
        temp, press = self.read_bmp280()
        alt = self.pressure_to_altitude(press)
        pitch_madgwick, roll_madgwick = self.get_orientation(dt)
        pitch_comp, roll_comp = self.get_orientation_complementary(dt)
        return {
            'ax': ax, 'ay': ay, 'az': az,
            'gx': gx, 'gy': gy, 'gz': gz,
            'temp': temp, 'press': press, 'alt': alt,
            'pitch_madgwick': pitch_madgwick, 'roll_madgwick': roll_madgwick,
            'pitch_complementary': pitch_comp, 'roll_complementary': roll_comp
        }
    

# imu_sensor/i2c_diagnostic.py
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)

imu = IMUGY91(i2c)

while True:
    data = imu.read_all(0.1)
    #print(f"Accel: ({data['ax']:.2f}, {data['ay']:.2f}, {data['az']:.2f}) g")
    #print(f"Gyro: ({data['gx']:.2f}, {data['gy']:.2f}, {data['gz']:.2f}) °/s")
    #print(f"Temp: {data['temp']:.2f} °C, Pressure: {data['press']:.2f} Pa, Altitude: {data['alt']:.2f} m")
    #print(f"Orientation: Pitch: {data['pitch']:.2f}°, Roll: {data['roll']:.2f}°")
    #print("--------------------------------------------------")
    
    imu.madgwick.update(data['gx'], data['gy'], data['gz'], data['ax'], data['ay'], data['az'], 0.1)
    pitch, roll = imu.madgwick.get_euler()
    print(f"Pitch: {pitch:.2f}°, Roll: {roll:.2f}°")
    sleep(0.1)
