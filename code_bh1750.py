# code_bh1750.py - Test harness for the simplified BH1750 module
import gc
import time
import supervisor
import board
import busio

supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO BH1750 LIGHT SENSOR TEST (Simplified) ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        # In a real system, the foundation would manage the I2C bus.
        # For this test, we create it here as the architecture specifies.
        i2c_bus = busio.I2C(board.GP5, board.GP4)
        print("✓ Shared I2C bus created.")
        
        if foundation.initialize_network():
            # --- Module Loading ---
            
            # Load the simplified BH1750 module
            from module_bh1750 import BH1750Module
            bh1750 = BH1750Module(foundation, i2c_bus)
            foundation.register_module("bh1750", bh1750)
            
            # Load other modules (e.g., LED control)
            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # --- Web Server Setup ---
            foundation.start_server()
            print(f"✓ Dashboard ready at: http://{foundation.server_ip}")
            
            # Main loop
            while True:
                foundation.poll()  # This now handles server polling and module updates
                time.sleep(0.1)
                
    except Exception as e:
        print(f"✗ A critical error occurred: {e}")
        import sys
        sys.print_exception(e)
        print("Rebooting in 15 seconds...")
        time.sleep(15)
        supervisor.reload()

# Standard entry point
if __name__ == "__main__":
    main()