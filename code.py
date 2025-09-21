# code.py - New Module Order (SCD41 First)
import supervisor
import gc
from foundation_core import WicdpicoFoundation
from module_led_control import LEDControlModule
from module_bh1750 import BH1750Module
from module_scd41 import SCD41Module

supervisor.runtime.autoreload = False
print("--- System Integration Test ---")
print(f"Initial free memory: {gc.mem_free()} bytes")

try:
    # 1. Initialize Foundation (which creates the I2C bus)
    foundation = WicdpicoFoundation()
    print(f"Memory after foundation: {gc.mem_free()} bytes")

    # Exit if I2C bus failed to initialize
    if not foundation.i2c:
        raise RuntimeError("Could not initialize I2C bus. Halting.")

    # 2. Initialize the network to create the server object FIRST
    print("Initializing network and server...")
    network_ok = foundation.initialize_network()
    if not network_ok:
        raise RuntimeError("Failed to initialize network. Halting.")
    print("Network initialized.")

    # 3. NOW, initialize and register the modules in the desired order
    print("Loading modules...")

    # 1. SCD41 Module (will appear first on dashboard)
    scd41_module = SCD41Module(foundation, foundation.i2c)
    foundation.register_module("scd41", scd41_module)
    print(f"Memory after SCD41 module: {gc.mem_free()} bytes")

    # 2. BH1750 Module (will appear second)
    bh1750_module = BH1750Module(foundation, foundation.i2c)
    foundation.register_module("bh1750", bh1750_module)
    print(f"Memory after BH1750 module: {gc.mem_free()} bytes")
    
    # 3. LED Module (will appear last)
    led_module = LEDControlModule(foundation)
    foundation.register_module("led", led_module)
    print(f"Memory after LED module: {gc.mem_free()} bytes")


    print("\n✓ SUCCESS: All modules loaded without crashing.")

    # 4. Start the server and run the main application loop
    foundation.start_server()
    foundation.run_main_loop()

except Exception as e:
    print("\n✗ FAILED: A critical error occurred.")
    import sys
    sys.print_exception(e)

print("--- Test Complete ---")