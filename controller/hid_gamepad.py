import struct
import time

class Gamepad:
    def __init__(self, devices):
        self._gamepad_device = None
        for dev in devices:
            if dev.usage_page == 0x01 and dev.usage == 0x05:
                self._gamepad_device = dev
                break
        if not self._gamepad_device:
            raise RuntimeError("Gamepad HID device not found. Check boot.py")
        self._report = bytearray(6)
        self._last_report = bytearray(6)

    def move_joysticks(self, x=0, y=0, z=0, r_z=0):
        self._report[2] = self._validate(x)
        self._report[3] = self._validate(y)
        self._report[4] = self._validate(z)
        self._report[5] = self._validate(r_z)
        self._send()

    def _validate(self, val):
        return max(-127, min(127, val)) & 0xFF

    def press_buttons(self, *buttons):
        for b in buttons:
            self._report[b // 8] |= (1 << (b % 8))
        self._send()

    def release_buttons(self, *buttons):
        for b in buttons:
            self._report[b // 8] &= ~(1 << (b % 8))
        self._send()

    def _send(self):
        if self._report != self._last_report:
            self._gamepad_device.send_report(self._report, 4)
            self._last_report[:] = self._report