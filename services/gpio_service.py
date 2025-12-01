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
        if Device.pin_factory is not None:
            logger.info("Closing existing pin factory...")
            Device.pin_factory.close()
            Device.pin_factory = None  # Force reset
    except Exception as cleanup_error:
        logger.warning(f"Pin factory cleanup warning: {cleanup_error}")
    
    try:
        logger.info(f"Initializing GPIO pins: LED blue={BLUE_LED_PIN}, red={RED_LED_PIN}, buzzer={BUZZER_PIN}, enable={ENABLE_PIN}, motor fwd={MOTOR_FORWARD_PIN} bwd={MOTOR_BACKWARD_PIN}")
        blue_led = LED(BLUE_LED_PIN)
        red_led = LED(RED_LED_PIN)
        buzzer = Buzzer(BUZZER_PIN)
        enable = OutputDevice(ENABLE_PIN)
        motor = Motor(forward=MOTOR_FORWARD_PIN, backward=MOTOR_BACKWARD_PIN)
        _gpio_initialized = True
        logger.info("✅ GPIO hardware initialized successfully - REAL HARDWARE READY")
    except Exception as e:
        import traceback
        logger.error(f"❌ GPIO init failed: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        # Create mock objects as fallback
        from unittest.mock import MagicMock
        blue_led = MagicMock()
        red_led = MagicMock()
        buzzer = MagicMock()
        enable = MagicMock()
        motor = MagicMock()
        GPIO_AVAILABLE = False
        _gpio_initialized = True
        logger.error("⚠️  Using MagicMock objects - HARDWARE WILL NOT WORK")

# Auto-initialize on import
_initialize_gpio()

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
    """Turn on the fan motor for specified fridge"""
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        
        # Diagnostic: Check if GPIO objects are real or mocks
        enable_type = type(enable).__name__
        motor_type = type(motor).__name__
        logger.info(f"turn_fan_on called - enable type: {enable_type}, motor type: {motor_type}")
        logger.info(f"GPIO_AVAILABLE: {GPIO_AVAILABLE}, _gpio_initialized: {_gpio_initialized}")
        
        # CRITICAL: Prevent MagicMock calls - raise error if not real hardware
        if enable_type == 'MagicMock' or motor_type == 'MagicMock':
            error_msg = f"Cannot control fan - GPIO hardware not available (enable: {enable_type}, motor: {motor_type})"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Control hardware
        enable.on()
        motor.backward()
        fan_states[fridge_id] = True
        logger.info(f"Fan {fridge_id} turned ON - motor spinning")
    except Exception as e:
        logger.error(f"Error turning ON fan {fridge_id}: {e}")
        raise

def turn_fan_off(fridge_id=1):
    """Turn off the fan motor for specified fridge"""
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        
        # CRITICAL: Prevent MagicMock calls
        if type(enable).__name__ == 'MagicMock' or type(motor).__name__ == 'MagicMock':
            error_msg = "Cannot control fan - GPIO hardware not available"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Update state first
        fan_states[fridge_id] = False
        
        # Only stop motor if both fridges are off
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

def force_reinitialize_gpio():
    """Force GPIO reinitialization - use when GPIO gets into bad state"""
    global _gpio_initialized
    logger.info("🔄 Force reinitializing GPIO...")
    _gpio_initialized = False  # Reset flag
    _initialize_gpio()
    return type(enable).__name__ != 'MagicMock'  # Return True if real hardware

def get_motor_state():
    return any(fan_states.values())
