# Pico RC Plane

A multi-part Raspberry Pi Pico RC aircraft system with wireless control, onboard flight automation, telemetry, and a desktop ground station.

## Overview

This repository includes three main systems:

- `controller/`: Pico-based RC transmitter and input menu system with USB HID and nRF24L01 wireless command transmission.
- `flight_controller/`: Pico flight stack with IMU/GPS/barometer sensors, PID control, motor/servo drivers, and nRF24L01 telemetry.
- `telemetry_receiver/`: companion nRF24L01 receiver for telemetry forwarding and logging.
- `desktop_app/`: Python/PyQt ground control station for live telemetry visualization, recording, and replay.

## Key Features

- 2.4 GHz nRF24L01 command and telemetry link
- Stabilize and manual flight modes
- Telemetry logging and replay support
- USB HID gamepad compatibility
- Onboard sensor fusion for roll/pitch and altitude
- GPS position telemetry support
- Ground station with 3D visualization and dark/light themes

## Repository Structure

- `controller/`
  - `main.py` / `code.py`: transmitter runtime and menu management
  - `rc_controller.py`: command packet creation and nRF24L01 transmission
  - `usb_hid_gamepad.py`: USB gamepad support
  - `input_module.py`: button and switch input handling
  - `menu_module.py`, `state_control.py`: mode and state management

- `flight_controller/`
  - `main.py`: primary flight loop, sensor updates, PID control, and telemetry integration
  - `nrf_module.py`: nRF24L01 receiver for RC commands and telemetry sender back to the ground station
  - `imu_module.py`, `gps_module.py`, `bmp085.py`, `mpu6050.py`, `QMC5883L.py`: sensor drivers and fusion logic
  - `motor_control.py`, `servo_control.py`: actuator output control
  - `pid_controller.py`, `pid_controller_v2.py`, `simple_pid.py`: flight control algorithms
  - `lib/`: supporting sensor and communication libraries

- `telemetry_receiver/`
  - `main.py`: simple receiver loop that updates the NRF module and listens for telemetry packets
  - `nrf_module.py`: dedicated telemetry receiver logic

- `desktop_app/`
  - `main.py`: ground station user interface
  - `requirements.txt`: Python dependency manifest
  - `telemetry_logs/`: saved telemetry recordings for replay
  - `plane_models/`: 3D model assets and loader support

## Requirements

- Python 3.10+ for the desktop application
- Raspberry Pi Pico boards for embedded firmware
- CircuitPython / MicroPython on the Pico devices as appropriate
- nRF24L01 modules for wireless RC and telemetry
- IMU, GPS, barometer, servos, motors, and ESC hardware for the flight controller

## nRF24L01 Connections and Payloads

### Connection Summary

- `controller/rc_controller.py` uses the transmitter Pico with SPI pins:
  - `GP10`: SCK
  - `GP11`: MOSI
  - `GP12`: MISO
  - `GP9`: CSN
  - `GP8`: CE

- `flight_controller/nrf_module.py` uses the flight Pico with SPI pins:
  - `GP18`: SCK
  - `GP19`: MOSI
  - `GP16`: MISO
  - `GP17`: CSN
  - `GP20`: CE

- Both endpoints use channel `108`, payload size `24`, and address pair:
  - TX address: `b"node2"`
  - RX address: `b"node3"`

### Payload Formats

#### RC Command Payload

The controller sends a packed 4-byte command payload to the flight Pico using the format:

```python
struct.pack("<bBbb", jx1, jy1, jx2_trimmed, jy2_trimmed)
```

- `jx1`: a signed byte for channel 1 control input
- `jy1`: an unsigned byte for throttle
- `jx2_trimmed`: a signed byte for roll after trim adjustments
- `jy2_trimmed`: a signed byte for pitch after trim adjustments

This payload is decoded by `flight_controller/nrf_module.py` with:

```python
ch1, ch2, ch3, ch4 = struct.unpack("<bBbb", data)
```

#### Telemetry Payload

The flight controller sends telemetry back at approximately 5 Hz using a 24-byte payload:

```python
struct.pack("<fffffI", roll, pitch, altitude, lat, lon, timestamp)
```

- `roll`: 4-byte float
- `pitch`: 4-byte float
- `altitude`: 4-byte float
- `lat`: 4-byte float
- `lon`: 4-byte float
- `timestamp`: 4-byte unsigned integer

This payload supports ground station display and logging of attitude, altitude, and GPS position.

## Desktop App Setup

1. Create or activate a Python virtual environment.
2. Install dependencies:

```bash
python -m pip install -r desktop_app/requirements.txt
```

3. Run the ground station:

```bash
python desktop_app/main.py
```

## Embedded Deployment

### Controller

- Copy the contents of `controller/` to your Pico transmitter drive.
- Ensure the necessary CircuitPython libraries are installed for `board`, `busio`, `digitalio`, `circuitpython_nrf24l01`, etc.
- Run `main.py` or `code.py` on the Pico.

### Flight Controller

- Copy the contents of `flight_controller/` to your Pico flight controller filesystem.
- Use MicroPython-compatible firmware for the Pi Pico.
- Run `main.py` on the flight Pico.

### Telemetry Receiver

- Copy `telemetry_receiver/` to another Pico board if needed.
- Run `telemetry_receiver/main.py`.

## Usage

- On the transmitter, use the menu to choose `Fly Mode` or `USB Mode`.
- Arm and disarm the flight controller using the arm switch.
- Adjust trim and flight mode with physical buttons.
- In the desktop app, select a serial port and connect to receive telemetry.
- Use recording and replay controls to save and review flight data.
- Switch between dark and light UI themes as needed.

## Notes

- `flight_controller/nrf_module.py` transmits telemetry packets containing roll, pitch, altitude, latitude, and longitude.
- The flight controller loop runs at approximately 100 Hz, while telemetry updates are sent at around 5 Hz.
- Pin mappings and module dependencies may need adjustment for your specific Pico hardware and wiring.

## License

This repository does not include a license file. Add a license if you intend to share or publish the project.
