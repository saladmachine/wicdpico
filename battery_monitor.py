"""
Battery Monitor Module - minimal test version
SAVE THIS FILE AS: battery_monitor.py
"""

import board
import analogio
import time
import json
from adafruit_httpserver import Request, Response

try:
    from module_base import PicowicdModule # Assuming PicowidModule is the correct base class name
    BaseClass = PicowicdModule
except ImportError:
    BaseClass = object

class BatteryMonitorModule(BaseClass):
    def __init__(self, foundation):
        if BaseClass != object:
            super().__init__(foundation)
            self.name = "Battery Monitor"
        else:
            self.foundation = foundation
            self.name = "Battery Monitor"

        # Initialize ADC
        self.adc = analogio.AnalogIn(board.A0)  # GPIO26

        # Load test state - this will now indicate if the load test *page* is active, not an active process
        self.load_test_active = False # Retained for potential future use or to indicate page view

        self._register_routes()

    def _register_routes(self):
        @self.foundation.server.route("/api/battery", methods=['GET'])
        def get_battery_status(request: Request):
            raw = self.adc.value
            adc_voltage = (raw * 3.3) / 65536
            battery_voltage = adc_voltage * 2.0

            data = {
                "raw": raw,
                "adc_voltage": round(adc_voltage, 3),
                "battery_voltage": round(battery_voltage, 3),
                "load_test": self.load_test_active # Still reporting this flag if desired, but not displayed on page
            }

            return Response(request, json.dumps(data), content_type="application/json")

        @self.foundation.server.route("/battery-load-test-page", methods=['GET'])
        def show_load_test_page(request: Request):
            """Serve the second page with load test data and a return button."""
            self.load_test_active = True # Indicate load test data is being viewed
            html_content = '''
            <div class="module-section">
                <h3>Battery Monitor Details</h3>
                <div id="loadTestData">Loading...</div>
                <button onclick="window.location.href='/'">Return to Dashboard</button>
            </div>
            <script>
            function updateLoadTest() {
                fetch('/api/battery')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('loadTestData').innerHTML =
                            `Battery: ${data.battery_voltage}V<br>` +
                            `ADC: ${data.adc_voltage}V<br>` +
                            `Raw: ${data.raw}`;
                    });
            }

            // Update immediately and then every second
            updateLoadTest();
            setInterval(updateLoadTest, 1000);
            </script>
            '''
            return Response(request, self.foundation.templates.render_page("Battery Monitor Details", html_content, ""), content_type="text/html")


    def update(self):
        # The 'update' method remains, but does nothing specific for battery monitor.
        pass

    def get_dashboard_html(self):
        """Return HTML for the initial Battery Monitor interface with only a single button."""
        self.load_test_active = False # Indicate not viewing detailed load test data
        return '''
        <div class="module-section">
            <h3>Battery Monitor</h3>
            <button onclick="window.location.href='/battery-load-test-page'">Battery Monitor</button>
        </div>
        ''' # REMOVED: batteryDataSummary div and associated JavaScript
