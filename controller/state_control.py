import menu_module

# --- 5. STATE MACHINE ---
STATE_MENU = 0
STATE_FLY = 1
STATE_USB = 2
current_state = STATE_MENU

def setup():
    global current_state
    current_state = STATE_MENU

def change_state(new_state):
    global current_state
    if new_state in (STATE_MENU, STATE_FLY, STATE_USB):
        current_state = new_state
        menu_module.change_menu(current_state)
        