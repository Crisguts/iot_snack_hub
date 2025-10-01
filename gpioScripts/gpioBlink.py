import RPi.GPIO as GPIO 
from time import sleep 

GPIO.setwarnings(False) 
GPIO.setmode(GPIO.BCM) 

def blink(led_color):
    if led_color == "blue":
        LED=21 # SET THE BLUE PIN TO GPIO 21
        GPIO.setup(LED, GPIO.OUT) 
    elif led_color == "red":
        LED=20 # SET THE RED PIN TO GPIO 20
        GPIO.setup(LED, GPIO.OUT) 
        buzzer = 16 # SET THE BUZZER TO GPIO 16
        GPIO.setup(buzzer, GPIO.OUT)
        
    for _ in range(4): # BLINK THE LED 4 TIMES
        GPIO.output(LED, GPIO.HIGH) # Turn on
        if led_color == "red":
            GPIO.output(buzzer, GPIO.HIGH) # Turn on buzzer
        sleep(0.5)
        GPIO.output(LED, GPIO.LOW) # Turn off
        if led_color == "red":
            GPIO.output(buzzer, GPIO.LOW) # Turn off buzzer
        sleep(0.5)
    
    GPIO.cleanup() # Clean up - Reset GPIO settings