# services/gpio_service.py
# DC Motor Control for Refrigerator Cooling Fans
# Manages GPIO hardware, fan state tracking, and LED/buzzer alerts

import logging
import time
from unittest.mock import MagicMock

try:
    from gpiozero import LED, Buzzer, Motor, OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    LED = Buzzer = Motor = OutputDevice = MagicMock
    GPIO_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Raspberry Pi GPIO pin assignments for hardware components
BLUE_LED_PIN = 21
RED_LED_PIN = 20
BUZZER_PIN = 16
ENABLE_PIN = 22          # Motor enable control
MOTOR_FORWARD_PIN = 17
MOTOR_BACKWARD_PIN = 27

# Initialize GPIO components (only once)
blue_led = None
red_led = None
buzzer = None
enable = None
motor = None
_gpio_initialized = False

def _initialize_gpio():
    """Initialize GPIO hardware once. Called on first import."""
    global blue_led, red_led, buzzer, enable, motor, _gpio_initialized, GPIO_AVAILABLE
    
    if _gpio_initialized:
        logger.info("GPIO already initialized, skipping")
        return
    
    try:
        # Force cleanup of any existing GPIO state
        from gpiozero import Device
        Device.pin_factory.close()
    except:
        pass  # Ignore if nothing to close
    
    try:
        blue_led = LED(BLUE_LED_PIN)
        red_led = LED(RED_LED_PIN)
        buzzer = Buzzer(BUZZER_PIN)
        enable = OutputDevice(ENABLE_PIN)
        motor = Motor(forward=MOTOR_FORWARD_PIN, backward=MOTOR_BACKWARD_PIN)
        _gpio_initialized = True
        logger.info("GPIO hardware initialized successfully")
    except Exception as e:
        logger.error(f"GPIO init failed: {e}")
        # Create mock objects as fallback
        from unittest.mock import MagicMock
        blue_led = MagicMock()
        red_led = MagicMock()
        buzzer = MagicMock()
        enable = MagicMock()
        motor = MagicMock()
        GPIO_AVAILABLE = False
        _gpio_initialized = True

# Auto-initialize on import
_initialize_gpio()

# Track fan state for both refrigerators (shared motor)
fan_states = {1: False, 2: False}


def blink(led_color: str, times: int = 3, delay: float = 0.3):
    try:
        if blue_led is None or red_led is None or buzzer is None:
            logger.warning("GPIO not initialized, cannot blink")
            return
            
        led = blue_led if led_color == "blue" else red_led
        use_buzzer = (led_color == "red")
        logger.info(f"Blinking {led_color} LED ({times}x)")
        
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
    """Activate cooling fan motor for specified refrigerator"""
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        
        # Activate motor (backward direction provides optimal airflow)
        enable.on()
        motor.backward()
        fan_states[fridge_id] = True
        logger.info(f"Fan {fridge_id} turned ON - motor spinning")
    except Exception as e:
        logger.error(f"Error turning ON fan {fridge_id}: {e}")
        raise

def turn_fan_off(fridge_id=1):
    """Deactivate fan for specified refrigerator (smart shutdown)"""
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        
        fan_states[fridge_id] = False
        
        # Only stop physical motor if both fridges are off (extends motor life)
        if not any(fan_states.values()):
            motor.stop()
            enable.off()
            logger.info(f"Fan {fridge_id} turned OFF - motor stopped")
        else:
            logger.info(f"Fan {fridge_id} turned OFF - motor still running for fridge 2")
    except Exception as e:
        logger.error(f"Error turning OFF fan {fridge_id}: {e}")
        raise

def get_fan_state(fridge_id=None):
    if fridge_id is None:
        return fan_states
    return fan_states.get(fridge_id, None)

def get_motor_state():
    return any(fan_states.values())