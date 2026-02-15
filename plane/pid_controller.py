import time

class PID:
    def __init__(self, kp, ki, kd, output_limits=(0, 255)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._limits = output_limits

        self.last_error = 0
        self.integral = 0
        self.last_time = time.ticks_ms()

    def compute(self, setpoint, actual):
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time) / 1000.0
        if dt <= 0: return self.last_error # Prevent division by zero

        error = setpoint - actual
        
        # Proportional
        p = self.kp * error
        
        # Integral
        self.integral += error * dt
        i = self.ki * self.integral
        
        # Derivative
        d = self.kd * (error - self.last_error) / dt
        
        output = p + i + d
        
        # Apply limits (0-255)
        output = max(self._limits[0], min(self._limits[1], output))
        
        self.last_error = error
        self.last_time = now
        return output