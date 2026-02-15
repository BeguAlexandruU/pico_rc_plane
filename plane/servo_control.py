from lib.picozero import Servo

# --- Configuration ---
# Pulse width range (in seconds) - typically covers 180 degrees total
MIN_PULSE_WIDTH = 0.5 / 1000    # 0.5ms (-90 physical degrees)
MAX_PULSE_WIDTH = 2.5 / 1000    # 2.5ms (+90 physical degrees)
PHYSICAL_RANGE = 180.0          # Total physical range of the servo

# Flight Control Limits
AILERON_MAX_ANGLE = 30  
AILERON_MIN_ANGLE = -30 
ELEVATOR_MAX_ANGLE = 30
ELEVATOR_MIN_ANGLE = -30

# Pins
AILERON_LEFT_PIN = 28
AILERON_RIGHT_PIN = 27
ELEVATOR_PIN = 26

aileron_right = None
aileron_left = None
elevator = None

def setup():
    global aileron_left, aileron_right, elevator
    
    # Initialize servos
    aileron_left = Servo(AILERON_LEFT_PIN, min_pulse_width=MIN_PULSE_WIDTH, max_pulse_width=MAX_PULSE_WIDTH)
    aileron_right = Servo(AILERON_RIGHT_PIN, min_pulse_width=MIN_PULSE_WIDTH, max_pulse_width=MAX_PULSE_WIDTH)
    elevator = Servo(ELEVATOR_PIN, min_pulse_width=MIN_PULSE_WIDTH, max_pulse_width=MAX_PULSE_WIDTH)
    
    center_all()

def map_input_to_servo(input_val, target_min_angle, target_max_angle):
    """
    Maps 0-255 input -> Target Angle -> Servo Value (0.0 to 1.0)
    """
    # 1. Map input (0-255) to Target Angle (e.g., -30 to 30)
    # Formula: (val - in_min) * (out_range) / (in_range) + out_min
    angle = (input_val - 0) * (target_max_angle - target_min_angle) / (255 - 0) + target_min_angle
    
    # 2. Map Target Angle to Servo Value (0.0 - 1.0)
    # Assumes 0.0 = -90deg, 0.5 = 0deg, 1.0 = +90deg (Standard 180 throw)
    # Offset angle by +90 to align with 0-180 scale, then divide by total range
    servo_value = (angle + (PHYSICAL_RANGE / 2.0)) / PHYSICAL_RANGE
    
    return servo_value

def set_aileron(input_value): # 0 to 255
    global aileron_left, aileron_right
    
    # Calculate the normalized servo value (0.0 to 1.0) for the requested angle
    val = map_input_to_servo(input_value, AILERON_MIN_ANGLE, AILERON_MAX_ANGLE)
    
    aileron_left.value = val
    aileron_right.value = val 

def set_elevator(input_value): # 0 to 255
    global elevator
    
    # Calculate the normalized servo value (0.0 to 1.0) for the requested angle
    val = map_input_to_servo(input_value, ELEVATOR_MIN_ANGLE, ELEVATOR_MAX_ANGLE)
    
    elevator.value = val

def center_all():
    set_aileron(127)  
    set_elevator(127)
    