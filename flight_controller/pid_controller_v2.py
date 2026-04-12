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
        self._min_out, self._max_out = output_limits

        self._integral = 0
        self._last_input = 0
        self._last_output = 0
        self._last_time = time.ticks_ms()

    def compute(self, setpoint, actual):
        now = time.ticks_ms()
        # Calculează diferența de timp corect în MicroPython
        dt = time.ticks_diff(now, self._last_time) / 1000.0
        
        # Evită diviziunea la zero sau update-uri prea rapide
        if dt <= 0.001: 
            return self._last_output

        error = setpoint - actual
        
        # 1. Proportional
        p = self.kp * error
        
        # 2. Integral cu Anti-Windup (clamping inclus)
        self._integral += self.ki * error * dt
        self._integral = max(self._min_out, min(self._max_out, self._integral))
        
        # 3. Derivative on Measurement (previne "Derivative Kick")
        # Observație: scădem d_input pentru că o creștere a valorii actuale 
        # acționează ca o frână asupra ratei de schimbare.
        d_input = actual - self._last_input
        d = -self.kd * (d_input / dt)
        
        output = p + self._integral + d
        
        # Limitare output final
        output = max(self._min_out, min(self._max_out, output))
        
        # Salvare stare pentru următorul pas
        self._last_input = actual
        self._last_output = output
        self._last_time = now
        
        return output

    def reset(self):
        self._integral = 0
        self._last_input = 0
        self._last_time = time.ticks_ms()

# Constante de mapare
# NRF trimite de obicei 0-255. Dacă ch3/ch4 sunt deja -127 la 127, ajustează formula.
IN_MIN, IN_MAX = 0, 255
OUT_MIN, OUT_MAX = -30, 30

roll_pid = None
pitch_pid = None

def setup():
    global roll_pid, pitch_pid
    # Tunings: Kp, Ki, Kd
    roll_pid = PID(kp=1.2, ki=0.5, kd=0.1, output_limits=(-127, 127))
    pitch_pid = PID(kp=1.2, ki=0.5, kd=0.1, output_limits=(-127, 127))

def map_input_to_angle(x):
    """Mapare liniară: (valoare - in_min) * (out_range / in_range) + out_min"""
    return (x - IN_MIN) * (OUT_MAX - OUT_MIN) / (IN_MAX - IN_MIN) + OUT_MIN

def update():
    # 1. Obținere Target (din Stick-uri NRF)
    # Presupunem că nrf_module.chX returnează valori 0-255
    target_roll = map_input_to_angle(nrf_module.ch3)
    target_pitch = map_input_to_angle(nrf_module.ch4)
    
    # 2. Obținere Orientare Actuală (din IMU)
    current_roll = imu_module.fusion.roll
    current_pitch = imu_module.fusion.pitch
    
    # 3. Calcul PID
    aileron_cmd = roll_pid.compute(target_roll, current_roll)
    elevator_cmd = pitch_pid.compute(target_pitch, current_pitch)
    
    # 4. Aplicare comenzi
    servo_control.set_aileron(aileron_cmd)
    servo_control.set_elevator(elevator_cmd)
    
    # Throttle-ul merge direct la motor (poate necesita mapare 0-100% sau PWM)
    motor_control.set_throttle(nrf_module.ch2)