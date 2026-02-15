import imu_module
import nrf_module
import motor_control
import servo_control
from pid_controller import PID

# ==== for me
# gpio 28 
# gpio 27
# gpio 26
# gpio 22

roll_pid = PID(kp=1.2, ki=0.1, kd=0.05, output_limits=(-127, 127))
pitch_pid = PID(kp=1.2, ki=0.1, kd=0.05, output_limits=(-127, 127))

def setup():
    motor_control.setup()
    servo_control.setup()
    
    imu_module.setup()
    nrf_module.setup()

ROLL_SLOPE = (30 - (-30)) / (127 - (-127))
def map_input_to_angle(x):
    # Simplified Formula: (x - in_min) * slope + out_min
    return (x + 127) * ROLL_SLOPE - 30

setup()    
while True:
    imu_module.update()
    # print("Heading, Pitch, Roll: {:7.3f} {:7.3f} {:7.3f}".format(imu_module.fusion.heading, imu_module.fusion.pitch, imu_module.fusion.roll), end="\r")
    
    nrf_module.update()
    # print("Channels: {:3d} {:3d} {:3d} {:3d}".format(nrf_module.ch1, nrf_module.ch2, nrf_module.ch3, nrf_module.ch4), end="\r")
    
    # 2. Convert NRF Stick (0-255) to Target Angle (-30 to +30 degrees)
    target_roll = map_input_to_angle(nrf_module.ch3)
    target_pitch = map_input_to_angle(nrf_module.ch4)
    
    # 3. Get Actual Angles from IMU
    current_roll = imu_module.fusion.roll
    current_pitch = imu_module.fusion.pitch
    
    # 4. Compute PID correction
    # The PID returns a value in the -127 to 127 range for your servo_control
    aileron_output = roll_pid.compute(target_roll, current_roll)
    elevator_output = pitch_pid.compute(target_pitch, current_pitch)
    
    servo_control.set_aileron(aileron_output)
    servo_control.set_elevator(elevator_output)
