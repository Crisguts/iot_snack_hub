from gpiozero import Motor, OutputDevice
from time import sleep

# Define pins
enable = OutputDevice(22)  # Enable Pin
motor = Motor(forward=17, backward=27)  # Forward and Backward Pins


def turnFanOn():
    enable.on()
    motor.forward()
    print("Fan turned on.")

def turnFanOff():
    motor.stop()
    enable.off()
    print("Fan turned off.")



# # Run motor forward
# print("Running motor: forward direction.")
# motor.forward()
# sleep(5)

# # Run motor backward
# print("Running motor: reverse direction.")
# motor.backward()
# sleep(5)

# # Disable the motor
# print("Disabling motor.")
# enable.off()