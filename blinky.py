import board, digitalio, time
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
while True:
   led.value = not led.value
   time.sleep(0.5) 