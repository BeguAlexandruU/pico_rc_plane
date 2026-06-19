import struct
import gps_module
import imu_module
import utime
from machine import Pin, SPI
import lib.nrf24l01 as nrf24l01 

# Channel Mapping:
# ch1 = rudder (not used)
# ch2 = throttle  
# ch3 = aileron
# ch4 = elevator

# --- Configuration ---
CHANNEL = 108           
PAYLOAD_SIZE = 28      
TX_ADDR = b"node3"
RX_ADDR = b"node2"

nrf = None
last_packet_time = None
last_telemetry_time = None

ch1_rudder = 0
ch2_throttle = 0
ch3_aileron = 0
ch4_elevator = 0
fly_mode = 0  # 0: Stabilize, 1: Manual

def setup():
    global nrf, last_packet_time, last_telemetry_time
    
    # initialize nRF24L01
    spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    csn = Pin(17)
    ce = Pin(20)
    
    nrf = nrf24l01.NRF24L01(spi, csn, ce, channel=CHANNEL, payload_size=PAYLOAD_SIZE)
    
    # MAX power and LOWEST speed for maximum RC range
    nrf.set_power_speed(nrf24l01.POWER_3, nrf24l01.SPEED_250K)
    
    # disable auto-ack
    nrf.reg_write(0x01, 0x00)
    nrf.reg_write(0x04, 0x00)
    
    # rx mode
    nrf.open_tx_pipe(TX_ADDR)
    nrf.open_rx_pipe(1, RX_ADDR)
    
    nrf.start_listening()
    current_time = utime.ticks_ms()
    last_packet_time = current_time
    last_telemetry_time = current_time

def update():
    global nrf, last_packet_time, last_telemetry_time
    global ch1_rudder, ch2_throttle, ch3_aileron, ch4_elevator, fly_mode
    
    current_time = utime.ticks_ms()
  
    if nrf.any():
        data = nrf.recv()
        last_packet_time = current_time
        
        # Unpack RC Channels
        try:
            ch1_rudder, ch2_throttle, ch3_aileron, ch4_elevator, fly_mode = struct.unpack("<bBbbB", data)
            # print("Received Channels:", ch1_rudder, ch2_throttle, ch3_aileron, ch4_elevator, fly_mode)
            # Use channel[0], channel[1] etc for servos/motors

        except:
            print("Received malformed packet")
        
    # Send telemetry 5Hz
    if utime.ticks_diff(current_time, last_telemetry_time) > 200:

        try:
            last_telemetry_time = current_time
            nrf.stop_listening()
            payload = struct.pack("<ffffffI", 
                            imu_module.fusion.roll, 
                            imu_module.fusion.pitch, 
                            imu_module.fusion.heading,
                            imu_module.relative_altitude, 
                            gps_module.lat,
                            gps_module.lon,
                            current_time)
            nrf.send(payload)
        except:
            print("Failed to send telemetry")
        nrf.start_listening()

    # FAILSAFE Logic: If no packet for 1000ms, cut the motors
    if utime.ticks_diff(current_time, last_packet_time) > 1000:
        # print("!!! FAILSAFE ACTIVE - SIGNAL LOST !!!")
        ch1_rudder = 0
        ch2_throttle = 0
        ch3_aileron = 10
        ch4_elevator = 0
        fly_mode = 0



