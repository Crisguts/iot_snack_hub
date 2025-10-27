from gpiozero import Motor, OutputDevice
from time import sleep
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

enable = OutputDevice(22)
motor = Motor(forward=17, backward=27)

# enable2 = OutputDevice(23)
# motor2 = Motor(forward=24, backward=25)

fan_states = {
    1: False,
    2: False
}

def turnFanOn(fridge_id=1):
    try:
        logger.info(f"Turning ON fan for Fridge {fridge_id}")
        
        if fridge_id == 1:
            if not fan_states[1]:
                enable.on()
                motor.backward()
                fan_states[1] = True
                logger.info(f"Motor 1 (Fridge {fridge_id}) turned ON")
                logger.info(f"Enable pin active: {enable.is_active}")
                logger.info(f"Motor backward value: {motor.value}")
            else:
                logger.info(f"Motor 1 (Fridge {fridge_id}) already running")
                
        elif fridge_id == 2:
            if not any(fan_states.values()):
                enable.on()
                motor.backward()
                logger.info(f"Demo: Motor turned ON for Fridge {fridge_id}")
            fan_states[2] = True
            logger.info(f"Fridge {fridge_id} fan state set to ON")
            
        else:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
            
    except Exception as e:
        logger.error(f"Error turning on fan for fridge {fridge_id}: {e}")
        raise

def turnFanOff(fridge_id=1):
    try:
        logger.info(f"Turning OFF fan for Fridge {fridge_id}")
        
        if fridge_id == 1:
            fan_states[1] = False
            if not any(fan_states.values()):
                motor.stop()
                enable.off()
                logger.info(f"Motor 1 (Fridge {fridge_id}) turned OFF")
            else:
                logger.info(f"Motor 1 stays ON (other fans running)")
                
        elif fridge_id == 2:
            fan_states[2] = False
            if not any(fan_states.values()):
                motor.stop()
                enable.off()
                logger.info(f"Demo: Motor turned OFF (no fans running)")
            logger.info(f"Fridge {fridge_id} fan state set to OFF")
            
        else:
            raise ValueError(f"Invalid fridge_id: {fridge_id}")
            
    except Exception as e:
        logger.error(f"Error turning off fan for fridge {fridge_id}: {e}")
        raise

def getFanState(fridge_id=None):
    if fridge_id is None:
        return fan_states
    elif fridge_id in [1, 2]:
        return fan_states[fridge_id]
    else:
        raise ValueError(f"Invalid fridge_id: {fridge_id}")

def getMotorState():
    return any(fan_states.values())