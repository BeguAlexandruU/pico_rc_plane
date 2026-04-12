# generator_test.py
import serial
import time
import math

ser = serial.Serial('COM10', 115200) # Portul de emisie
t = 0
while True:
    v_batt = 12.4
    pitch = math.sin(t) * 30
    roll = math.cos(t) * 30
    alt = 100 + math.sin(t) * 10
    
    msg = f"{v_batt},{pitch},{roll},{alt}\n"
    ser.write(msg.encode('utf-8'))
    
    t += 0.1