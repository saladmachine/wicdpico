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
        print("✓ Shared I2C bus acquired from foundation.")
        if foundation.initialize_network():
            from module_scd41 import SCD41Module
            scd41 = SCD41Module(foundation)
            foundation.register_module("scd41", scd41)

            from adafruit_httpserver import Response
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                cache_headers = {
                    "Cache-Control": "no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
                dashboard_html = foundation.render_dashboard("WicdPico SCD41 Test")
                return Response(request, dashboard_html, content_type="text/html", headers=cache_headers)
            foundation.start_server()
            print("✓ Dashboard ready at: http://{}".format(foundation.server_ip))
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