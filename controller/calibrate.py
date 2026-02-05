import board
import analogio
import time

ax = analogio.AnalogIn(board.GP26)

# Start with extreme opposites
min_val = 65535
max_val = 0

print("Rotate the stick in full circles now...")

for _ in range(500): # Measure for about 5 seconds
    val = ax.value
    if val < min_val: min_val = val
    if val > max_val: max_val = val
    print(f"Min: {min_val} | Max: {max_val}", end='\r')
    time.sleep(0.01)

print(f"\nFinal Calibration: Min={min_val}, Max={max_val}")