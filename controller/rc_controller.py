import board
import busio
import digitalio
import struct
import time
from circuitpython_nrf24l01.rf24 import RF24
import input_module as controller

# constants
CHANNEL = 108
PAYLOAD_SIZE = 16
ROLE = "tx"
# PIPES = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
address = [b"1Node", b"2Node"]

nrf = None

# debug variables
packets_sent = 0
packets_success = 0
start_time = time.monotonic()

# control variables
armed = True
fly_mode = 0  # 0: Stabilize, 1: Manual
trim_roll = 0
trim_pitch = 0

def setup():
    global nrf
    global packets_sent, packets_success, start_time # debug
    
    # controller.setup()
    
    # Initialize SPI and NRF24L01
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP12)
    csn = digitalio.DigitalInOut(board.GP9)
    ce = digitalio.DigitalInOut(board.GP8)
    nrf = RF24(spi, csn, ce)
    
    # MAX power și LOWEST speed (250kbps)
    # pa_level: 0 = MAX, -6 = HIGH, -12 = LOW, -18 = MIN
    nrf.pa_level = 0 
    nrf.data_rate = 250
    
    # Deactivate Auto-ACK ( nrf.reg_write(0x01, 0x00) )
    nrf.allow_ask_no_ack = False
    nrf.dynamic_payloads = False
    nrf.payload_length = 16
    nrf.channel = CHANNEL
    
    # Configure pipes
    nrf.open_tx_pipe(address[0])
    nrf.open_rx_pipe(1, address[1])
    
    nrf.listen = False 

    nrf.print_details()
    nrf.print_pipes()
    
    packets_sent = 0
    packets_success = 0
    start_time = time.monotonic()
    
def send_message():
    global nrf
    global packets_sent, packets_success, start_time # debug
    
    jx1, jy1, jx2, jy2 = controller.get_axis()
    if armed:
        jy1 = 0
    payload = struct.pack("<iiii", jx1, jy1, jx2, jy2) 
    
    result = nrf.send(payload)
    packets_sent += 1
    
    if result:
        packets_success += 1
        
    # 3. Statistici la fiecare secundă (opțional)
    # if time.monotonic() - start_time > 1.0:
    #     print(f"Status: {packets_sent} PPS | Trimis cu succes: {result}")
    #     packets_sent = 0
    #     start_time = time.monotonic()

    # Mică pauză pentru stabilitate (50Hz = 20ms)
    # time.sleep(0.02)

# Rulare
if __name__ == "__main__":

    setup()
    
    # În CircuitPython, nrf.listen controlează dacă e în mod RX sau TX
    print("RC Transmitter Mode Started (CircuitPython)...")
    
    while True:
        send_message()


