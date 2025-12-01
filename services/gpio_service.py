# services/gpio_service.py
import logging
import time

try:
    from gpiozero import LED, Buzzer, Motor, OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    LED = Buzzer = Motor = OutputDevice = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hardware pin assignments
BLUE_LED_PIN = 21
RED_LED_PIN = 20
BUZZER_PIN = 16
ENABLE_PIN = 22
MOTOR_FORWARD_PIN = 17
MOTOR_BACKWARD_PIN = 27

# Initialize GPIO components
blue_led = None
red_led = None
buzzer = None
enable = None
motor = None

if GPIO_AVAILABLE:
    try:
        import os
        # Check if running on actual Pi hardware
        if not os.path.exists('/dev/gpiomem'):
            logger.warning("Not running on Raspberry Pi hardware")
        else:
            # Try to use RPi.GPIO pin factory for better compatibility
            try:
                from gpiozero.pins.rpigpio import RPiGPIOFactory
                from gpiozero import Device
                Device.pin_factory = RPiGPIOFactory()
            except:
                pass  # Use default factory
            
            blue_led = LED(BLUE_LED_PIN)
            red_led = LED(RED_LED_PIN)
            buzzer = Buzzer(BUZZER_PIN)
            enable = OutputDevice(ENABLE_PIN)
            motor = Motor(forward=MOTOR_FORWARD_PIN, backward=MOTOR_BACKWARD_PIN)
            logger.info("GPIO hardware initialized successfully")
    except Exception as e:
        import traceback
        logger.error(f"GPIO initialization failed: {e}")
        logger.error(traceback.format_exc())
        blue_led = red_led = buzzer = enable = motor = None
else:
    logger.warning("gpiozero library not available")

fan_states = {1: False, 2: False}


def blink(led_color: str, times: int = 3, delay: float = 0.3):
    if not GPIO_AVAILABLE or not blue_led or not red_led or not buzzer:
        return
        
    try:
        led = blue_led if led_color == "blue" else red_led
        use_buzzer = (led_color == "red")
        
        for _ in range(times):
            led.on()
            if use_buzzer:
                buzzer.on()
            time.sleep(delay)
            led.off()
            if use_buzzer:
                buzzer.off()
            time.sleep(delay)
    except Exception as e:
        logger.error(f"Error in blink: {e}")


def turn_fan_on(fridge_id=1):
    """Turn on the fan motor for specified fridge"""
    if fridge_id not in fan_states:
        raise ValueError(f"Invalid fridge_id: {fridge_id}")
    
    if not GPIO_AVAILABLE or not enable or not motor:
        raise RuntimeError("GPIO hardware not available")
    
    try:
        enable.on()
        motor.backward()
        fan_states[fridge_id] = True
        logger.info(f"Fan {fridge_id} turned ON")
    except Exception as e:
        logger.error(f"Error turning ON fan {fridge_id}: {e}")
        raise

def turn_fan_off(fridge_id=1):
    """Turn off the fan motor for specified fridge"""
    if fridge_id not in fan_states:
        raise ValueError(f"Invalid fridge_id: {fridge_id}")
    
    if not GPIO_AVAILABLE or not enable or not motor:
        raise RuntimeError("GPIO hardware not available")
    
    try:
        fan_states[fridge_id] = False
        
        # Only stop motor if both fridges are off
        if not any(fan_states.values()):
            motor.stop()
            enable.off()
            logger.info(f"Fan {fridge_id} turned OFF - motor stopped")
        else:
            logger.info(f"Fan {fridge_id} turned OFF - motor still running for other fridge")
    except Exception as e:
        logger.error(f"Error turning OFF fan {fridge_id}: {e}")
        raise

def get_fan_state(fridge_id=None):
    if fridge_id is None:
        return fan_states
    return fan_states.get(fridge_id, None)

def get_motor_state():
    return any(fan_states.values())
