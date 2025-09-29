from gpiozero import LED, Buzzer
from time import sleep

def blink(led_color):
    if led_color == "blue":
        led = LED(21) # SET THE BLUE PIN TO GPIO 21
    elif led_color == "red":
        led = LED(20) # SET THE RED PIN TO GPIO 20
        buzzer = Buzzer(16) # SET THE BUZZER TO GPIO 16
    for _ in range(4): # BLINK THE LED 4 TIMES
        led.on()
        if buzzer:
            buzzer.on()
        sleep(0.5)
        led.off()
        if buzzer:
            buzzer.off()
        sleep(0.5)

    # Clean up - Close the GPIO resources
    led.close()
    if buzzer:
        buzzer.close()


