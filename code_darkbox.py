# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
Main entry point for WicdPico DarkBox dashboard.
Serves dashboard and calibration pages for DarkBoxModule.
"""

import gc
import time
import wifi
import supervisor
supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO DARKBOX TEST ===")
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()

        if foundation.initialize_network():
            from module_darkbox import DarkBoxModule
            darkbox = DarkBoxModule(foundation)
            foundation.register_module("darkbox", darkbox)

            from adafruit_httpserver import Response

            # Minimal CSS for cards and buttons
            css = """
            <style>
                .module {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 1em;
                    margin-bottom: 1em;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    background: #fff;
                }
                .control-group {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1em;
                    margin-top: 1em;
                }
                button {
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0.75em 2em;
                    cursor: pointer;
                    font-size: 1em;
                    margin: 0.5em 0;
                }
                button:active, button:focus {
                    outline: none;
                }
            </style>
            """

            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    import time
                    t = time.localtime()
                    timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                        t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec
                    )
                    dashboard_html = f"""
                    <html>
                    <head>
                        <title>WicdPico DarkBox Dashboard</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        {css}
                    </head>
                    <body>
                        <div style="text-align:right; font-size:0.9em; color:#888;">
                            Page generated at: {timestamp}
                        </div>
                        {darkbox.get_dashboard_html()}
                        <!-- SD Card Section -->
                        <div class="module" style="margin-top:2em;">
                            <h2>SD Card</h2>
                            <div class="control-group">
                                <button disabled>SD Files</button>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print(f"Dashboard error: {e}")
                    return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")

            @foundation.server.route("/calibration", methods=['GET'])
            def serve_calibration(request):
                try:
                    calibration_html = darkbox.get_calibration_html()
                    calibration_page = f"""
                    <html>
                    <head>
                        <title>CO2 Calibration</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        {css}
                    </head>
                    <body>
                        {calibration_html}
                    </body>
                    </html>
                    """
                    return Response(request, calibration_page, content_type="text/html")
                except Exception as e:
                    print(f"Calibration page error: {e}")
                    return Response(request, f"<h1>Calibration Page Error</h1><p>{e}</p>", content_type="text/html")

            # Register all module routes
            darkbox.register_routes(foundation.server)

            foundation.start_server()
            print("✓ DarkBox dashboard ready. Access via browser.")

            while True:
                foundation.server.poll()
                darkbox.update()
                time.sleep(0.1)
                gc.collect()
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()