# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
Test template for CPU Fan module using modular WicdPico workflow.
Provides standalone testing and development environment for fan control.
"""

import time
import gc

def main():
    print("=== WICDPICO CPU FAN TEST SYSTEM ===")
    from foundation_core import WicdpicoFoundation
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        from module_cpu_fan import CPUFanModule
        cpu_fan = CPUFanModule(foundation)
        foundation.register_module("cpu_fan", cpu_fan)

        # Register module routes
        cpu_fan.register_routes(foundation.server)

        # Serve dashboard route
        from adafruit_httpserver import Response
        @foundation.server.route("/", methods=['GET'])
        def serve_dashboard(request):
            try:
                dashboard_html = foundation.render_dashboard("CPU Fan Test Dashboard")
                return Response(request, dashboard_html, content_type="text/html")
            except Exception as e:
                print(f"Dashboard error: {e}")
                return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")

        foundation.start_server()
        print("✓ CPU Fan test dashboard ready. Access via browser at http://192.168.4.1")
        print("✓ Fan control available at dashboard")
        
        # Test fan initialization
        if cpu_fan.fan_available:
            print("✓ Fan hardware initialized successfully")
            print(f"✓ Initial fan speed: {cpu_fan.get_fan_speed()}%")
        else:
            print("⚠ Fan hardware not available - web interface will show unavailable status")

        # Main loop: poll the server and allow time for requests
        while True:
            foundation.server.poll()
            for module in foundation.modules.values():
                module.update()
            time.sleep(0.1)
            gc.collect()

if __name__ == "__main__":
    main()