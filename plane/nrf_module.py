import struct
import utime
from machine import Pin, SPI
import lib.nrf24l01 as nrf24l01 

# --- Configuration ---
CHANNEL = 108           
PAYLOAD_SIZE = 16       
# PIPES = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
address = [b"1Node", b"2Node"]

nrf = None
last_packet_time = None

ch1 = 0
ch2 = 0
ch3 = 0
ch4 = 0

def setup():
    global nrf, last_packet_time
    
    # initialize nRF24L01
    spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    csn = Pin(17)
    ce = Pin(20)
    
    nrf = nrf24l01.NRF24L01(spi, csn, ce, channel=CHANNEL, payload_size=PAYLOAD_SIZE)
    
    # MAX power and LOWEST speed for maximum RC range
    nrf.set_power_speed(nrf24l01.POWER_3, nrf24l01.SPEED_250K)
    
    # disable auto-ack
    # nrf.reg_write(0x01, 0x00)
    
    # rx mode
    nrf.open_tx_pipe(address[1])
    nrf.open_rx_pipe(1, address[0])
    
    nrf.start_listening()
    last_packet_time = utime.ticks_ms()

def update():
    global nrf, last_packet_time
    global ch1, ch2, ch3, ch4
  
    if nrf.any():
        data = nrf.recv()
        last_packet_time = utime.ticks_ms()
        
        # Unpack RC Channels
        try:
            ch1, ch2, ch3, ch4 = struct.unpack("<BBBB", data)
            # print("Received Channels:", ch1, ch2, ch3, ch4)
            # Use channel[0], channel[1] etc for servos/motors
            
        except:
            print("Failed to unpack data")
        
        # Optional: Send tiny telemetry packet back if needed
        # nrf.stop_listening()
        # nrf.send(struct.pack("i", rssi_value))
        # nrf.start_listening()
      
    # FAILSAFE Logic: If no packet for 1000ms, cut the motors!
    if utime.ticks_diff(utime.ticks_ms(), last_packet_time) > 1000:
        print("!!! FAILSAFE ACTIVE - SIGNAL LOST !!!")
        pass


