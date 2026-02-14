from machine import Pin, PWM

MIN_DUTY = 3277  # ~1ms pulse (0% throttle)
MAX_DUTY = 6554  # ~2ms pulse (100% throttle)
DUTY_RANGE = MAX_DUTY - MIN_DUTY
MOTOR_PIN = 0

motor_pwm = None

def setup():
    global motor_pwm
    motor_pwm = PWM(Pin(MOTOR_PIN))
    motor_pwm.freq(50)

def set_throttle(throttle_value): # 0 to 255
    
    # Map directly to duty: MIN_DUTY + (throttle_value * DUTY_RANGE / 256
    duty = MIN_DUTY + (throttle_value * DUTY_RANGE >> 8)
    motor_pwm.duty_u16(duty)
    
def stop_motor():
    motor_pwm.duty_u16(MIN_DUTY)