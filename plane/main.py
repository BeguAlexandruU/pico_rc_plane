import imu_module
import nrf_module
import motor_control
import pid_controller
import servo_control
import utime

# ==== for me
# gpio 28 
# gpio 27
# gpio 26
# gpio 22

LOOP_FREQ = 100 # Hz
TARGET_PERIOD = 1_000_000 // LOOP_FREQ # microseconds

def setup():
    motor_control.setup()
    servo_control.setup()
    
    imu_module.setup()
    nrf_module.setup()
    pid_controller.setup()


setup()    


# last_time = utime.ticks_us()
while True:
    
    # # 1. Calculate Delta Time
    # current_time = utime.ticks_us()
    # # ticks_diff handles the internal counter wrap-around
    # dt = utime.ticks_diff(current_time, last_time) / 1_000_000 
    # last_time = current_time
    
    # # Avoid division by zero
    # if dt > 0:
    #     frequency = 1 / dt
    #     print(f"Freq: {frequency:.2f} Hz", end="\r")


    start_tick = utime.ticks_us()


    nrf_module.update()
    # print("Channels: {:3d} {:3d} {:3d} {:3d}".format(nrf_module.ch1, nrf_module.ch2, nrf_module.ch3, nrf_module.ch4), end="\r")
    
    imu_module.update()
    # print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format(imu_module.fusion.heading, imu_module.fusion.pitch, imu_module.fusion.roll), end="\r")
    
    pid_controller.update()

    # Calculate how long the work took
    elapsed = utime.ticks_diff(utime.ticks_us(), start_tick)
    
    # Wait for the remaining time to hit exactly 100Hz
    if elapsed < TARGET_PERIOD:
        utime.sleep_us(TARGET_PERIOD - elapsed)
