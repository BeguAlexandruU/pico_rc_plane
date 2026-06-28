import imu_module
import nrf_module
import motor_control
import pid_controller
import servo_control
import gps_module
import utime
import machine

# ==== for me
# gpio 28
# gpio 27
# gpio 26
# gpio 22

machine.freq(250000000)

LOOP_FREQ = 100 # Hz
TARGET_PERIOD = 1_000_000 // LOOP_FREQ # microseconds

def setup():
    motor_control.setup()
    servo_control.setup()

    gps_module.setup()
    imu_module.setup()
    nrf_module.setup()
    pid_controller.setup()


setup()

_last_period_start = utime.ticks_us()
_loop_n = 0

while True:
    start_tick = utime.ticks_us()

    nrf_module.update()
    imu_module.update()
    pid_controller.update()
    gps_module.update()

    elapsed = utime.ticks_diff(utime.ticks_us(), start_tick)

    if elapsed < TARGET_PERIOD:
        utime.sleep_us(TARGET_PERIOD - elapsed)

    # # Măsoară perioada completă (muncă + sleep) după ce iterația s-a terminat.
    # # Printul este scos din fereastra de timp măsurată, deci nu distorsionează frecvența.
    # now = utime.ticks_us()
    # full_period = utime.ticks_diff(now, _last_period_start)
    # _last_period_start = now

    # _loop_n += 1
    # if _loop_n >= 50:
    #     freq = 1_000_000 / full_period if full_period > 0 else 0
    #     print(f"Freq: {freq:.1f} Hz  work: {elapsed} us / {TARGET_PERIOD} us", end="\r")
    #     _loop_n = 0

