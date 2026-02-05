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
# PIPES = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
address = [b"1Node", b"2Node"]

def setup_nrf(role):
    
    controller.init()
    
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
    
    if role == "tx":
        nrf.open_tx_pipe(address[0])
        nrf.open_rx_pipe(1, address[1])
    else:
        nrf.open_tx_pipe(address[1])
        nrf.open_rx_pipe(1, address[0])

    nrf.print_details()
    nrf.print_pipes()
    
    return nrf

def transmitter():
    """ Simulează un controller RC """
    nrf = setup_nrf("tx")
    
    # În CircuitPython, nrf.listen controlează dacă e în mod RX sau TX
    nrf.listen = False 
    print("RC Transmitter Mode Started (CircuitPython)...")
    
    packets_sent = 0
    packets_success = 0
    start_time = time.monotonic()

    while True:
        # 1. Pregătire date de trimis (exemplu simplu)
        payload = struct.pack("<iiii",1, 2, 3, 4) 
        
        # 2. Trimitere date
        packets_sent += 1
        
        # .send() returnează True dacă a fost trimis cu succes (dacă ACK e activ)
        # sau pur și simplu trimite dacă ACK e dezactivat.
        result = nrf.send(payload)
        
        if result:
            packets_success += 1
            
        # 3. Statistici la fiecare secundă (opțional)
        if time.monotonic() - start_time > 1.0:
            pps = packets_sent
            print(f"Status: {pps} PPS | Trimis cu succes: {result}")
            packets_sent = 0
            start_time = time.monotonic()

        # Mică pauză pentru stabilitate (50Hz = 20ms)
        # time.sleep(0.02)

# Rulare
if __name__ == "__main__":
    transmitter()


