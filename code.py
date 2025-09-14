# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
Main entry point for Darkbox system using modular WicdPico workflow.
Registers both Darkbox and Monitor modules for dashboard and CSV export.
"""

import time
import gc

def main():
    print("=== WICDPICO DARKBOX SYSTEM ===")
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
                dashboard_html = foundation.render_dashboard("WicdPico Darkbox Dashboard")
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

        def download_csv_file(self, request):
            # Get filename from query string, default to JoeText.csv if not provided
            try:
                query = request.query_params
                filename = query.get("file", "JoeText.csv")
                if not filename.endswith(".csv"):
                    return Response(request, "Invalid file type.", content_type="text/plain")
                # Only look in root directory
                try:
                    with open("/" + filename, "r") as f:
                        csv_data = f.read()
                    headers = {
                        "Content-Disposition": f'attachment; filename="{filename}"'
                    }
                    return Response(request, csv_data, content_type="text/csv", headers=headers)
                except OSError:
                    return Response(request, f"Error: {filename} not found.", content_type="text/plain")
            except Exception as e:
                return Response(request, f"Error downloading CSV file: {e}", content_type="text/plain")

if __name__ == "__main__":
    main()