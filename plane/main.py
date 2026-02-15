import imu_module
import nrf_module
import motor_control
import pid_controller
import servo_control

# ==== for me
# gpio 28 
# gpio 27
# gpio 26
# gpio 22

def setup():
    motor_control.setup()
    servo_control.setup()
    
    imu_module.setup()
    nrf_module.setup()
    pid_controller.setup()


setup()    
while True:
    
    nrf_module.update()
    # print("Channels: {:3d} {:3d} {:3d} {:3d}".format(nrf_module.ch1, nrf_module.ch2, nrf_module.ch3, nrf_module.ch4), end="\r")
    
    imu_module.update()
    # print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format(imu_module.fusion.heading, imu_module.fusion.pitch, imu_module.fusion.roll), end="\r")
    
    pid_controller.update()
