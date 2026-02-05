import sys
import struct
import utime
from machine import Pin, SPI, I2C
import lib.nrf24l01 as nrf24l01 
from lib.ssd1306 import SSD1306_I2C

# --- Configuration ---
CHANNEL = 108           
PAYLOAD_SIZE = 16       
# PIPES = (b"\xe1\xf0\xf0\xf0\xf0", b"\xd2\xf0\xf0\xf0\xf0")
address = [b"1Node", b"2Node"]

sda = Pin(0)
scl = Pin(1)
i2c = I2C(0, sda=sda, scl=scl)
oled = SSD1306_I2C(width=128, height=64, i2c=i2c, addr=0x3C)
oled.fill(0)  
oled.text("Test", 0, 0)  
oled.show()  

def setup_nrf(role):
    # Pin definitions (Adjust for your specific board, e.g., Raspberry Pi Pico)
    # Pico Example: SCK=2, MOSI=3, MISO=4, CSN=1, CE=0
    # breadboard
    # spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
    # csn = Pin(1)
    # ce = Pin(0)
    
    # plane board
    spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    csn = Pin(17)
    ce = Pin(20)
    
    nrf = nrf24l01.NRF24L01(spi, csn, ce, channel=CHANNEL, payload_size=PAYLOAD_SIZE)
    
    # spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    # nrf = nrf24l01.NRF24L01(spi, cs=Pin(17), ce=Pin(20), channel=108, payload_size=8) 
    
    
    # MAX power and LOWEST speed for maximum RC range
    nrf.set_power_speed(nrf24l01.POWER_3, nrf24l01.SPEED_250K)
    
    # disable auto-ack
    # nrf.reg_write(0x01, 0x00)
    
    if role == "tx":
        nrf.open_tx_pipe(address[0])
        nrf.open_rx_pipe(1, address[1])
    else:
        nrf.open_tx_pipe(address[1])
        nrf.open_rx_pipe(1, address[0])
    
    return nrf

def receiver():
    """ Simulates an RC Plane Receiver (Downlink) """
    nrf = setup_nrf("rx")
    nrf.start_listening()
    print("RC Receiver Mode Waiting...")
    
    last_packet_time = utime.ticks_ms()
    start_tick = utime.ticks_ms()
    recv_pps = 0  
    
    disp_pps = 0
    disp_delay = 0.0
    
    while True:
        if nrf.any():
            data = nrf.recv()
            last_packet_time = utime.ticks_ms()
            
            # Unpack RC Channels
            try:
                ch1, ch2, ch3, ch4 = struct.unpack("<iiii", data)
                # print("Received Channels:", ch1, ch2, ch3, ch4)
                # Use channel[0], channel[1] etc for servos/motors
                
                recv_pps += 1
            except:
                print("Failed to unpack data")
                continue
            
            # Optional: Send tiny telemetry packet back if needed
            # nrf.stop_listening()
            # nrf.send(struct.pack("i", rssi_value))
            # nrf.start_listening()
            
        # 3. Calculate Stats every 1 second    
        if utime.ticks_diff(utime.ticks_ms(), start_tick) > 100:
            
            disp_pps = recv_pps*10
            # disp_delay = (1000 / disp_pps) if disp_pps > 0 else 0
            
            oled.fill(0)
            oled.text("PPS: " + str(disp_pps), 0, 0)
            # oled.text("latt: " + f"{disp_delay:.2f}" + "ms", 0, 16)
            oled.text("ch1: " + str(ch1), 0, 12)
            oled.text("ch2: " + str(ch2), 0, 24)
            oled.text("ch3: " + str(ch3), 0, 36)
            oled.text("ch4: " + str(ch4), 0, 48)
            oled.show()
            
            recv_pps = 0
            start_tick = utime.ticks_ms()
          
          
            
        
        # FAILSAFE Logic: If no packet for 1000ms, cut the motors!
        if utime.ticks_diff(utime.ticks_ms(), last_packet_time) > 1000:
            # print("!!! FAILSAFE ACTIVE - SIGNAL LOST !!!")
            pass

receiver()    

