# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT
#
# code_cpu_fan.py
"""
WicdPico CPU Fan Controller Application Entrypoint

Minimal entrypoint for the CPU Fan module, following WicdPico conventions.
Sets up the foundation, registers the module, and starts the HTTP server and polling loop.
"""

import time
from foundation_core import WicdpicoFoundation
from module_cpu_fan import CpuFanModule

def main():
    """
    Main entrypoint for the WicdPico CPU Fan Controller application.
    Initializes the foundation, registers the CPU fan module, and starts the server.
    """
    print("=== WicdPico CPU Fan Controller ===")
    print("Initializing foundation...")
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():  # <-- Add this check
        print("Loading CPU Fan module...")
        cpu_fan_module = CpuFanModule(foundation)
        foundation.register_module("cpu_fan", cpu_fan_module)

        print("Starting HTTP server...")
        foundation.start_server()  # <-- Start the server first!

        print("foundation.server =", foundation.server)
        assert foundation.server is not None, "foundation.server is None! Cannot register routes."
        print("Registering module routes...")
        cpu_fan_module.register_routes(foundation.server)

        @foundation.server.route("/", methods=['GET'])
        def serve_dashboard(request):
            """
            Serve the main dashboard page.
            """
            html = foundation.render_dashboard()
            return foundation.html_response(request, html)

        print("Entering main polling loop. Press Ctrl+C to exit.")
        try:
            while True:
                for module in foundation.modules.values():
                    module.update()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Shutting down.")
    else:
        print("Network initialization failed.")

if __name__ == "__main__":
    main()