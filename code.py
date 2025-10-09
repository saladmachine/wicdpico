# code_monitor.py (Test Harness)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import supervisor
import sys

# Per project convention, disable autoreload for stability in test harnesses
supervisor.runtime.autoreload = False

def main():
    """
    Initializes the WicdPico foundation, registers the Monitor module,
    and starts the web server to test the module's functionality in isolation.
    """
    try:
        print("=== WICDPICO MONITOR TEST ===")
        
        # 1. Initialize the core application foundation
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        print("✓ Foundation core instantiated.")

        # 2. Initialize WiFi and network services
        if foundation.initialize_network():
            
            # 3. Import and instantiate the module to be tested
            from module_monitor import MonitorModule
            monitor = MonitorModule(foundation)

            # 4. Register the module. This automatically calls the module's
            #    register_routes() method, setting up all necessary web endpoints.
            foundation.register_module("monitor", monitor)

            # 5. Start the web server
            foundation.start_server()
            
            # The MonitorModule serves its own full page, so we point to its specific path.
            print("✓ Monitor ready at: http://{}/monitor".format(foundation.server_ip))

            # 6. Main application loop to keep the server responsive
            while True:
                foundation.poll()  # Handle incoming web requests
                time.sleep(0.1)
                
    except Exception as e:
        # Graceful error handling: print the exception and reboot the device
        print("✗ A critical error occurred: {}".format(e))
        sys.print_exception(e)
        print("Rebooting in 15 seconds...")
        time.sleep(15)
        supervisor.reload()

if __name__ == "__main__":
    main()