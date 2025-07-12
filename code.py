# Auto-save test - July 12
"""
Test application to verify LED Control module with foundation
"""
# Existing imports
from foundation_core import PicowicdFoundation # Changed name
from led_control import LEDControlModule
from file_manager import FileManagerModule
from console_monitor_simple import ConsoleMonitorModule
from adafruit_httpserver import Request, Response
from rtc_control_module import RTCControlModule

# NEW: Import the BatteryMonitorModule
from battery_monitor import BatteryMonitorModule # Add this line

print("=== **** VSCode CircuitPython Test **** ===")

import supervisor
supervisor.runtime.autoreload = False
print(f"Autoreload disabled: {supervisor.runtime.autoreload}")

def main():
    # Initialize foundation
    # Changed instantiation to the new class name
    foundation = PicowicdFoundation() # Change this line
    foundation.startup_print("Starting Picowicd Application...") # Generic message

    # Initialize network
    if not foundation.initialize_network():
        foundation.startup_print("Network initialization failed!")
        return

    rtc_module = RTCControlModule(foundation)
    foundation.register_module("rtc_control", rtc_module)


    # Create and register LED module
    led_module = LEDControlModule(foundation)
    foundation.register_module("led_control", led_module)

    # Create and register File Manager module
    file_manager_module = FileManagerModule(foundation)
    foundation.register_module("file_manager", file_manager_module)

    # Create and register Console Monitor module
    console_module = ConsoleMonitorModule(foundation)
    foundation.register_module("console", console_module)

    # NEW: Create and register Battery Monitor module
    battery_module = BatteryMonitorModule(foundation) # Add this line
    foundation.register_module("battery_monitor", battery_module) # Add this line

    @foundation.server.route("/", methods=['GET'])
    def handle_root(request: Request):
        return Response(
            request,
            foundation.render_dashboard("Picowicd Dashboard"), # Changed title
            content_type="text/html"
        )

    # Start server and run
    foundation.start_server()
    foundation.startup_print("Picowicd Application ready!") # Generic message
    foundation.run_main_loop()

if __name__ == "__main__":
    main()