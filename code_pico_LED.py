# code_pico_led.py (Corrected Test Harness v3)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import supervisor
import gc

supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO Pico LED TEST ===")
        from foundation_core import WicdpicoFoundation
        
        foundation = WicdpicoFoundation()
        print("✓ Foundation initialized.")

        if foundation.initialize_network():
            from module_led_control import LEDControlModule

            # Keep a reference to the module instance
            led_module = LEDControlModule(foundation)
            foundation.register_module("led", led_module)

            from adafruit_httpserver import Response
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                cache_headers = {
                    "Cache-Control": "no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
                dashboard_html = foundation.render_dashboard("WicdPico LED Test")
                return Response(request, dashboard_html, content_type="text/html", headers=cache_headers)

            foundation.start_server()

            # Main application loop
            while True:
                # 1. Poll the web server for requests
                foundation.server.poll()
                
                # 2. ADDED: Call the update method for the module
                led_module.update()
                
                # 3. Short pause and memory cleanup
                time.sleep(0.1)
                gc.collect()


    except Exception as e:
        print("✗ A critical error occurred: {}".format(e))
        import sys
        sys.print_exception(e)
        print("Rebooting in 15 seconds...")
        time.sleep(15)
        supervisor.reload()

if __name__ == "__main__":
    main()