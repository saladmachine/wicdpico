# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
Main entry point for MonitorModule, following standard WicdPico process.
"""

import time
import gc

def main():
    print("=== WICDPICO MONITOR TEST ===")
    from foundation_core import WicdpicoFoundation
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        from module_monitor import MonitorModule
        monitor = MonitorModule(foundation)
        foundation.register_module("monitor", monitor)

        # Register module routes with the server
        monitor.register_routes(foundation.server)

        # Serve dashboard route using foundation.render_dashboard and error handling
        from adafruit_httpserver import Response
        @foundation.server.route("/", methods=['GET'])
        def serve_dashboard(request):
            try:
                dashboard_html = foundation.render_dashboard("WicdPico Monitor Dashboard")
                return Response(request, dashboard_html, content_type="text/html")
            except Exception as e:
                print(f"Dashboard error: {e}")
                return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")

        foundation.start_server()
        print("✓ Monitor dashboard ready. Access via browser.")

        # Optionally, simulate some console output for initial testing
        for i in range(5):
            monitor.console_print(f"Test message {i+1}")
            time.sleep(0.1)

        # Main loop: poll the server and allow time for requests
        while True:
            foundation.server.poll()
            time.sleep(0.1)  # Allow server to process requests
            gc.collect()

if __name__ == "__main__":
    main()