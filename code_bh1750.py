# code_bh1750.py - Test harness for the simplified BH1750 module (Foundation-based I2C)
import gc
import time
import supervisor

supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO BH1750 LIGHT SENSOR TEST (Foundation Pattern) ===")
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        print("✓ Shared I2C bus acquired from foundation.")

        if foundation.initialize_network():
            # Load the BH1750 module, letting it get I2C from foundation
            from module_bh1750 import BH1750Module
            bh1750 = BH1750Module(foundation)
            foundation.register_module("bh1750", bh1750)

            # --- Web Server Setup ---
            foundation.start_server()
            print("✓ Dashboard ready at: http://{}".format(foundation.server_ip))
            # Main loop
            while True:
                foundation.poll()
                time.sleep(0.1)
    except Exception as e:
        print("✗ A critical error occurred: {}".format(e))
        import sys
        sys.print_exception(e)
        print("Rebooting in 15 seconds...")
        time.sleep(15)
        supervisor.reload()

if __name__ == "__main__":
    main()