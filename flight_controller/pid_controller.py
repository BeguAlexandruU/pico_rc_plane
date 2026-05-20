import time
import nrf_module
import imu_module
import motor_control
import servo_control


class PID:
    def __init__(self, kp, ki, kd, output_limits=(-127, 127)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._limits = output_limits

        self.last_error = 0
        self._integral = 0
        self.last_time = time.ticks_ms()

    def reset_integral(self):
        self._integral = 0

    def compute(self, setpoint, actual):
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time) / 1000.0
        if dt <= 0: return self.last_error # Prevent division by zero

        error = setpoint - actual
        
        # Proportional
        p = self.kp * error
        
        # Integral
        self._integral += self.ki * error * dt
        self._integral = max(self._limits[0], min(self._limits[1], self._integral))
        
        # Derivative
        d = self.kd * (error - self.last_error) / dt
        
        output = p + self._integral + d
        
        # Apply limits (-127 to 127)
        output = max(self._limits[0], min(self._limits[1], output))
        
        self.last_error = error
        self.last_time = now
        return output


ROLL_SLOPE = (80 - (-80)) / (127 - (-127))
roll_pid = None
pitch_pid = None

def setup():
    global roll_pid, pitch_pid
    roll_pid = PID(kp=1.2, ki=0.2, kd=0.05, output_limits=(-127, 127))
    pitch_pid = PID(kp=1.0, ki=0.1, kd=0.05, output_limits=(-127, 127))

def map_input_to_angle(x):
    # Simplified Formula: (x - in_min) * slope + out_min
    return (x + 127) * ROLL_SLOPE - 80

def update():
    if nrf_module.fly_mode == 0:  # Stabilize Mode
        # Convert NRF Stick (-127 to 127) to Target Angle (-80 to +80 degrees)
        target_roll = map_input_to_angle(nrf_module.ch3_aileron)
        target_pitch = map_input_to_angle(nrf_module.ch4_elevator)
        
        # Get Actual Angles from IMU
        current_roll = imu_module.fusion.roll
        current_pitch = imu_module.fusion.pitch

        if abs(nrf_module.ch2_throttle) < 10:
            roll_pid.reset_integral()
            pitch_pid.reset_integral()
        
        # Compute PID correction
        # The PID returns a value in the -127 to 127 range for your servo_control
        aileron_output = roll_pid.compute(target_roll, -current_roll)
        elevator_output = pitch_pid.compute(target_pitch, current_pitch)
        
        servo_control.set_aileron(aileron_output)
        servo_control.set_elevator(-elevator_output)

        motor_control.set_throttle(nrf_module.ch2_throttle)
    else:  # Manual Mode
        servo_control.set_aileron(nrf_module.ch3_aileron)
        servo_control.set_elevator(-nrf_module.ch4_elevator)
        motor_control.set_throttle(nrf_module.ch2_throttle)

    # print(f"Target Roll: {target_roll:.1f} | Current Roll: {current_roll:.1f} | Aileron Output: {aileron_output:.1f}")



