# module_bh1750.py (With Added Debugging)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import adafruit_bh1750
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

SENSOR_READ_INTERVAL = 2.0
ENABLE_AUTO_UPDATES = True

class BH1750Module(WicdpicoModule):
    def __init__(self, foundation, i2c_bus):
        super().__init__(foundation)
        self.name = "BH1750 Light Sensor"
        self.foundation = foundation
        self.i2c = i2c_bus
        self.read_interval = SENSOR_READ_INTERVAL
        self.auto_updates_enabled = ENABLE_AUTO_UPDATES
        self.sensor_available = False
        self.bh1750 = None
        self.last_reading_time = 0
        self.last_light_level = None
        self.status_message = "Initializing..."
        self.last_error = None
        self._initialize_sensor()
        self.foundation.startup_print(f"BH1750 module created. Status: {self.status_message}")

    def _initialize_sensor(self):
        if not self.i2c:
            self.status_message = "Error: I2C Not Available"
            self.last_error = "Foundation failed to provide I2C bus."
            self.sensor_available = False
            return
        try:
            self.bh1750 = adafruit_bh1750.BH1750(self.i2c)
            self.last_light_level = round(self.bh1750.lux, 1)
            self.last_reading_time = time.monotonic()
            self.sensor_available = True
            self.status_message = "Ready"
        except Exception as e:
            self.sensor_available = False
            self.last_error = f"BH1750 not found: {e}"
            self.status_message = "Error: Not Found"

    def get_sensor_reading(self):
        if not self.sensor_available:
            return None
        
        try:
            light_lux = self.bh1750.lux
            self.last_light_level = round(light_lux, 1)
            self.last_reading_time = time.monotonic()
            self.last_error = None
            return self.last_light_level
        except Exception as e:
            self.last_error = f"Reading failed: {e}"
            self.foundation.startup_print(f"BH1750 error: {self.last_error}")
            return None

    def update(self):
        if self.auto_updates_enabled and self.sensor_available:
            if time.monotonic() - self.last_reading_time >= self.read_interval:
                self.get_sensor_reading()

    def register_routes(self, server):
        @server.route("/bh1750/read", methods=['POST'])
        def read_route(request: Request):
            # --- DEBUGGING LINES ADDED ---
            self.foundation.startup_print("BH1750: Received /read POST request.")
            reading = self.get_sensor_reading()
            if reading is not None:
                self.foundation.startup_print(f"BH1750: Sending reading: {reading}")
                return Response(request, f"{reading} lux")
            else:
                self.foundation.startup_print(f"BH1750: Failed to get reading. Error: {self.last_error}")
                return Response(request, f"Failed: {self.last_error}")
        self.foundation.startup_print("BH1750 route '/bh1750/read' registered.")

    def get_dashboard_html(self):
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        error_html = f'<br><span class="error-text"><strong>Error:</strong> {self.last_error}</span>' if self.last_error else ""

        if self.last_light_level is not None:
            age = time.monotonic() - self.last_reading_time
            last_reading_text = f'<strong>{self.last_light_level} lux</strong> ({int(age)}s ago)'
        else:
            last_reading_text = "No readings yet"

        return f'''
        <div class="module">
            <h3>{self.name}</h3>
            <div class="status" style="border-left-color: {status_color};">
                <strong>Status:</strong> <span style="color: {status_color};">{self.status_message}</span><br>
                <strong>Last Reading:</strong> <span id="bh1750-last-reading">{last_reading_text}</span>
                {error_html}
            </div>
            <button id="bh1750-read-btn" onclick="getBH1750Reading()">Get Fresh Reading</button>
        </div>
        <script>
        function getBH1750Reading() {{
            const statusSpan = document.getElementById('bh1750-last-reading');
            const button = document.getElementById('bh1750-read-btn');
            statusSpan.textContent = 'Reading...';
            button.disabled = true;

            fetch('/bh1750/read', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    statusSpan.innerHTML = '<strong>' + result + '</strong> (just now)';
                }})
                .catch(error => {{
                    statusSpan.textContent = 'Error: ' + error.message;
                }})
                .finally(() => {{
                    button.disabled = false;
                }});
        }}
        </script>
        '''