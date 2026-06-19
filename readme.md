# Pico RC Plane

A multi-part Raspberry Pi Pico RC aircraft system with wireless control, onboard flight automation, telemetry, and a desktop ground station.

## Overview

This repository includes three main systems:

- `controller/`: Pico-based RC transmitter and input menu system with USB HID and nRF24L01 wireless command transmission.
- `flight_controller/`: Pico flight stack with IMU/GPS/barometer sensors, PID control, motor/servo drivers, and nRF24L01 telemetry.
- `telemetry_receiver/`: companion nRF24L01 receiver for telemetry forwarding and logging.
- `desktop_app/`: Python/PyQt ground control station for live telemetry visualization, recording, and replay.

## Key Features

- 2.4 GHz nRF24L01 command and telemetry link (250 kbps, MAX power)
- Flight modes: **Stabilize** (PID-assisted attitude control) and **Manual** (direct stick control)
- Telemetry logging and replay support with CSV export
- USB HID gamepad compatibility for ground testing
- Onboard sensor fusion (MPU6050 + QMC5883L) for roll/pitch/heading
- Barometric altitude hold capability (BMP180)
- GPS position telemetry support (NMEA GPRMC/GNRMC)
- Ground station with live 3D visualization, map display, and dark/light UI themes
- 100 Hz flight control loop with PID-based attitude stabilization

## Repository Structure

- `controller/`
  - `code.py`: transmitter runtime loop with menu management
  - `rc_controller.py`: nRF24L01 command transmitter (250 kbps, MAX power)
  - `input_module.py`: 4x analog joystick (GP27, GP29, GP28, GP26) and 8x button inputs
  - `menu_module.py`, `state_control.py`: UI mode and flight mode state management
  - `usb_hid_gamepad.py`: USB gamepad emulation for ground testing
  - `hid_gamepad.py`: HID protocol implementation

- `flight_controller/`
  - `main.py`: 100 Hz flight loop running sensor updates, PID control, and telemetry transmission
  - `nrf_module.py`: nRF24L01 receiver for RC commands and telemetry transmitter (roll, pitch, heading, altitude, GPS, timestamp)
  - `imu_module.py`: MPU6050 + QMC5883L sensor fusion (Fusion library) for roll/pitch/heading
  - `gps_module.py`: UART0 (9600 baud) GPS receiver parsing GPRMC/GNRMC sentences
  - `motor_control.py`: PWM motor control on GP28 (50 Hz, throttle 0-255)
  - `servo_control.py`: 3x servo outputs (Aileron Left=GP26, Aileron Right=GP27, Elevator=GP22) with ±30° flight limits
  - `pid_controller.py`: Roll/Pitch stabilization PID controllers (Roll: Kp=1.2, Ki=0.2, Kd=0.05; Pitch: Kp=1.0, Ki=0.1, Kd=0.05)
  - `lib/`: MPU6050, QMC5883L, BMP180 sensor drivers; Fusion algorithm; nRF24L01 library; picozero servo abstraction

- `telemetry_receiver/`
  - `main.py`: dedicated telemetry receiver loop
  - `nrf_module.py`: nRF24L01 telemetry receiver logic

- `desktop_app/`
  - `main.py`: PyQt5-based ground control station with live telemetry display, 3D GLWidget, folium map, recording/replay
  - `requirements.txt`: Python 3.10+ dependencies (PyQt5, numpy, folium, pyqtgraph, numpy-stl, pyserial)
  - `telemetry_logs/`: saved CSV flight recordings for replay and analysis
  - `plane_models/`: 3D STL model assets for visualization

## Requirements

### Desktop Application
- Python 3.10+
- Dependencies: PyQt5, numpy, folium, pyqtgraph, numpy-stl, pyserial (see `desktop_app/requirements.txt`)

### Embedded Systems
- Raspberry Pi Pico boards (RP2040)
- **Controller Pico**: CircuitPython with nRF24L01, board, busio, digitalio, analogio libraries
- **Flight Controller Pico**: MicroPython with nRF24L01 support
- **Telemetry Receiver Pico**: MicroPython with nRF24L01 support

### Hardware
- 3× nRF24L01+ modules (or nRF24L01 with external antenna for longer range)
- IMU/Compass: MPU6050 (6-axis accelerometer + gyroscope)
- Compass: QMC5883L (3-axis magnetometer)
- Barometer: BMP180 (pressure/altitude sensor)
- GPS: UART-based module (9600 baud, NMEA GPRMC/GNRMC format)
- Motor: ESC (electronic speed controller) with PWM input
- Servos: 3× analog servos (0.5-2.5 ms pulse width) for aileron (left/right) and elevator
- I2C Sensors: MPU6050, QMC5883L, BMP180 on I2C1 (SDA=GP14, SCL=GP15)

## nRF24L01 Radio Configuration

### Connection Summary

**Transmitter Pico** (`controller/rc_controller.py`):
- SPI pins: GP10 (SCK), GP11 (MOSI), GP12 (MISO), GP9 (CSN), GP8 (CE)

**Flight Controller Pico** (`flight_controller/nrf_module.py`):
- SPI pins: GP18 (SCK), GP19 (MOSI), GP16 (MISO), GP17 (CSN), GP20 (CE)

**Common Settings**:
- Channel: 108
- Data Rate: 250 kbps (lowest, longest range)
- Power Level: MAX (0 dBm)
- Payload Size: 28 bytes
- Auto-ACK: Disabled
- TX Address: `b"node2"`
- RX Address: `b"node3"`

### Payload Formats

#### RC Command Payload (Transmitter → Flight Controller)

The controller sends a 28-byte command packet every control loop iteration:

```python
struct.pack("<bBbbB", jx1, jy1, jx2_trimmed, jy2_trimmed, fly_mode)
```

- `jx1`: signed byte (-127 to +127), channel 1 / rudder control
- `jy1`: unsigned byte (0 to 255), channel 2 / throttle
- `jx2_trimmed`: signed byte (-127 to +127), channel 3 / aileron (roll) after trim
- `jy2_trimmed`: signed byte (-127 to +127), channel 4 / elevator (pitch) after trim
- `fly_mode`: unsigned byte, 0=Stabilize, 1=Manual

Decoded by `flight_controller/nrf_module.py`:

```python
ch1, ch2, ch3, ch4, fly_mode = struct.unpack("<bBbbB", data)
```

#### Telemetry Payload (Flight Controller → Ground Station)

The flight controller sends a 28-byte telemetry packet at approximately 5 Hz:

```python
struct.pack("<fffffffff", roll, pitch, heading, relative_altitude, lat, lon, gps_accuracy, reserved, timestamp_ms)
```

- `roll`: 4-byte float (-180 to +180 degrees)
- `pitch`: 4-byte float (-90 to +90 degrees)
- `heading`: 4-byte float (0 to 360 degrees, from magnetometer)
- `relative_altitude`: 4-byte float (meters above baseline)
- `lat`: 4-byte float (latitude in decimal degrees)
- `lon`: 4-byte float (longitude in decimal degrees)
- Additional fields padded to 28 bytes

## Desktop App Setup

### Prerequisites
- Python 3.10 or higher
- A serial connection to the telemetry receiver (USB-to-Serial adapter or Pico with UART-to-USB)

### Installation

1. Navigate to the project directory:
   ```bash
   cd pico_rc_plane
   ```

2. Create a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r desktop_app/requirements.txt
   ```

### Running the Ground Station

```bash
python desktop_app/main.py
```

The application will launch with:
- **Telemetry Panel**: Live roll, pitch, heading, altitude, GPS position
- **3D Visualization**: Real-time attitude display (GLWidget)
- **Map View**: GPS track on folium map
- **Recording Controls**: Start/stop telemetry recording
- **Replay Controls**: Load and playback saved CSV flights
- **Theme Toggle**: Switch between Dark and Light UI modes

## Embedded Deployment

### Controller (Transmitter Pico)

1. Flash **CircuitPython** to the Pico
2. Copy all files from `controller/` to the Pico drive
3. Ensure required libraries are installed:
   - `circuitpython_nrf24l01`
   - `board`, `busio`, `digitalio`, `analogio`, `keypad`
4. Run `code.py` (automatically executed on boot)
5. Use the menu to select flight mode or USB HID mode

### Flight Controller (Main Flight Pico)

1. Flash **MicroPython** to the Pico
2. Copy all files from `flight_controller/` (including `lib/` subdirectory) to the Pico filesystem
3. Connect sensors via I2C1:
   - MPU6050, QMC5883L, BMP180 on SDA=GP14, SCL=GP15
   - GPS UART on UART0 (TX=GP12, RX=GP13, 9600 baud)
4. Connect actuators:
   - Motor ESC PWM: GP28
   - Aileron Left Servo: GP26
   - Aileron Right Servo: GP27
   - Elevator Servo: GP22
5. Run `main.py` on the flight Pico (100 Hz control loop begins automatically)

### Telemetry Receiver (Optional Standalone Receiver Pico)

1. Flash **MicroPython** to the Pico
2. Copy all files from `telemetry_receiver/` to the Pico filesystem
3. This device receives telemetry packets and can relay them via UART to a ground station
4. Run `telemetry_receiver/main.py`

## Usage

### Transmitter (Controller)

1. Power on the transmitter Pico
2. Navigate the menu to select:
   - **Fly Mode**: Wireless RC control via nRF24L01
   - **USB Mode**: Emulate a USB HID gamepad for ground testing
3. Adjust flight mode (Stabilize vs Manual) using physical buttons
4. Use trim buttons to calibrate stick offsets before flight
5. Press the ARM switch to arm/disarm the flight controller

### Flight Controller

1. Power on and ensure all sensors initialize (check I2C, GPS connection)
2. Wait for magnetometer calibration to complete (20 seconds)
3. Once armed via transmitter, the flight controller begins stabilization
4. **Stabilize Mode**: The 100 Hz PID loop maintains level attitude
   - Roll/Pitch setpoints are mapped from stick input (-80° to +80°)
   - Control is proportional and damped
5. **Manual Mode**: Direct stick-to-servo pass-through control

### Ground Station (Desktop App)

1. Connect the telemetry receiver (or flight controller) to a USB serial port
2. Run `python desktop_app/main.py`
3. Select the serial port and connect
4. View live telemetry:
   - Roll, Pitch, Heading (3D visualization)
   - Altitude (barometer)
   - GPS position (map view with folium)
5. Record telemetry data to CSV (automatically saved to `telemetry_logs/`)
6. Replay past flights from CSV files
7. Toggle between Dark and Light UI themes

## Technical Notes

### Flight Control
- **Control Loop**: 100 Hz on flight controller (10 ms per iteration)
- **Telemetry Output**: ~5 Hz (200 ms between packets)
- **Attitude Stabilization** (Stabilize Mode):
  - Roll setpoint: -80° to +80° (mapped from stick input -127 to +127)
  - Pitch setpoint: -80° to +80°
  - PID Gains:
    - Roll: Kp=1.2, Ki=0.2, Kd=0.05
    - Pitch: Kp=1.0, Ki=0.1, Kd=0.05
  - Servo Limits: ±30° deflection for aileron and elevator
- **Throttle Range**: 0-255 (0% to 100%)

### Sensor Fusion
- **IMU**: MPU6050 provides raw accelerometer and gyroscope data
- **Compass**: QMC5883L provides heading reference
- **Fusion Algorithm**: Custom 9-DOF Fusion (gyro + accel + mag)
- **Output**: Roll, Pitch, Heading angles in degrees

### Wireless Link
- **Frequency**: 2.4 GHz (ISM band)
- **Data Rate**: 250 kbps (optimized for range, reduces interference sensitivity)
- **Latency**: ~4 ms per packet (nRF24L01 SPI transfer time)
- **Packet Loss Tolerance**: Auto-retransmit disabled for low-latency control

### Power Management
- **Flight Controller CPU**: 250 MHz (configured in main.py)
- **Motor PWM**: 50 Hz (standard servo/ESC frequency)
- **GPS**: 9600 baud, non-blocking UART reads (updates only on complete NMEA sentences)

### Telemetry Data Recorded
- Timestamp (ms since boot)
- Roll, Pitch, Heading (degrees)
- Altitude (meters, relative to baseline)
- GPS Latitude, Longitude (decimal degrees)
- Flight mode, arm state, sensor health

### Calibration
- **Magnetometer**: Auto-calibration routine runs on IMU module setup (20 seconds)
- **Barometer**: Baseline altitude sampled on startup (5 samples averaged)
- **Joysticks**: Deadzone = 2000 ADC units around center (32768)

## Wiring Reference

### Controller (Transmitter Pico - CircuitPython)

| Component | Pin | Purpose |
|-----------|-----|---------|
| nRF24L01 SCK | GP10 | SPI Clock |
| nRF24L01 MOSI | GP11 | SPI Data Out |
| nRF24L01 MISO | GP12 | SPI Data In |
| nRF24L01 CSN | GP9 | Chip Select |
| nRF24L01 CE | GP8 | Chip Enable |
| Joystick 1 X-Axis | GP27 | Analog (0-3.3V) |
| Joystick 1 Y-Axis | GP29 | Analog (0-3.3V) |
| Joystick 2 X-Axis | GP28 | Analog (0-3.3V) |
| Joystick 2 Y-Axis | GP26 | Analog (0-3.3V) |
| Buttons (8x) | GP3, GP15, GP5, GP6, GP14, GP7, GP4, GP2 | Digital Input |

### Flight Controller Pico (MicroPython)

| Component | Pin(s) | Purpose |
|-----------|--------|---------|
| nRF24L01 SCK | GP18 | SPI Clock |
| nRF24L01 MOSI | GP19 | SPI Data Out |
| nRF24L01 MISO | GP16 | SPI Data In |
| nRF24L01 CSN | GP17 | Chip Select |
| nRF24L01 CE | GP20 | Chip Enable |
| Motor ESC PWM | GP28 | Throttle Control |
| Aileron Left Servo | GP26 | PWM Signal |
| Aileron Right Servo | GP27 | PWM Signal |
| Elevator Servo | GP22 | PWM Signal |
| I2C SDA (Sensors) | GP14 | IMU, Compass, Barometer |
| I2C SCL (Sensors) | GP15 | IMU, Compass, Barometer |
| GPS TX | GP12 | UART0 RX (9600 baud) |
| GPS RX | GP13 | UART0 TX (9600 baud) |

### Sensor I2C Addresses

- **MPU6050**: 0x68 (default, can be 0x69 if AD0 pin pulled high)
- **QMC5883L**: 0x0D
- **BMP180**: 0x77

---

## Troubleshooting

### nRF24L01 Connection Issues

- **No communication**: Verify SPI pin mappings and power supply (nRF24L01 requires stable 3.3V with capacitor)
- **Intermittent packets**: Check antenna orientation and use external antenna version for improved range
- **Slow data rate**: Reduce payload size or increase TX power (current setting is 250 kbps for range)

### Sensor Initialization Failures

- **I2C errors**: Verify pull-up resistors (typically 4.7k Ω on SDA/SCL) and sensor addresses with `i2c_scan.py`
- **GPS no signal**: Check UART baud rate (9600) and NMEA sentence format compatibility
- **Magnetometer calibration timeout**: Rotate the aircraft in figure-8 pattern during initial 20-second calibration

### Flight Control Issues

- **Aircraft won't stabilize**: Verify PID gains and servo limits; check motor/servo connections for backward polarity
- **Erratic attitude readings**: Ensure IMU is mounted level and magnetometer has no metal interference
- **GPS position drift**: Allow 20+ second GPS lock-in period after power-up; avoid flying near large metal structures

### Desktop App Connection Issues

- **Serial port not detected**: Verify USB driver installation and check COM port in Device Manager
- **Telemetry data frozen**: Check baud rate (typically 115200 for UART-to-USB adapter) and packet format
- **3D visualization lag**: Reduce plot update frequency or close background applications

---

## Performance Metrics

- **Radio Latency**: ~4 ms (SPI transfer + processing)
- **Control Loop Rate**: 100 Hz (10 ms cycle)
- **Attitude Response Time**: ~200 ms (depends on PID tuning and air disturbance)
- **GPS Update Rate**: Depends on module (typically 1-5 Hz)
- **Telemetry Bandwidth**: ~168 bytes/sec @ 5 Hz telemetry + 28 bytes/sec commands = ~196 bytes/sec

---

## License

This repository does not include a license file. Add a license if you intend to share or publish the project.


