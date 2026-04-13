import time
import machine
import math
import nrf_module



nrf_module.setup()

while True:
    nrf_module.update()
    # time.sleep(0.01)  # Telemetrie la 100Hz

# Aici ar fi logica ta de primire date de la nRF24L01
# Presupunem că ai extras deja valorile:
# t = 0
# while True:
#     v_batt = 12.4
#     pitch = math.sin(t) * 30
#     roll = math.cos(t) * 30
#     alt = 100 + math.sin(t) * 10
    
#     # Trimitem datele prin USB Serial
#     print(f"{v_batt},{pitch},{roll},{alt}")
    
#     t += 0.1
#     #time.sleep(0.1) # Telemetrie la 10Hz

