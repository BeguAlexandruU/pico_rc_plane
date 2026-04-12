import serial
import time
import math

if __name__ == "__main__":
    ser = serial.Serial('COM10', 115200)
    t = 0
    pitch = 0
    roll = 0
    alt = 0


    try:
        while True:
            v_batt = 12.4
            # pitch = math.sin(t) * 30
            roll = math.cos(t) * 30
            alt = 100 + math.sin(t) * 10
            
            msg = f"{v_batt},{pitch},{roll},{alt}\n"
            ser.write(msg.encode('utf-8'))
            
            t += 0.1
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nProgram stopped")
    finally:
        ser.close()