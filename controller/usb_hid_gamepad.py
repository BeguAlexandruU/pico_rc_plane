import usb_hid
import time
from hid_gamepad import Gamepad
import input_module as controller
import state_control

gp = None

def setup():
    global gp
    gp = Gamepad(usb_hid.devices)

def send_usb_message():
    global gp
    
    # 1. Read Joysticks with Deadzone
    jx1, jy1, jx2, jy2 = controller.get_axis_b_format()
    
    # 2. Update movement
    gp.move_joysticks(x=jx1, y=jy1*-1, z=jx2*-1, r_z=jy2*-1)

    # 3. Handle Buttons
    while True:
        event = controller.keys.events.get()
        if not event:
            break 
            
        if event.pressed:
            # return to menu on Button A
            if event.key_number == controller.BTN_A:
                controller.clear_events()
                state_control.change_state(state_control.STATE_MENU)
            
            gp.press_buttons(event.key_number)
        
        if event.released:
            gp.release_buttons(event.key_number)
            
