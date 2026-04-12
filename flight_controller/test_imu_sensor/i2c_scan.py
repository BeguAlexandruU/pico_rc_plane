from machine import Pin, I2C
from time import sleep

LED = machine.Pin("LED", Pin.OUT)
LED.on
print("wait...")
sleep(3)
i2c = I2C(0, sda=Pin(16), scl=Pin(17))


print("Scaninc I2C devices...")
devices = i2c.scan()

if not devices:
    print("No I2C devices found!")
    LED.off()  # Indicate error
    while True: pass  # Halt

print("Dispozitive I2C detectate:", [hex(addr) for addr in devices])

