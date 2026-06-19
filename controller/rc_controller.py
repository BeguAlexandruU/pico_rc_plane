import board
import busio
import digitalio
import struct
import time
from circuitpython_nrf24l01.rf24 import RF24
import input_module as controller

# constants
CHANNEL = 108
PAYLOAD_SIZE = 28
TX_ADDR = b"node2"
RX_ADDR = b"....."

nrf = None

# # debug variables
# packets_sent = 0
# packets_success = 0
# start_time = time.monotonic()

# control variables
armed = True
fly_mode = 0  # 0: Stabilize, 1: Manual
trim_roll = 0
trim_pitch = 0

def setup():
    global nrf
    global packets_sent, packets_success, start_time # debug
    
    # Initialize SPI and NRF24L01
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    csn = digitalio.DigitalInOut(board.GP9)
    ce = digitalio.DigitalInOut(board.GP8)
    nrf = RF24(spi, csn, ce)
    
    # MAX power și LOWEST speed (250kbps)
    # pa_level: 0 = MAX, -6 = HIGH, -12 = LOW, -18 = MIN
    nrf.pa_level = 0 
    nrf.data_rate = 250
    
    # Deactivate Auto-ACK 
    nrf.allow_ask_no_ack = False
    nrf.dynamic_payloads = False
    nrf.payload_length = PAYLOAD_SIZE
    nrf.channel = CHANNEL
    nrf.auto_ack = False       # Dezactivează așteptarea ACK global
    nrf.arc = 0                # Dezactivează re-trimiterile (Auto Re-transmit Count)
    
    # Configure pipes
    nrf.open_tx_pipe(TX_ADDR)
    nrf.open_rx_pipe(1, RX_ADDR)
    
    nrf.listen = False 

    nrf.print_details()
    nrf.print_pipes()
    
    packets_sent = 0
    packets_success = 0
    start_time = time.monotonic()
    
def send_message():
    global nrf
    global packets_sent, packets_success, start_time # debug
    
    jx1, jy1, jx2, jy2 = controller.get_axis_rc_format()
    if armed:
        jy1 = 0
    
    # map controll
    # jy1 = 0  # throttle
    # jx2 = 0  # aileron
    # jy2 = 0  # elevator
    payload = struct.pack("<bBbbB", jx1, jy1, max(-127, min(127, int(jx2-trim_roll))), max(-127, min(127, int(jy2+trim_pitch))), fly_mode)
    
    result = nrf.send(payload)