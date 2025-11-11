# services/gpio_service.py
import logging
import time

try:
    from gpiozero import LED, Buzzer, Motor, OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    from unittest.mock import MagicMock
    LED = Buzzer = Motor = OutputDevice = MagicMock
    GPIO_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Hardware setup ---
# LED + Buzzer Pins
BLUE_LED_PIN = 21
RED_LED_PIN = 20
BUZZER_PIN = 16

# Motor pins
ENABLE_PIN = 22
MOTOR_FORWARD_PIN = 17
MOTOR_BACKWARD_PIN = 27

# --- Initialize Components ---
try:
    blue_led = LED(BLUE_LED_PIN)
    red_led = LED(RED_LED_PIN)
    buzzer = Buzzer(BUZZER_PIN)
    enable = OutputDevice(ENABLE_PIN)
    motor = Motor(forward=MOTOR_FORWARD_PIN, backward=MOTOR_BACKWARD_PIN)
except Exception as e:
    logger.warning(f"GPIO init failed (mock mode likely): {e}")

fan_states = {1: False, 2: False}

# --- LED / Buzzer alert ---
def blink(led_color: str, times: int = 3, delay: float = 0.3):
    try:
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

# --- Fan / Motor control ---
def turn_fan_on(fridge_id=1):
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        if fan_states[fridge_id]:
            logger.info(f"Fan {fridge_id} already on.")
            return
        
        enable.on()
        motor.backward()
        fan_states[fridge_id] = True
        logger.info(f"Fan {fridge_id} turned ON.")
    except Exception as e:
        logger.error(f"Error turning ON fan {fridge_id}: {e}")

def turn_fan_off(fridge_id=1):
    try:
        if fridge_id not in fan_states:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
        fan_states[fridge_id] = False
        if not any(fan_states.values()):
            motor.stop()
            enable.off()
        logger.info(f"Fan {fridge_id} turned OFF.")
    except Exception as e:
        logger.error(f"Error turning OFF fan {fridge_id}: {e}")

def get_fan_state(fridge_id=None):
    if fridge_id is None:
        return fan_states
    return fan_states.get(fridge_id, None)

def get_motor_state():
    return any(fan_states.values())
