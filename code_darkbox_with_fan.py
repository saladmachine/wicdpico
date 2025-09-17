# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
Main entry point for Darkbox system with CPU Fan support using modular WicdPico workflow.
Registers Darkbox, Monitor, and CPU Fan modules for comprehensive dashboard.
"""

import time
import gc

def main():
    print("=== WICDPICO DARKBOX + CPU FAN SYSTEM ===")
    from foundation_core import WicdpicoFoundation
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        # Load primary modules
        from module_darkbox import DarkBoxModule
        darkbox = DarkBoxModule(foundation)
        foundation.register_module("darkbox", darkbox)

        from module_monitor import MonitorModule
        monitor = MonitorModule(foundation)
        foundation.register_module("monitor", monitor)

        # Load CPU Fan module (optional - graceful failure if hardware unavailable)
        try:
            from module_cpu_fan import CPUFanModule
            cpu_fan = CPUFanModule(foundation)
            foundation.register_module("cpu_fan", cpu_fan)
            print("✓ CPU Fan module loaded")
        except Exception as e:
            print(f"⚠ CPU Fan module unavailable: {e}")

        # Register all module routes
        for module in foundation.modules.values():
            module.register_routes(foundation.server)

        # Serve dashboard route
        from adafruit_httpserver import Response
        @foundation.server.route("/", methods=['GET'])
        def serve_dashboard(request):
            global last_activity_time
            last_activity_time = time.monotonic()
            try:
                dashboard_html = foundation.render_dashboard("Darkbox + CPU Fan Dashboard 1.03")
                return Response(request, dashboard_html, content_type="text/html")
            except Exception as e:
                print(f"Dashboard error: {e}")
                return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")

        foundation.start_server()
        print("✓ Enhanced dashboard ready. Access via browser.")
        print(f"✓ {len(foundation.modules)} modules loaded")

        # Main loop: poll the server and allow time for requests
        while True:
            foundation.server.poll()
            for module in foundation.modules.values():
                module.update()
            time.sleep(0.1)
            gc.collect()

if __name__ == "__main__":
    main()