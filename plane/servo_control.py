from lib.picozero import Servo

# Pulse width range (in seconds)
MIN_PULSE_WIDTH = 0.5 / 1000    # 0.5ms
MAX_PULSE_WIDTH = 2.5 / 1000    # 2.5ms

AILERON_LEFT_PIN = 1
AILERON_RIGHT_PIN = 2
ELEVATOR_PIN = 3

aileron_right = None
aileron_left = None
elevator = None

def setup():
    global aileron_left, aileron_right, elevator
    
    aileron_left = Servo(AILERON_LEFT_PIN, min_pulse_width=MIN_PULSE_WIDTH, max_pulse_width=MAX_PULSE_WIDTH)
    aileron_left.value = 0.5
    
    aileron_right = Servo(AILERON_RIGHT_PIN, min_pulse_width=MIN_PULSE_WIDTH, max_pulse_width=MAX_PULSE_WIDTH)
    aileron_right.value = 0.5
    
    elevator = Servo(ELEVATOR_PIN, min_pulse_width=MIN_PULSE_WIDTH, max_pulse_width=MAX_PULSE_WIDTH)
    elevator.value = 0.5 
    
def set_aileron(input_value): # 0 to 255
    global aileron_left, aileron_right
    
    aileron_left.value = input_value / 255.0  # Map to 0 to 1.0
    aileron_right.value = input_value / 255.0 # Map to 0 to 1.0

def set_elevator(value):
    global elevator
    elevator.value = value / 255.0  # Map to 0 to 1.0

def center_all():
    set_aileron(128)  
    set_elevator(128) 

