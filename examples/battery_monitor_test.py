"""
Battery Monitor Module - minimal test version
SAVE THIS FILE AS: battery_monitor.py
"""

import board
import analogio
import digitalio
import time
import json
from adafruit_httpserver import Request, Response

try:
    from module_base import ModuleBase
    BaseClass = ModuleBase
except ImportError:
    BaseClass = object

class BatteryMonitorModule(BaseClass):
    def __init__(self, foundation):
        if BaseClass != object:
            super().__init__(foundation, "Battery Monitor")
        else:
            self.foundation = foundation
            self.name = "Battery Monitor"

        # Initialize ADC and LED
        self.adc = analogio.AnalogIn(board.A0)  # GPIO26
        self.led = digitalio.DigitalInOut(board.LED)
        self.led.direction = digitalio.Direction.OUTPUT
        self.led.value = False

        # Load test state
        self.load_test_active = False
        self.last_blink = 0

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
                "load_test": self.load_test_active
            }

            return Response(request, json.dumps(data), content_type="application/json")

        @self.foundation.server.route("/api/battery/load", methods=['POST'])
        def toggle_load_test(request: Request):
            self.load_test_active = not self.load_test_active
            if not self.load_test_active:
                self.led.value = False

            return Response(request, json.dumps({"active": self.load_test_active}), content_type="application/json")

    def update(self):
        if self.load_test_active:
            current_time = time.monotonic()
            if current_time - self.last_blink > 0.1:  # 10Hz blink
                self.led.value = not self.led.value
                self.last_blink = current_time

    def get_dashboard_html(self):
        return '''
        <div class="module-section">
            <h3>Battery Monitor</h3>
            <div id="batteryData">Loading...</div>
            <button onclick="toggleLoad()">Toggle Load Test</button>
        </div>
        <script>
        function updateBattery() {
            fetch('/api/battery')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('batteryData').innerHTML =
                        `Battery: ${data.battery_voltage}V<br>` +
                        `ADC: ${data.adc_voltage}V<br>` +
                        `Raw: ${data.raw}<br>` +
                        `Load Test: ${data.load_test ? 'ON' : 'OFF'}`;
                });
        }

        function toggleLoad() {
            fetch('/api/battery/load', {method: 'POST'});
        }

        setInterval(updateBattery, 1000);
        updateBattery();
        </script>
        '''