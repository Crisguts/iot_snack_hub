# services/gpio_service.py
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

try:
    blue_led = LED(BLUE_LED_PIN)
    red_led = LED(RED_LED_PIN)
    buzzer = Buzzer(BUZZER_PIN)
    enable = OutputDevice(ENABLE_PIN)
    motor = Motor(forward=MOTOR_FORWARD_PIN, backward=MOTOR_BACKWARD_PIN)
    logger.info("GPIO hardware initialized successfully")
except Exception as e:
    logger.error(f"GPIO init failed: {e}")
    # Create mock objects as fallback - MagicMock is already imported at top
    from unittest.mock import MagicMock
    blue_led = MagicMock()
    red_led = MagicMock()
    buzzer = MagicMock()
    enable = MagicMock()
    motor = MagicMock()
    GPIO_AVAILABLE = False

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
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        
        if enable is None or motor is None:
            raise RuntimeError("GPIO hardware not initialized")
        
        # Always control hardware to ensure sync
        enable.on()
        motor.backward()
        fan_states[fridge_id] = True
        logger.info(f"Fan {fridge_id} turned ON.")
    except Exception as e:
        logger.error(f"Error turning ON fan {fridge_id}: {e}")
        raise

def turn_fan_off(fridge_id=1):
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        
        if enable is None or motor is None:
            raise RuntimeError("GPIO hardware not initialized")
        
        # Update state first
        fan_states[fridge_id] = False
        
        # Only stop motor if both fridges are off
        if not any(fan_states.values()):
            motor.stop()
            enable.off()
            logger.info(f"Fan {fridge_id} turned OFF - motor stopped.")
        else:
            logger.info(f"Fan {fridge_id} turned OFF - motor still running for other fridge.")
    except Exception as e:
        logger.error(f"Error turning OFF fan {fridge_id}: {e}")
        raise

def get_fan_state(fridge_id=None):
    if fridge_id is None:
        return fan_states
    return fan_states.get(fridge_id, None)

def get_motor_state():
    return any(fan_states.values())
