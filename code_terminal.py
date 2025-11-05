# code_terminal.py - Test harness for the Web Terminal Module
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import supervisor
import sys # Import sys here to ensure it's available for print_exception

# Per project convention, disable autoreload for stability in test harnesses
supervisor.runtime.autoreload = False

def main():
    """
    Initializes the WicdPico foundation, registers the TerminalModule,
    and starts the web server for isolated module testing.
    """
    try:
        print("=== WICDPICO WEB TERMINAL TEST (Foundation Pattern) ===")
        
        # 1. Initialize the core application foundation
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        print("✓ Foundation core instantiated.")

        # 2. Initialize WiFi and network services
        if foundation.initialize_network():
            
            # 3. Import and instantiate the custom module (module_terminal.py)
            from module_terminal import TerminalModule
            terminal = TerminalModule(foundation)

            # 4. Register the module with the foundation. 
            foundation.register_module("terminal", terminal)

            # 5. Start the web server
            foundation.start_server()
            
            print("✓ Dashboard ready at: http://{}".format(foundation.server_ip))
            print("   Connect to WiFi SSID: {} (Password: {})".format(foundation.config.WIFI_SSID, foundation.config.WIFI_PASSWORD))

            # 6. Main application loop
            while True:
                foundation.poll()  # Handle incoming web requests and call module.update()
                time.sleep(0.1) # Yield a small time slice
                
    except Exception as e:
        # Graceful error handling
        print("✗ A critical error occurred: {}".format(e))
        sys.print_exception(e)
        print("Rebooting in 15 seconds...")
        time.sleep(15)
        # supervisor.reload()

if __name__ == "__main__":
    main()