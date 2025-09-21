# code_scd41.py (Refactored Test Harness)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import supervisor

supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO SCD41 TEST (Refactored) ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        # 1. Get the shared I2C bus from the foundation
        i2c_bus = foundation.get_i2c_bus()
        print("✓ Shared I2C bus acquired from foundation.")
        
        if foundation.initialize_network():
            # 2. Load modules, passing the shared bus to those that need it
            from module_scd41 import SCD41Module
            scd41 = SCD41Module(foundation, i2c_bus)
            foundation.register_module("scd41", scd41)

            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)

            # 3. Set up the standard dashboard route with cache control
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                # Define headers to prevent browser caching
                cache_headers = {
                    "Cache-Control": "no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
                # Render the standard dashboard page
                dashboard_html = foundation.render_dashboard("WicdPico SCD41 Test")
                return Response(request, dashboard_html, content_type="text/html", headers=cache_headers)
            
            foundation.start_server()
            print(f"✓ Dashboard ready at: http://{foundation.server_ip}")
            
            # 4. Use the standard foundation.poll() main loop
            while True:
                foundation.poll()
                time.sleep(0.1)
                
    except Exception as e:
        print(f"✗ A critical error occurred: {e}")
        import sys
        sys.print_exception(e)
        print("Rebooting in 15 seconds...")
        time.sleep(15)
        supervisor.reload()

if __name__ == "__main__":
    main()