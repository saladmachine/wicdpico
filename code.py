# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
Main entry point for Darkbox system using modular WicdPico workflow.
Registers both Darkbox and Monitor modules for dashboard and CSV export.
"""

import time
import gc

def main():
    print("=== WICDPICO DARKBOX SYSTEM === 1.3")
    from foundation_core import WicdpicoFoundation
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        from module_darkbox import DarkBoxModule
        darkbox = DarkBoxModule(foundation)
        foundation.register_module("darkbox", darkbox)

        from module_monitor import MonitorModule
        monitor = MonitorModule(foundation)
        foundation.register_module("monitor", monitor)

        # Register module routes
        darkbox.register_routes(foundation.server)
        monitor.register_routes(foundation.server)

        # Serve dashboard route
        from adafruit_httpserver import Response
        @foundation.server.route("/", methods=['GET'])
        def serve_dashboard(request):
            try:
                dashboard_html = foundation.render_dashboard("WicdPico Darkbox Dashboard 1.2")
                return Response(request, dashboard_html, content_type="text/html")
            except Exception as e:
                print(f"Dashboard error: {e}")
                return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")

        foundation.start_server()
        print("✓ Darkbox dashboard ready. Access via browser.")

        # Main loop: poll the server and allow time for requests
        while True:
            foundation.server.poll()
            for module in foundation.modules.values():
                module.update()
            time.sleep(0.1)
            gc.collect()

if __name__ == "__main__":
    main()