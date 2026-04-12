"""
I2C Diagnostic Script for Pico
This script helps diagnose I2C communication issues with the SSD1306 OLED display.
"""

from machine import I2C, Pin
from time import sleep
import sys

def test_i2c_basic():
    """Test basic I2C functionality"""
    print("=== I2C Diagnostic Test ===")
    print("Testing I2C communication...")
    
    try:
        # Initialize I2C with the same pins as your main script
        sda = Pin(0)
        scl = Pin(1)
        i2c = I2C(id=0, sda=sda, scl=scl, freq=400000)
        
        print(f"I2C initialized successfully")
        print(f"SDA: Pin {sda}")
        print(f"SCL: Pin {scl}")
        print(f"Frequency: 400kHz")
        
        return i2c
    except Exception as e:
        print(f"Failed to initialize I2C: {e}")
        return None

def scan_i2c_devices(i2c):
    """Scan for I2C devices"""
    print("\n=== Scanning I2C Bus ===")
    
    try:
        devices = i2c.scan()
        
        if not devices:
            print("❌ No I2C devices found!")
            print("Check your wiring:")
            print("  - SDA should be connected to Pin 0")
            print("  - SCL should be connected to Pin 1") 
            print("  - VCC should be connected to 3.3V")
            print("  - GND should be connected to GND")
            return None
        else:
            print(f"✅ Found {len(devices)} I2C device(s):")
            for addr in devices:
                print(f"  - Device at address: 0x{addr:02X} ({addr})")
            return devices
            
    except Exception as e:
        print(f"❌ Error scanning I2C bus: {e}")
        return None

def test_oled_communication(i2c, addr=0x3C):
    """Test communication with OLED at specific address"""
    print(f"\n=== Testing OLED at 0x{addr:02X} ===")
    
    try:
        # Try to write a simple command to the OLED
        i2c.writeto(addr, bytearray([0x80, 0xAE]))  # Display OFF command
        print(f"✅ Successfully communicated with OLED at 0x{addr:02X}")
        
        # Try display ON command
        i2c.writeto(addr, bytearray([0x80, 0xAF]))  # Display ON command
        print("✅ OLED responded to display commands")
        
        return True
        
    except OSError as e:
        print(f"❌ Failed to communicate with OLED at 0x{addr:02X}: {e}")
        if e.errno == 5:  # EIO error
            print("This is the same error you're getting in your main script")
        return False

def test_different_frequencies(i2c_pins):
    """Test I2C at different frequencies"""
    print("\n=== Testing Different I2C Frequencies ===")
    
    frequencies = [100000, 200000, 400000]  # 100kHz, 200kHz, 400kHz
    
    for freq in frequencies:
        try:
            print(f"\nTesting at {freq//1000}kHz...")
            sda, scl = i2c_pins
            i2c = I2C(id=0, sda=sda, scl=scl, freq=freq)
            
            devices = i2c.scan()
            if devices:
                print(f"✅ Found devices at {freq//1000}kHz: {[hex(d) for d in devices]}")
                # Test OLED communication at this frequency
                if 0x3C in devices:
                    if test_oled_communication(i2c, 0x3C):
                        print(f"✅ OLED works at {freq//1000}kHz")
                        return freq
            else:
                print(f"❌ No devices found at {freq//1000}kHz")
                
        except Exception as e:
            print(f"❌ Error at {freq//1000}kHz: {e}")
    
    return None

def main():
    """Main diagnostic function"""
    print("Starting I2C diagnostic...")
    
    # Test basic I2C
    i2c = test_i2c_basic()
    if not i2c:
        return
    
    # Scan for devices
    devices = scan_i2c_devices(i2c)
    if not devices:
        print("\n🔧 Troubleshooting steps:")
        print("1. Check all connections are secure")
        print("2. Verify the display is getting power (3.3V)")
        print("3. Try different jumper wires")
        print("4. Check if the display works with other devices")
        return
    
    # Test OLED specifically
    if 0x3C in devices:
        test_oled_communication(i2c, 0x3C)
    elif 0x3D in devices:
        print("Found device at 0x3D instead of 0x3C")
        test_oled_communication(i2c, 0x3D)
    else:
        print("OLED not found at expected addresses (0x3C or 0x3D)")
        print("Available devices:", [hex(d) for d in devices])
    
    # Test different frequencies
    i2c_pins = (Pin(0), Pin(1))
    working_freq = test_different_frequencies(i2c_pins)
    
    if working_freq:
        print(f"\n✅ Recommended I2C frequency: {working_freq//1000}kHz")
    
    print("\n=== Diagnostic Complete ===")

if __name__ == "__main__":
    main()
