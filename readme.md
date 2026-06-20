# Pico RC Plane — Wireless RC Aircraft with Onboard Autopilot

A complete RC aircraft control system built on Raspberry Pi Pico microcontrollers, featuring 2.4 GHz wireless control, onboard PID-based attitude stabilization, multi-sensor fusion, GPS telemetry, and a Python desktop ground control station.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Hardware Components](#hardware-components)
4. [Subsystem Descriptions](#subsystem-descriptions)
   - [Transmitter Controller](#transmitter-controller)
   - [Flight Controller](#flight-controller)
   - [Telemetry Receiver](#telemetry-receiver)
   - [Desktop Ground Station](#desktop-ground-station)
5. [Wireless Communication Protocol](#wireless-communication-protocol)
6. [Flight Control Algorithm (PID)](#flight-control-algorithm-pid)
7. [Sensor Fusion](#sensor-fusion)
8. [Installation and Setup](#installation-and-setup)
9. [Pin Reference](#pin-reference)
10. [Technical Specifications](#technical-specifications)
11. [Known Limitations](#known-limitations)

---

## System Overview

The system consists of four interconnected components operating across two physical devices (Pico microcontrollers) and a PC:

```
┌─────────────────┐    2.4 GHz RF    ┌──────────────────────┐
│   TRANSMITTER   │ ───────────────► │   FLIGHT CONTROLLER  │
│  (CircuitPython)│  RC commands     │    (MicroPython)     │
│  Raspberry Pi   │  28 bytes/packet │   Raspberry Pi Pico  │
│  Pico           │                  │                      │
│                 │ ◄─────────────── │  IMU + GPS + Baro    │
└─────────────────┘  telemetry 5 Hz  │  Servos + ESC        │
                                     └──────────┬───────────┘
                                                │ telemetry
                                                │ (NRF24L01)
                                     ┌──────────▼───────────┐
                                     │  TELEMETRY RECEIVER  │
                                     │   (MicroPython)      │
                                     │   Raspberry Pi Pico  │
                                     └──────────┬───────────┘
                                                │ USB serial
                                                │ CSV stream
                                     ┌──────────▼───────────┐
                                     │   DESKTOP GCS        │
                                     │   (Python / PyQt5)   │
                                     │  Live display        │
                                     │  Recording & Replay  │
                                     └──────────────────────┘
```

---

## Architecture

### Communication Flow

| Link | Direction | Protocol | Rate | Payload |
|------|-----------|----------|------|---------|
| Transmitter → Flight Controller | RC Commands | NRF24L01, 250 kbps | ~50 Hz | 5 bytes |
| Flight Controller → Telemetry Receiver | Sensor Data | NRF24L01, 250 kbps | 5 Hz | 28 bytes |
| Telemetry Receiver → PC | CSV Serial | USB-CDC, 115200 baud | 5 Hz | ~60 bytes/line |

### Flight Control Loop

The flight controller runs a fixed-rate control loop at 100 Hz on the Raspberry Pi Pico (RP2040 @ 250 MHz):

```
┌─────────────────────────────────────────────────────────────────┐
│  100 Hz Control Loop (10 ms period)                             │
│                                                                 │
│  1. NRF receive → decode RC stick commands                      │
│  2. IMU update  → sensor fusion → roll, pitch, heading          │
│  3. PID update  → compute servo corrections (Stabilize mode)    │
│  4. GPS update  → parse NMEA, update lat/lon (non-blocking)     │
│  5. Sleep remaining time to maintain exactly 100 Hz             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hardware Components

### Transmitter (Controller Pico)

| Component | Part | Interface |
|-----------|------|-----------|
| Microcontroller | Raspberry Pi Pico (RP2040) | — |
| RF Module | nRF24L01+ | SPI0 |
| Joysticks | 2× dual-axis analog (4 ADC channels) | GP26–GP29 |
| Buttons | 8× digital inputs | GP2–GP7, GP14, GP15 |
| Display | SSD1306 OLED 128×64 | I2C (GP0 SDA, GP1 SCL) |
| Power Monitor | INA219 | I2C |

### Flight Controller Pico

| Component | Part | Interface |
|-----------|------|-----------|
| Microcontroller | Raspberry Pi Pico (RP2040) | — |
| RF Module | nRF24L01+ | SPI1 |
| IMU | MPU6050 (6-axis accel + gyro) | I2C1 |
| Magnetometer | QMC5883L (3-axis compass) | I2C1 |
| Barometer | BMP180 (pressure/altitude) | I2C1 |
| GPS | Generic UART NMEA module | UART0 |
| Motor ESC | Brushless ESC (PWM input) | GP28 |
| Aileron Left Servo | Analog servo | GP26 |
| Aileron Right Servo | Analog servo | GP27 |
| Elevator Servo | Analog servo | GP22 |

### Telemetry Receiver Pico

| Component | Part | Interface |
|-----------|------|-----------|
| Microcontroller | Raspberry Pi Pico (RP2040) | — |
| RF Module | nRF24L01+ | SPI0 |
| PC Link | USB serial (USB-CDC) | USB |

---

## Subsystem Descriptions

### Transmitter Controller

**File:** `controller/code.py`  
**Runtime:** CircuitPython

The transmitter implements a three-state machine:

| State | Description |
|-------|-------------|
| `STATE_MENU` (0) | OLED menu for selecting operating mode |
| `STATE_FLY` (1) | Wireless RC transmission via NRF24L01 |
| `STATE_USB` (2) | USB HID gamepad emulation for ground testing |

In FLY mode, the main loop reads four analog joystick axes and eight digital buttons, packages the data into a 5-byte struct, and transmits at approximately 50 Hz. An ARM switch disables the throttle channel when disarmed, preventing accidental motor starts.

**Joystick Processing:**
- Raw ADC: 0–65535 (12-bit Pico ADC)
- Active range: 8000–58000
- Deadzone: ±2000 units around center (32768)
- Output: Throttle 0–255, all other axes −127 to +127

**Trim System:** Dedicated buttons incrementally adjust `trim_roll` and `trim_pitch` offsets that are added to stick values before transmission.

---

### Flight Controller

**File:** `flight_controller/main.py`  
**Runtime:** MicroPython  
**CPU:** RP2040 @ 250 MHz

#### Input Processing

The NRF module receives 5-byte RC command packets and exposes four channels as global variables:

| Variable | Type | Range | Control |
|----------|------|-------|---------|
| `ch1_rudder` | int8 | −127 to +127 | (unused, future rudder) |
| `ch2_throttle` | uint8 | 0 to 255 | Motor throttle |
| `ch3_aileron` | int8 | −127 to +127 | Roll / aileron |
| `ch4_elevator` | int8 | −127 to +127 | Pitch / elevator |
| `fly_mode` | uint8 | 0 or 1 | Stabilize / Manual |

**Failsafe:** If no packet is received for 1000 ms, all channels are zeroed (throttle off, surfaces centered) and `fly_mode` is set to Stabilize.

#### Flight Modes

**Stabilize Mode (fly_mode = 0):**  
Stick deflection commands a target attitude angle (−80° to +80°). The PID controller computes the servo correction needed to reach and hold that angle. This provides self-leveling behavior — releasing the stick commands 0° (wings level).

**Manual Mode (fly_mode = 1):**  
Stick deflection maps directly to servo position with no attitude feedback. The pilot has direct control analogous to a conventional RC system.

#### Motor Control

The ESC is driven by a 50 Hz PWM signal on GP28:

| Throttle Value | Pulse Width | State |
|---|---|---|
| 0 | 1.0 ms | Armed, zero thrust |
| 128 | 1.5 ms | ~50% thrust |
| 255 | 2.0 ms | Full thrust |

#### Servo Control

Three servos control the flight surfaces. All use 0.5–2.5 ms pulse range (180° physical travel):

| Servo | Pin | Flight Limit |
|-------|-----|-------------|
| Aileron Left | GP26 | ±30° |
| Aileron Right | GP27 | ±30° (mirrored, differential) |
| Elevator | GP22 | ±30° |

Differential aileron: `aileron_right.value = 1.0 - aileron_left.value` ensures that when the left aileron deflects down, the right deflects up, generating a rolling moment.

---

### Telemetry Receiver

**File:** `telemetry_receiver/main.py`  
**Runtime:** MicroPython

A minimal Pico dedicated to receiving the 28-byte telemetry packets from the flight controller and printing them as CSV lines to the USB serial port. The desktop app reads these lines at 115200 baud.

**Output format:**
```
roll,pitch,heading,altitude,gps_lat,gps_lon,timestamp_ms
```
Example: `-1.23,2.45,180.00,12.50,47.150476,27.636506,45230`

---

### Desktop Ground Station

**File:** `desktop_app/main.py`  
**Runtime:** Python 3.10+, PyQt5

A PyQt5 graphical application providing:

- **Live telemetry display** — numeric readouts for roll, pitch, heading, altitude, and GPS position with colour-coded alerts (amber at warning threshold, red at critical)
- **2D map view** — GPS flight track rendered on a Leaflet.js map inside a `QWebEngineView`, switchable between OpenStreetMap, Google Satellite, and Google Terrain
- **Full 3D view** — PyQtGraph OpenGL visualization of the aircraft model (STL) with real attitude applied via Euler rotation
- **CSV recording** — saves live telemetry to timestamped CSV files in `telemetry_logs/`
- **Replay system** — loads any saved log and replays it at correct real-time speed (computed from `timestamp_ms` differences between consecutive frames), with timeline slider, speed multiplier (0.5×–4×), and frame-accurate scrubbing
- **Analytics charts** — altitude and roll/pitch/yaw time-series charts populated on replay load

**Project structure:**
```
desktop_app/
├── main.py               entry point
├── app/
│   ├── gcs_window.py     main QMainWindow
│   ├── core/
│   │   ├── models.py     TelemetryFrame dataclass
│   │   ├── serial_reader.py  QThread serial reader
│   │   └── recorder.py   CSV read/write/list
│   ├── ui/
│   │   ├── themes.py     dark and light QSS stylesheets
│   │   ├── telemetry_panel.py  gauge widgets with alert colouring
│   │   ├── map_view.py   Leaflet.js map
│   │   ├── view_3d.py    PyQtGraph 3D view
│   │   └── charts.py     pyqtgraph analytics
│   └── utils/
│       └── stl_loader.py STL mesh loader
└── requirements.txt
```

---

## Wireless Communication Protocol

### NRF24L01 Common Configuration

| Parameter | Value |
|-----------|-------|
| Frequency band | 2.4 GHz ISM |
| RF channel | 108 (2508 MHz) |
| Data rate | 250 kbps |
| Output power | 0 dBm (MAX) |
| Payload size | 28 bytes (fixed) |
| Auto-ACK | Disabled |
| CRC | 2 bytes |

### RC Command Packet — Transmitter → Flight Controller

**TX address:** `b"node2"` | **RX address:** `b"node2"`

```python
struct.pack("<bBbbB", ch1_rudder, ch2_throttle, ch3_aileron, ch4_elevator, fly_mode)
```

| Field | C Type | Range | Description |
|-------|--------|-------|-------------|
| ch1_rudder | int8 | −127 to +127 | Channel 1 (unused) |
| ch2_throttle | uint8 | 0 to 255 | Throttle |
| ch3_aileron | int8 | −127 to +127 | Roll command |
| ch4_elevator | int8 | −127 to +127 | Pitch command |
| fly_mode | uint8 | 0 or 1 | 0 = Stabilize, 1 = Manual |

Total: 5 bytes active. Remaining 23 bytes are padding to reach the fixed 28-byte payload.

### Telemetry Packet — Flight Controller → Telemetry Receiver

**TX address:** `b"node3"` | **RX address:** `b"node3"`

```python
struct.pack("<ffffffI",
    roll, pitch, heading,
    relative_altitude,
    gps_lat, gps_lon,
    timestamp_ms)
```

| Field | C Type | Unit | Description |
|-------|--------|------|-------------|
| roll | float32 | degrees | Bank angle (−180 to +180) |
| pitch | float32 | degrees | Pitch angle (−90 to +90) |
| heading | float32 | degrees | Magnetic heading (0 to 360) |
| relative_altitude | float32 | metres | Altitude above takeoff point |
| gps_lat | float32 | decimal degrees | Latitude |
| gps_lon | float32 | decimal degrees | Longitude |
| timestamp_ms | uint32 | milliseconds | Time since boot |

Total: 6 × 4 + 4 = **28 bytes** exactly.

---

## Flight Control Algorithm (PID)

### Overview

The Stabilize flight mode uses two independent PID controllers — one for roll (aileron axis) and one for pitch (elevator axis). Each controller computes a servo correction signal in the range −127 to +127.

### Signal Chain

```
RC Stick (−127…+127)
        │
        ▼
  map_to_angle()          linear map: −127…+127 → −80°…+80°
        │
        ▼
  Target Angle (°)
        │
        ├─────────────────────────────────┐
        │                                 │
   setpoint                           measurement
        │                          (IMU fusion roll/pitch)
        └──────────► PID.compute() ◄─────┘
                          │
                          ▼
                  Servo Command (−127…+127)
                          │
                          ▼
               servo_control.set_aileron()
```

### PID Implementation

The controller implements **derivative-on-measurement** and **integral anti-windup**:

```python
# Proportional
p = Kp × error

# Integral with clamping (anti-windup)
integral += error × dt
integral  = clamp(integral, −integral_max, +integral_max)
I = Ki × integral

# Derivative on measurement (no derivative kick on setpoint change)
raw_d    = −(measurement − prev_measurement) / dt
d_filtered = α × raw_d + (1−α) × prev_d_filtered   # low-pass filter
D = Kd × d_filtered

output = clamp(P + I + D, −127, +127)
```

**Derivative-on-measurement** computes the derivative of the sensor reading rather than the error. When the pilot moves the stick, the setpoint changes instantaneously — computing the derivative of the error would produce a large spike (derivative kick). Since the measured angle changes smoothly, the derivative of the measurement remains bounded.

**Integral anti-windup** limits the accumulated integral to ±40 (separate from the output limits of ±127). This prevents the integrator from saturating the output when the aircraft is held in a sustained error state (e.g., during a large attitude change).

**Derivative low-pass filter** with coefficient α = 0.4 reduces the amplification of IMU quantization noise by the kd gain.

### Tuned Parameters

| Axis | Kp | Ki | Kd | integral_max | d_alpha |
|------|----|----|-----|-------------|---------|
| Roll | 1.2 | 0.2 | 0.05 | 40 | 0.4 |
| Pitch | 1.0 | 0.1 | 0.05 | 40 | 0.4 |

---

## Sensor Fusion

### IMU — MPU6050

The MPU6050 provides 6-axis inertial data at up to 1 kHz. At the 100 Hz control loop rate, it supplies:
- 3-axis accelerometer (g-force, used to determine tilt via gravity vector)
- 3-axis gyroscope (deg/s, used for angular rate integration)

### Magnetometer — QMC5883L

The QMC5883L provides 3-axis magnetic field measurements used to compute absolute heading (0°–360°). A 20-second calibration routine at startup rotates the aircraft through a figure-8 pattern to determine hard-iron and soft-iron offsets.

### Sensor Fusion Algorithm

The Mahony/Madgwick-style 9-DOF fusion algorithm (`lib/fusion.py`) combines accelerometer, gyroscope, and magnetometer data to produce drift-free roll, pitch, and heading angles:
- **Gyroscope integration** provides fast, low-noise short-term angle tracking
- **Accelerometer** provides a gravity reference to correct gyroscope drift in roll and pitch
- **Magnetometer** provides an Earth's magnetic field reference to correct heading drift

### Barometer — BMP180

Relative altitude is computed from atmospheric pressure. A 5-sample baseline is averaged at startup. Subsequent readings are smoothed with an IIR low-pass filter:

```
altitude_filtered = 0.9 × altitude_prev + 0.1 × altitude_raw
```

This update runs at 20 Hz (every 5th control loop iteration) to stay within the BMP180's maximum conversion rate.

---

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- Two Raspberry Pi Pico boards (one for transmitter, one for flight controller)
- One additional Pico for the dedicated telemetry receiver (optional)

### Desktop Application

```bash
cd desktop_app
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

**Dependencies:** `PyQt5`, `PyQtWebEngine`, `pyqtgraph`, `PyOpenGL`, `numpy`, `numpy-stl`, `pyserial`

### Transmitter (Controller Pico)

1. Flash **CircuitPython** to the Pico
2. Copy all files from `controller/` to the Pico drive
3. Install CircuitPython libraries: `circuitpython_nrf24l01`, `adafruit_ssd1306`, `adafruit_ina219`
4. `code.py` runs automatically on boot

### Flight Controller Pico

1. Flash **MicroPython** (v1.20+) to the Pico
2. Copy `flight_controller/` files and `lib/` directory to the Pico filesystem
3. Connect sensors to I2C1 (SDA=GP14, SCL=GP15)
4. Connect GPS UART to UART0 (RX=GP13)
5. `main.py` runs automatically on boot (100 Hz loop starts immediately)

### Telemetry Receiver Pico

1. Flash **MicroPython** to the Pico
2. Copy `telemetry_receiver/` files and `lib/` directory to the Pico
3. `main.py` runs automatically on boot; telemetry appears as CSV on USB serial

---

## Pin Reference

### Transmitter Pico (CircuitPython)

| Signal | Pin | Notes |
|--------|-----|-------|
| NRF24L01 SCK | GP10 | SPI0 |
| NRF24L01 MOSI | GP11 | SPI0 |
| NRF24L01 MISO | GP12 | SPI0 |
| NRF24L01 CSN | GP9 | — |
| NRF24L01 CE | GP8 | — |
| Joystick 1 X | GP27 | ADC |
| Joystick 1 Y | GP29 | ADC |
| Joystick 2 X | GP28 | ADC |
| Joystick 2 Y | GP26 | ADC |
| 8× Buttons | GP2–GP7, GP14, GP15 | Digital in |

### Flight Controller Pico (MicroPython)

| Signal | Pin | Notes |
|--------|-----|-------|
| NRF24L01 SCK | GP18 | SPI1 |
| NRF24L01 MOSI | GP19 | SPI1 |
| NRF24L01 MISO | GP16 | SPI1 |
| NRF24L01 CSN | GP17 | — |
| NRF24L01 CE | GP20 | — |
| IMU/Compass/Baro SDA | GP14 | I2C1 |
| IMU/Compass/Baro SCL | GP15 | I2C1 |
| GPS UART RX | GP13 | UART0 |
| GPS UART TX | GP12 | UART0 |
| Motor ESC PWM | GP28 | 50 Hz PWM |
| Aileron Left | GP26 | 50 Hz PWM |
| Aileron Right | GP27 | 50 Hz PWM |
| Elevator | GP22 | 50 Hz PWM |

### Sensor I2C Addresses

| Sensor | Address |
|--------|---------|
| MPU6050 | 0x68 |
| QMC5883L | 0x0D |
| BMP180 | 0x77 |

### Telemetry Receiver Pico (MicroPython)

| Signal | Pin | Notes |
|--------|-----|-------|
| NRF24L01 SCK | GP2 | SPI0 |
| NRF24L01 MOSI | GP3 | SPI0 |
| NRF24L01 MISO | GP4 | SPI0 |
| NRF24L01 CSN | GP1 | — |
| NRF24L01 CE | GP0 | — |

---

## Technical Specifications

| Parameter | Value |
|-----------|-------|
| Control loop frequency | 100 Hz |
| Servo/ESC PWM frequency | 50 Hz |
| IMU update rate | 100 Hz |
| Barometer update rate | 20 Hz |
| GPS baud rate | 9600 baud (NMEA) |
| Telemetry output rate | 5 Hz |
| RF link latency | ~4 ms (SPI transfer) |
| RF channel | 108 (2508 MHz) |
| RF data rate | 250 kbps |
| RF payload size | 28 bytes (fixed) |
| Stick-to-angle mapping | ±127 stick → ±80° |
| Servo travel limit | ±30° (aileron and elevator) |
| Throttle range | 0–255 → 1.0–2.0 ms PWM |
| Failsafe timeout | 1000 ms |
| Desktop GCS update rate | 5 Hz (serial), 10 Hz (map), 60 Hz (3D) |

---

## Known Limitations

- **GPS accuracy:** float32 provides ~6 significant digits of coordinate precision, sufficient for visual tracking but not survey-grade positioning. GPS has no lock indicator in telemetry — `lat=0.0, lon=0.0` is transmitted until a valid NMEA fix is obtained.
- **Magnetometer heading:** Subject to magnetic interference from the motor, ESC, and battery. Positioning the compass away from high-current conductors is required for reliable heading data.
- **Single-axis PID:** Roll and pitch are controlled independently. Cross-coupling between axes (e.g., rudder-roll interaction) is not compensated.
- **No airspeed sensing:** The PID gains are tuned for a nominal airspeed. At very low or high airspeeds, control authority changes and the PID response will differ from the tuned behavior.
- **Barometric altitude:** Sensitive to local weather pressure changes. The baseline is sampled at startup; a pressure change of 1 hPa corresponds to approximately 8.5 m of apparent altitude change.
- **No return-to-home:** Loss of signal activates failsafe (throttle off, surfaces neutral) rather than autonomous return.
