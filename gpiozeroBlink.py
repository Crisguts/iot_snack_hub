from gpiozero import LED, Buzzer
from time import sleep

def blink(led_color):
    buzzer = None  # Initialize buzzer variable
    
    if led_color == "blue":
        led = LED(21) # SET THE BLUE PIN TO GPIO 21
    elif led_color == "red":
        led = LED(20) # SET THE RED PIN TO GPIO 20
        buzzer = Buzzer(16) # SET THE BUZZER TO GPIO 16
    for _ in range(2): # BLINK THE LED 3 TIMES
        led.on()
        if buzzer:
            buzzer.on()
        sleep(0.1)
        
        if buzzer:
            buzzer.off()
        led.off()
        sleep(0.1)

    # Clean up - Close the GPIO resources
    led.close()
    if buzzer:
        buzzer.close()


