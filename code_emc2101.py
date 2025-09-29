"""
WicdPico EMC2101 Fan Controller Test Harness
Follows repo pattern: uses foundation's shared I2C bus.
"""

import time
import gc
from foundation_core import WicdpicoFoundation
from module_emc2101 import Emc2101Module
from adafruit_httpserver import Response

def main():
    print("=== WicdPico EMC2101 Fan Controller ===")
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        # --- Module Setup ---
        print("Loading EMC2101 Fan module...")
        emc2101_module = Emc2101Module(foundation)
        foundation.register_module("emc2101", emc2101_module)
        emc2101_module.register_routes(foundation.server)
        print("✓ EMC2101 module loaded and routes registered.")

        # --- Main Dashboard Route ---
        @foundation.server.route("/", methods=['GET'])
        def serve_dashboard(request):
            try:
                html = foundation.render_dashboard("WicdPico EMC2101 Fan Dashboard")
                return Response(request, html, content_type="text/html")
            except Exception as e:
                print("Dashboard rendering error: {}".format(e))
                error_html = "<h1>Dashboard Error</h1><p>{}</p>".format(e)
                return Response(request, error_html, content_type="text/html")

        foundation.start_server()
        print("✓ Server started. Dashboard is active.")
        print("--- Entering main application loop ---")
        
        while True:
            foundation.server.poll()
            for module in foundation.modules.values():
                module.update()
            time.sleep(0.1)
            gc.collect()

    else:
        print("✗ Network initialization failed. Check your settings.toml file.")

if __name__ == "__main__":
    main()