import board
import digitalio
import time
 
# Configurable blink interval (seconds)
BLINK_INTERVAL = 0.25

# Setup LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Blink timing
last_blink = time.monotonic()
led_state = False

def update_blinky():
    global last_blink, led_state
    current_time = time.monotonic()
    
    if current_time - last_blink >= BLINK_INTERVAL:
        led_state = not led_state
        led.value = led_state
        last_blink = current_time
