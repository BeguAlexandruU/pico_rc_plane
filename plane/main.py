import imu_module
import nrf_module

def setup():
    imu_module.setup()
    nrf_module.setup()


setup()    
while True:
    imu_module.update()
    # nrf_module.update()
    print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format(imu_module.fusion.heading, imu_module.fusion.pitch, imu_module.fusion.roll), end="\r")


