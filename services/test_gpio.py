#!/usr/bin/env python3
"""
test_gpio.py - Standalone GPIO Motor Debug Script

Run this script directly on your Raspberry Pi to test motor control
without needing the Flask frontend.

Usage:
    python3 test_gpio.py              # Run all tests
    python3 test_gpio.py --motor-only # Skip LED tests, test motor only
    python3 test_gpio.py --interactive # Interactive mode with menu
"""

import sys
import time
import argparse

# Add verbosity to imports
print("=" * 60)
print("GPIO Motor Debug Script")
print("=" * 60)

# Check GPIO library availability
try:
    from gpiozero import LED, Buzzer, Motor, OutputDevice, Device
    print("✅ gpiozero library imported successfully")
    GPIO_AVAILABLE = True
except ImportError as e:
    print(f"❌ gpiozero library not available: {e}")
    print("   Install with: sudo apt-get install python3-gpiozero")
    GPIO_AVAILABLE = False
    sys.exit(1)

# Check hardware availability
import os
if not os.path.exists('/dev/gpiomem'):
    print("❌ /dev/gpiomem not found - not running on Raspberry Pi hardware")
    print("   This script must be run on a Raspberry Pi")
    sys.exit(1)
else:
    print("✅ /dev/gpiomem found - Raspberry Pi hardware detected")

# Check user permissions
if not os.access('/dev/gpiomem', os.R_OK | os.W_OK):
    print("⚠️  WARNING: No read/write access to /dev/gpiomem")
    print(f"   Current user: {os.getenv('USER')}")
    print("   You may need to add user to 'gpio' group:")
    print("   sudo usermod -a -G gpio $USER")
    print("   Then log out and log back in")

# Pin definitions (matching gpio_service.py)
BLUE_LED_PIN = 21
RED_LED_PIN = 20
BUZZER_PIN = 16
ENABLE_PIN = 22
MOTOR_FORWARD_PIN = 17
MOTOR_BACKWARD_PIN = 27

print("\nPin Configuration:")
print(f"  Blue LED:       GPIO {BLUE_LED_PIN}")
print(f"  Red LED:        GPIO {RED_LED_PIN}")
print(f"  Buzzer:         GPIO {BUZZER_PIN}")
print(f"  Motor Enable:   GPIO {ENABLE_PIN}")
print(f"  Motor Forward:  GPIO {MOTOR_FORWARD_PIN}")
print(f"  Motor Backward: GPIO {MOTOR_BACKWARD_PIN}")
print("=" * 60)

# Initialize hardware components
blue_led = None
red_led = None
buzzer = None
enable = None
motor = None

def initialize_hardware():
    """Initialize all GPIO components with detailed error reporting"""
    global blue_led, red_led, buzzer, enable, motor
    
    print("\n🔧 Initializing Hardware...")
    
    try:
        # Set pin factory for better compatibility
        try:
            from gpiozero.pins.rpigpio import RPiGPIOFactory
            Device.pin_factory = RPiGPIOFactory()
            print("  ✅ Using RPi.GPIO pin factory")
        except Exception as e:
            print(f"  ⚠️  Using default pin factory: {e}")
        
        # Initialize each component separately for better error tracking
        try:
            blue_led = LED(BLUE_LED_PIN)
            print(f"  ✅ Blue LED initialized on GPIO {BLUE_LED_PIN}")
        except Exception as e:
            print(f"  ❌ Blue LED failed: {e}")
        
        try:
            red_led = LED(RED_LED_PIN)
            print(f"  ✅ Red LED initialized on GPIO {RED_LED_PIN}")
        except Exception as e:
            print(f"  ❌ Red LED failed: {e}")
        
        try:
            buzzer = Buzzer(BUZZER_PIN)
            print(f"  ✅ Buzzer initialized on GPIO {BUZZER_PIN}")
        except Exception as e:
            print(f"  ❌ Buzzer failed: {e}")
        
        try:
            enable = OutputDevice(ENABLE_PIN)
            print(f"  ✅ Enable pin initialized on GPIO {ENABLE_PIN}")
        except Exception as e:
            print(f"  ❌ Enable pin failed: {e}")
            return False
        
        try:
            motor = Motor(forward=MOTOR_FORWARD_PIN, backward=MOTOR_BACKWARD_PIN)
            print(f"  ✅ Motor initialized (Forward: GPIO {MOTOR_FORWARD_PIN}, Backward: GPIO {MOTOR_BACKWARD_PIN})")
        except Exception as e:
            print(f"  ❌ Motor failed: {e}")
            return False
        
        print("✅ Hardware initialization complete!\n")
        return True
        
    except Exception as e:
        print(f"❌ Hardware initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_pin_states():
    """Check and display current state of all pins"""
    print("\n📊 Current Pin States:")
    
    try:
        if blue_led:
            print(f"  Blue LED:      {'ON' if blue_led.value else 'OFF'} (value: {blue_led.value})")
        if red_led:
            print(f"  Red LED:       {'ON' if red_led.value else 'OFF'} (value: {red_led.value})")
        if buzzer:
            print(f"  Buzzer:        {'ON' if buzzer.value else 'OFF'} (value: {buzzer.value})")
        if enable:
            print(f"  Enable Pin:    {'HIGH' if enable.value else 'LOW'} (value: {enable.value})")
        if motor:
            print(f"  Motor Value:   {motor.value}")
            print(f"  Motor Forward: {'ON' if hasattr(motor, 'forward_device') and motor.forward_device.value else 'OFF'}")
            print(f"  Motor Backward: {'ON' if hasattr(motor, 'backward_device') and motor.backward_device.value else 'OFF'}")
    except Exception as e:
        print(f"  ❌ Error reading pin states: {e}")

def test_leds():
    """Test LED functionality"""
    print("\n🔵 Testing LEDs...")
    
    if not blue_led or not red_led:
        print("  ⚠️  LEDs not initialized, skipping test")
        return False
    
    try:
        print("  Testing Blue LED (3 blinks)...")
        for i in range(3):
            blue_led.on()
            print(f"    Blink {i+1}: ON")
            time.sleep(0.5)
            blue_led.off()
            print(f"    Blink {i+1}: OFF")
            time.sleep(0.5)
        
        print("  Testing Red LED (3 blinks)...")
        for i in range(3):
            red_led.on()
            print(f"    Blink {i+1}: ON")
            time.sleep(0.5)
            red_led.off()
            print(f"    Blink {i+1}: OFF")
            time.sleep(0.5)
        
        print("  ✅ LED test complete")
        return True
    except Exception as e:
        print(f"  ❌ LED test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_motor_basic():
    """Test basic motor functionality"""
    print("\n⚙️  Testing Motor (Basic)...")
    
    if not enable or not motor:
        print("  ❌ Motor or enable pin not initialized")
        return False
    
    try:
        print("  Step 1: Setting enable pin HIGH...")
        enable.on()
        time.sleep(0.5)
        check_pin_states()
        
        print("\n  Step 2: Starting motor BACKWARD (fan on)...")
        motor.backward()
        time.sleep(0.5)
        check_pin_states()
        
        print("\n  ⏱️  Motor running for 3 seconds...")
        time.sleep(3)
        
        print("\n  Step 3: Stopping motor...")
        motor.stop()
        time.sleep(0.5)
        check_pin_states()
        
        print("\n  Step 4: Setting enable pin LOW...")
        enable.off()
        time.sleep(0.5)
        check_pin_states()
        
        print("\n  ✅ Motor test complete")
        return True
        
    except Exception as e:
        print(f"  ❌ Motor test failed: {e}")
        import traceback
        traceback.print_exc()
        # Try to safely stop
        try:
            if motor:
                motor.stop()
            if enable:
                enable.off()
        except:
            pass
        return False

def test_motor_extended():
    """Test extended motor functionality (forward, backward, speed control)"""
    print("\n⚙️  Testing Motor (Extended)...")
    
    if not enable or not motor:
        print("  ❌ Motor or enable pin not initialized")
        return False
    
    try:
        # Test backward (normal fan operation)
        print("  Test 1: BACKWARD direction (normal fan)...")
        enable.on()
        motor.backward()
        print("    Motor running backward for 2 seconds...")
        check_pin_states()
        time.sleep(2)
        motor.stop()
        enable.off()
        print("    Stopped")
        time.sleep(1)
        
        # Test forward
        print("\n  Test 2: FORWARD direction...")
        enable.on()
        motor.forward()
        print("    Motor running forward for 2 seconds...")
        check_pin_states()
        time.sleep(2)
        motor.stop()
        enable.off()
        print("    Stopped")
        time.sleep(1)
        
        # Test speed control (if supported)
        print("\n  Test 3: Variable speed (50%)...")
        enable.on()
        motor.backward(speed=0.5)
        print("    Motor at 50% speed for 2 seconds...")
        check_pin_states()
        time.sleep(2)
        motor.stop()
        enable.off()
        print("    Stopped")
        
        print("\n  ✅ Extended motor test complete")
        return True
        
    except Exception as e:
        print(f"  ❌ Extended motor test failed: {e}")
        import traceback
        traceback.print_exc()
        # Try to safely stop
        try:
            if motor:
                motor.stop()
            if enable:
                enable.off()
        except:
            pass
        return False

def test_gpio_service_functions():
    """Test the actual functions from gpio_service.py"""
    print("\n🔍 Testing gpio_service.py functions...")
    
    try:
        # Import the service
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from services.gpio_service import turn_fan_on, turn_fan_off, get_fan_state, get_motor_state
        
        print("  ✅ gpio_service imported successfully")
        
        print("\n  Test: turn_fan_on(1)...")
        turn_fan_on(1)
        print(f"    Fan state: {get_fan_state(1)}")
        print(f"    Motor state: {get_motor_state()}")
        time.sleep(3)
        
        print("\n  Test: turn_fan_off(1)...")
        turn_fan_off(1)
        print(f"    Fan state: {get_fan_state(1)}")
        print(f"    Motor state: {get_motor_state()}")
        time.sleep(1)
        
        print("\n  Test: turn_fan_on(2)...")
        turn_fan_on(2)
        print(f"    Fan state: {get_fan_state(2)}")
        print(f"    Motor state: {get_motor_state()}")
        time.sleep(3)
        
        print("\n  Test: turn_fan_off(2)...")
        turn_fan_off(2)
        print(f"    Fan state: {get_fan_state(2)}")
        print(f"    Motor state: {get_motor_state()}")
        
        print("\n  ✅ gpio_service function tests complete")
        return True
        
    except Exception as e:
        print(f"  ❌ gpio_service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def interactive_mode():
    """Interactive menu for manual testing"""
    print("\n🎮 Interactive Mode")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("  1 - Check pin states")
        print("  2 - Test LEDs")
        print("  3 - Motor ON (backward)")
        print("  4 - Motor OFF")
        print("  5 - Motor FORWARD")
        print("  6 - Enable pin ON")
        print("  7 - Enable pin OFF")
        print("  8 - Test gpio_service functions")
        print("  9 - Run all tests")
        print("  0 - Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "0":
            print("Exiting...")
            break
        elif choice == "1":
            check_pin_states()
        elif choice == "2":
            test_leds()
        elif choice == "3":
            if enable and motor:
                print("Turning motor ON (backward)...")
                enable.on()
                motor.backward()
                check_pin_states()
            else:
                print("❌ Motor not initialized")
        elif choice == "4":
            if enable and motor:
                print("Turning motor OFF...")
                motor.stop()
                enable.off()
                check_pin_states()
            else:
                print("❌ Motor not initialized")
        elif choice == "5":
            if enable and motor:
                print("Turning motor FORWARD...")
                enable.on()
                motor.forward()
                check_pin_states()
            else:
                print("❌ Motor not initialized")
        elif choice == "6":
            if enable:
                print("Enable pin ON...")
                enable.on()
                check_pin_states()
            else:
                print("❌ Enable pin not initialized")
        elif choice == "7":
            if enable:
                print("Enable pin OFF...")
                enable.off()
                check_pin_states()
            else:
                print("❌ Enable pin not initialized")
        elif choice == "8":
            test_gpio_service_functions()
        elif choice == "9":
            run_all_tests(skip_leds=False)
        else:
            print("Invalid choice")

def run_all_tests(skip_leds=False):
    """Run all test sequences"""
    results = []
    
    if not skip_leds:
        results.append(("LED Test", test_leds()))
    
    results.append(("Motor Basic Test", test_motor_basic()))
    results.append(("Motor Extended Test", test_motor_extended()))
    results.append(("GPIO Service Test", test_gpio_service_functions()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    print("=" * 60)

def cleanup():
    """Clean up GPIO resources"""
    print("\n🧹 Cleaning up GPIO resources...")
    try:
        if motor:
            motor.stop()
            motor.close()
        if enable:
            enable.off()
            enable.close()
        if blue_led:
            blue_led.off()
            blue_led.close()
        if red_led:
            red_led.off()
            red_led.close()
        if buzzer:
            buzzer.off()
            buzzer.close()
        print("  ✅ Cleanup complete")
    except Exception as e:
        print(f"  ⚠️  Cleanup error: {e}")

def main():
    parser = argparse.ArgumentParser(description="GPIO Motor Debug Script")
    parser.add_argument("--motor-only", action="store_true", help="Skip LED tests")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--gpio-service", action="store_true", help="Only test gpio_service functions")
    args = parser.parse_args()
    
    try:
        # Initialize hardware
        if not initialize_hardware():
            print("\n❌ Hardware initialization failed. Cannot proceed.")
            return 1
        
        # Check initial states
        check_pin_states()
        
        if args.gpio_service:
            # Only test gpio_service
            test_gpio_service_functions()
        elif args.interactive:
            # Interactive mode
            interactive_mode()
        else:
            # Run all tests
            run_all_tests(skip_leds=args.motor_only)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cleanup()

if __name__ == "__main__":
    sys.exit(main())