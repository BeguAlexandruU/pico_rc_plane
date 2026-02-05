import board
import analogio
import digitalio
import keypad

X1_MIN, X1_MAX = 8000, 58000 
Y1_MIN, Y1_MAX = 8000, 57000
X2_MIN, X2_MAX = 8000, 58000
Y2_MIN, Y2_MAX = 8000, 58000
CENTER_VAL = 32768
DEADZONE = 2000  # Deadzone around center

# Joystick and Button Setup
#      _________________________
#     |   [LT]           [RT]  |
#     |   [LB]           [RB]  |
#     |________________________|
#     |   [sw_arm]             |
#     |  [ay1]  [A][B]  [ay1]  |
#     | ^>[ax1]    [C] ^>[ax2] |
#     |________________________|
#  
BTN_LB = 0
BTN_LT = 1
BTN_RB = 2
BTN_RT = 3
BTN_A  = 4
BTN_B  = 5
BTN_C  = 6
SW_ARM = 7

ax1 = None
ay1 = None
ax2 = None
ay2 = None

keys = None

def setup():
    global ax1, ay1, ax2, ay2
    global keys
    
    # Initialize Joysticks
    ax1 = analogio.AnalogIn(board.GP29)
    ay1 = analogio.AnalogIn(board.GP27)
    ax2 = analogio.AnalogIn(board.GP26)
    ay2 = analogio.AnalogIn(board.GP28)
    
    # Initialize Buttons
    buttons = (board.GP3, board.GP15, board.GP5, board.GP6, board.GP14, board.GP7, board.GP4, board.GP2)
    keys = keypad.Keys(buttons, value_when_pressed=False, pull=True)

def calibrate_axis(raw_val, v_min, v_max):
    # 1. Clip the value so it doesn't go outside your measured bounds
    raw_val = max(v_min, min(v_max, raw_val))
    
    # 2. Check for deadzone around center
    if abs(raw_val - CENTER_VAL) < DEADZONE:
        return 0
        
    # 3. Map the measured range to -127 to 127
    # Formula: (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    mapped = (raw_val - v_min) * (127 - (-127)) / (v_max - v_min) + (-127)
    
    return int(mapped)

def get_axis():
    global ax1, ay1, ax2, ay2
    jx1 = calibrate_axis(ax1.value, X1_MIN, X1_MAX)
    jy1 = calibrate_axis(ay1.value, Y1_MIN, Y1_MAX)
    jx2 = calibrate_axis(ax2.value, X2_MIN, X2_MAX)
    jy2 = calibrate_axis(ay2.value, Y2_MIN, Y2_MAX)

    return jx1, jy1, jx2, jy2

def clear_events():
    """Flushes the event queue to prevent 'ghost' presses when switching modes."""
    while keys.events.get():
        pass