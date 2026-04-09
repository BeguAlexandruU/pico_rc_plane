import board
import busio
import displayio
import terminalio
import time
import i2cdisplaybus  
import adafruit_displayio_ssd1306 
from adafruit_display_text import bitmap_label
import rc_controller as rc_controller
import state_control as state_control

from adafruit_ina219 import INA219


# --- 5. STATE MACHINE ---
# STATE_MENU = 0
# STATE_FLY = 1
# STATE_USB = 2
# current_state = STATE_MENU
menu_index = 0 # 0 for Fly, 1 for USB

# UI GROUPS
main_group = None
menu_group = None
fly_group = None
usb_group = None

# UI Elements
menu_label = None

power_label = None
arm_label = None
mode_label = None
trim_roll_label = None
trim_pitch_label = None

usb_label = None

# Data Variables (Simulated)
pitch_value = 0
roll_value = 0
last_display_update = time.monotonic()

# Hardware Interfaces
ina219 = None

def setup():
    global main_group, menu_group, fly_group, usb_group, menu_index, menu_label, arm_label, mode_label, trim_roll_label, trim_pitch_label, usb_label
    global ina219, power_label
    # controller.setup()
    # usb_gamepad.setup()
    # rc_controller.setup()

    # --- 1. MODERN DISPLAY SETUP ---
    displayio.release_displays()
    i2c = busio.I2C(board.GP1, board.GP0)

    # The specific line that was causing your error:
    display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

    # 
    ina219 = INA219(i2c)    

    # --- 3. UI GROUPS (Performance Secret) ---
    # We create separate groups for different screens so we don't 
    # have to "redraw" everything—we just switch which group is visible.
    main_group = displayio.Group()
    menu_group = displayio.Group()
    fly_group = displayio.Group()
    usb_group = displayio.Group()

    display.root_group = main_group

    # --- 4. PRE-BUILD THE SCREENS ---
    # We build these ONCE to save CPU cycles during flight.

    # Setup Menu
    menu_label = bitmap_label.Label(terminalio.FONT, text="> Fly Mode\n  USB Mode", x=10, y=20, line_spacing=1.5)
    menu_group.append(menu_label)

    # Setup Fly Mode (Using specific labels we can update individually)
    power_label = bitmap_label.Label(terminalio.FONT, text="0 V", x=8, y=8)
    power_label.anchor_point = (1.0, 0)
    power_label.anchored_position = (120, 0)
    arm_label = bitmap_label.Label(terminalio.FONT, text="ARMED", x=8, y=8)
    mode_label = bitmap_label.Label(terminalio.FONT, text="Mode: STABILIZE", x=8, y=20)
    trim_roll_label = bitmap_label.Label(terminalio.FONT, text="Trim Roll: 0", x=8, y=32)
    trim_pitch_label = bitmap_label.Label(terminalio.FONT, text="Trim Pitch: 0", x=8, y=44)
    fly_group.append(power_label)
    fly_group.append(arm_label)
    fly_group.append(mode_label)
    fly_group.append(trim_roll_label)
    fly_group.append(trim_pitch_label)
    
    # Setup USB Mode
    usb_label = bitmap_label.Label(terminalio.FONT, text="USB \nMODE", x=5, y=20, scale=2)
    usb_label.anchor_point = (0.5, 0.5)
    usb_label.anchored_position = (display.width // 2, display.height // 2)  
    usb_group.append(usb_label)

def change_menu(new_state):
    global current_state, main_group, menu_group, fly_group, usb_group
    current_state = new_state
    # Clear the main group and load the new screen
    while len(main_group) > 0:
        main_group.pop()
    
    if new_state == state_control.STATE_MENU:
        main_group.append(menu_group)
    elif new_state == state_control.STATE_FLY:
        main_group.append(fly_group)
    elif new_state == state_control.STATE_USB:
        main_group.append(usb_group)

def update_power():
    global ina219, power_label

    power_label.text = f"{ina219.bus_voltage:.2f} V"


