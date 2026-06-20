import struct
import utime
from machine import Pin, SPI
import lib.nrf24l01 as nrf24l01 

# --- Configuration ---
CHANNEL = 108           
PAYLOAD_SIZE = 28       
TX_ADDR = b"....."
RX_ADDR = b"node3"

nrf = None
last_packet_time = None
_signal_lost = False

roll = 0.0
pitch = 0.0
heading = 0.0
alt = 0.0
gps_lat = 0.0
gps_lon = 0.0
timestamp = 0

def setup():
    global nrf, last_packet_time
    
    # initialize nRF24L01
    spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
    csn = Pin(1)
    ce = Pin(0)
    
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
    last_packet_time = utime.ticks_ms()

def update():
    global nrf, last_packet_time, _signal_lost
    global roll, pitch, heading, alt, gps_lat, gps_lon, timestamp

    if nrf.any():
        data = nrf.recv()
        last_packet_time = utime.ticks_ms()
        _signal_lost = False
        try:
            roll, pitch, heading, alt, gps_lat, gps_lon, timestamp = struct.unpack("<ffffffI", data)
            print(f"{roll},{pitch},{heading},{alt},{gps_lat},{gps_lon},{timestamp}")
        except:
            pass

    if utime.ticks_diff(utime.ticks_ms(), last_packet_time) > 1000:
        if not _signal_lost:
            print("NO SIGNAL")
            _signal_lost = True
