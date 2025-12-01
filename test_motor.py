#!/usr/bin/env python3
"""
Motor/Fan Hardware Test Script
Tests the motor functionality directly without the web app
"""
import time
import sys

try:
    from gpiozero import Motor, OutputDevice
    GPIO_AVAILABLE = True
    print("✓ GPIO library loaded successfully")
except ImportError:
    print("✗ GPIO library not available - install gpiozero:")
    print("  pip3 install gpiozero pigpio")
    sys.exit(1)

# Pin definitions (from gpio_service.py)
MOTOR_FORWARD_PIN = 17
MOTOR_BACKWARD_PIN = 27
ENABLE_PIN = 22

print("\n=== Motor Hardware Test ===")
print(f"Motor Forward Pin: GPIO {MOTOR_FORWARD_PIN}")
print(f"Motor Backward Pin: GPIO {MOTOR_BACKWARD_PIN}")
print(f"Enable Pin: GPIO {ENABLE_PIN}")

try:
    # Initialize hardware
    print("\n1. Initializing motor...")
    motor = Motor(forward=MOTOR_FORWARD_PIN, backward=MOTOR_BACKWARD_PIN)
    enable = OutputDevice(ENABLE_PIN)
    print("✓ Motor initialized")
    
    # Test 1: Turn motor backward (fan ON)
    print("\n2. Testing motor BACKWARD (Fan ON) for 3 seconds...")
    enable.on()
    motor.backward()
    print("   Motor should be spinning now!")
    print("   Check if fan is spinning...")
    time.sleep(3)
    
    # Stop motor
    print("\n3. Stopping motor...")
    motor.stop()
    enable.off()
    print("   Motor should be stopped")
    time.sleep(2)
    
    # Test 2: Turn motor forward (alternate direction)
    print("\n4. Testing motor FORWARD for 2 seconds...")
    enable.on()
    motor.forward()
    print("   Motor spinning in opposite direction...")
    time.sleep(2)
    
    # Stop motor
    print("\n5. Stopping motor...")
    motor.stop()
    enable.off()
    print("   Motor stopped")
    
    print("\n=== Test Complete ===")
    print("If the motor didn't spin, check:")
    print("  1. Wiring connections (GPIO 17, 27, 22)")
    print("  2. Motor driver power supply")
    print("  3. Motor driver enable jumper")
    print("  4. Motor connections to driver")
    
except Exception as e:
    print(f"\n✗ Error during test: {e}")
    print("\nTroubleshooting:")
    print("  - Verify GPIO pins are not in use by another program")
    print("  - Check physical connections")
    print("  - Try running with sudo: sudo python3 test_motor.py")
    sys.exit(1)
