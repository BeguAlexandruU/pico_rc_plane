import board
import busio
import displayio
import state_control
import terminalio
import time
import i2cdisplaybus  
import adafruit_displayio_ssd1306 
import input_module as controller
import usb_hid_gamepad as usb_gamepad
import rc_controller as rc_controller
import menu_module as menu_module


def setup():
    controller.setup()
    usb_gamepad.setup()
    rc_controller.setup()
    menu_module.setup()
    state_control.setup()

setup()
menu_module.change_menu(state_control.STATE_MENU)

while True:

    if state_control.current_state == state_control.STATE_FLY:
        rc_controller.send_message()
        
        # PERFORMANCE TIP: Only update the .text property. 
        # Displayio only refreshes the changed pixels.
        # pitch_value = (pitch_value + 1) % 360
        # roll_value = (roll_value + 2) % 360
        
        # Update display only once per second
        # current_time = time.monotonic()
        # if current_time - last_display_update >= 1.0:
          # pitch_label.text = f"Pitch: {pitch_value}"
          # roll_label.text = f"Roll:  {roll_value}"
        # last_display_update = current_time
        
        # # Insert your nrf.send() logic here!
    elif state_control.current_state == state_control.STATE_USB:
        usb_gamepad.send_usb_message()
            
    # 2. HANDLE INPUT (The Performance Winner)
    event = controller.keys.events.get()
    if event:
        if event.pressed:
            # event.key_number corresponds to the index in your 'pins' tuple
            if event.key_number == controller.BTN_A: # Button A
                if state_control.current_state in (state_control.STATE_FLY, state_control.STATE_USB):
                    state_control.change_state(state_control.STATE_MENU)
            
            elif event.key_number == controller.BTN_B: # Button B
                if state_control.current_state == state_control.STATE_MENU:
                    menu_module.menu_index = (menu_module.menu_index + 1) % 2
                    menu_module.menu_label.text = "> Fly Mode\n  USB Mode" if menu_module.menu_index == 0 else "  Fly Mode\n> USB Mode"
                    
                if state_control.current_state == state_control.STATE_FLY: # Trim Pitch +
                    rc_controller.trim_pitch += 1
                    menu_module.trim_pitch_label.text = f"Trim Pitch: {rc_controller.trim_pitch}"

            elif event.key_number == controller.BTN_C: # Button C
                if state_control.current_state == state_control.STATE_MENU:
                    new_state = state_control.STATE_FLY if menu_module.menu_index == 0 else state_control.STATE_USB
                    state_control.change_state(new_state)
                    
                if state_control.current_state == state_control.STATE_FLY: # Trim Pitch -
                    rc_controller.trim_pitch -= 1
                    menu_module.trim_pitch_label.text = f"Trim Pitch: {rc_controller.trim_pitch}"
            
            elif event.key_number == controller.SW_ARM: # Switch ARM
                if state_control.current_state == state_control.STATE_FLY:
                    menu_module.arm_label.text = "ARMED"
                    rc_controller.armed = True
                    
            elif event.key_number == controller.BTN_LT: # Switch MODE
                if state_control.current_state == state_control.STATE_FLY:
                    rc_controller.fly_mode = (rc_controller.fly_mode + 1) % 2
                    mode_text = "STABILIZE" if rc_controller.fly_mode == 0 else "MANUAL"
                    menu_module.mode_label.text = f"Mode: {mode_text}"
                    
            elif event.key_number == controller.BTN_RB: # Trim Roll +
                if state_control.current_state == state_control.STATE_FLY:
                    rc_controller.trim_roll += 1
                    menu_module.trim_roll_label.text = f"Trim Roll: {rc_controller.trim_roll}"
                    
            elif event.key_number == controller.BTN_LB: # Trim Roll -
                if state_control.current_state == state_control.STATE_FLY:
                    rc_controller.trim_roll -= 1
                    menu_module.trim_roll_label.text = f"Trim Roll: {rc_controller.trim_roll}"
                    
                    
        elif event.released:
            if event.key_number == controller.SW_ARM: # Switch ARM
                if state_control.current_state == state_control.STATE_FLY:
                    menu_module.arm_label.text = "DISARMED"
                    rc_controller.armed = False