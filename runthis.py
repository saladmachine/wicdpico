# runthis.py - Controllable module for web interface
import board
import digitalio
import time

# Global control flag
running = False

def run_blinky():
    """Blinky function that can be controlled via global flag"""
    global running
    
    # Setup LED
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    
    print("Blinky started - check 'running' flag to stop")
    
    # Controlled loop - checks flag each iteration
    while running:
        led.value = not led.value
        print(f"LED: {'ON' if led.value else 'OFF'}")
        time.sleep(0.5)
    
    # Clean shutdown
    led.value = False
    print("Blinky stopped")

def start():
    """Start the blinky function"""
    global running
    running = True
    run_blinky()

def stop():
    """Stop the blinky function"""
    global running
    running = False

def is_running():
    """Check if currently running"""
    return running

# For direct testing
if __name__ == "__main__":
    start()