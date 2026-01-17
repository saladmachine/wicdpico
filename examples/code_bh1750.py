# code_bh1750.py (Corrected Test Harness with Dependencies)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

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
            # --- Load Required Dependencies ---
            # These modules are necessary for I2C stability, logging, and time services.
            from module_rtc import RTCModule
            from module_SD_manager import SDManagerModule
            from module_bh1750 import BH1750Module 
            
            # 1. Register essential system modules first (RTC and SD Manager)
            # This restores the necessary import chain and I2C environment stability.
            rtc = RTCModule(foundation)
            foundation.register_module("rtc", rtc)
            
            sd_manager = SDManagerModule(foundation)
            foundation.register_module("sd_manager", sd_manager)

            # 2. Register the module under test
            bh1750 = BH1750Module(foundation)
            foundation.register_module("bh1750", bh1750)
            
            from adafruit_httpserver import Response
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                cache_headers = {
                    "Cache-Control": "no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
                dashboard_html = foundation.render_dashboard("WicdPico BH1750 Test")
                return Response(request, dashboard_html, content_type="text/html", headers=cache_headers)
            
            foundation.start_server()
            print("✓ Dashboard ready at: http://{}".format(foundation.server_ip))
            
            # Main poll loop
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