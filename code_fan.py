"""
Main entry point for the WicdPico CPU Fan Controller application.
"""

import time
import gc
from foundation_core import WicdpicoFoundation
from module_cpu_fan import CpuFanModule
from adafruit_httpserver import Response

def main():
    print("=== WicdPico CPU Fan Controller ===")
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        # --- Module Setup ---
        print("Loading CPU Fan module...")
        cpu_fan_module = CpuFanModule(foundation)
        foundation.register_module("cpu_fan", cpu_fan_module)
        cpu_fan_module.register_routes(foundation.server)
        print("✓ CPU Fan module loaded and routes registered.")

        # --- Main Dashboard Route ---
        @foundation.server.route("/", methods=['GET'])
        def serve_dashboard(request):
            """Renders the main dashboard from all registered modules."""
            try:
                html = foundation.render_dashboard("WicdPico Dashboard")
                return Response(request, html, content_type="text/html")
            except Exception as e:
                print("Dashboard rendering error: {}".format(e))
                error_html = "<h1>Dashboard Error</h1><p>{}</p>".format(e)
                return Response(request, error_html, content_type="text/html")

        # --- Start Server & Main Loop ---
        foundation.start_server()
        print("✓ Server started. Dashboard is active.")
        print("--- Entering main application loop ---")
        
        while True:
            # Poll the web server to handle incoming browser requests
            foundation.server.poll()
            
            # Call the update() method for all registered modules
            for module in foundation.modules.values():
                module.update()
            
            # A small delay to prevent the loop from running too fast
            time.sleep(0.1)
            gc.collect()

    else:
        print("✗ Network initialization failed. Check your settings.toml file.")

if __name__ == "__main__":
    main()