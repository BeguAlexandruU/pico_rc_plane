"""
Synthetic telemetry generator for desktop app testing.

Sends comma-separated frames over serial matching the GCS protocol:
    roll, pitch, yaw, altitude, lat, lon, timestamp_ms

Usage:
    python test_generator.py [PORT]   (default: COM10)
"""
import math
import sys
import time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM10"
BAUD = 115200

# Iași base coordinates
BASE_LAT = 47.150476
BASE_LON = 27.636506


def main() -> None:
    ser = serial.Serial(PORT, BAUD)
    print(f"Sending synthetic telemetry on {PORT} @ {BAUD} baud. Ctrl+C to stop.")
    t = 0.0
    start_ms = time.time() * 1000
    try:
        while True:
            roll      = math.cos(t) * 30.0
            pitch     = math.sin(t) * 20.0
            yaw       = (t * 10.0) % 360.0
            altitude  = 50.0 + math.sin(t * 0.5) * 10.0
            lat       = BASE_LAT + math.sin(t * 0.2) * 0.001
            lon       = BASE_LON + math.cos(t * 0.2) * 0.001
            timestamp = int(time.time() * 1000 - start_ms)

            line = f"{roll:.4f},{pitch:.4f},{yaw:.4f},{altitude:.4f},{lat:.6f},{lon:.6f},{timestamp}\n"
            ser.write(line.encode("utf-8"))
            t += 0.05
            time.sleep(0.02)   # ~50 Hz transmit rate
    except KeyboardInterrupt:
        print("\nOprit.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
