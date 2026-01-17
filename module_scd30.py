# module_scd30.py
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import adafruit_scd30
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class SCD30Module(WicdpicoModule):
    def __init__(self, i2c_bus):
        super().__init__()
        self.name = "SCD30 CO2 Sensor"
        self.i2c = i2c_bus
        self.sensor = None
        self.sensor_available = False
        self.last_reading = {"co2": 0, "temp": 0, "humidity": 0}
        
        self.status_message = "Initializing..."
        self._initialize_sensor()

    def _initialize_sensor(self):
        if self.i2c is None:
            self.status_message = "Error: No I2C Bus"
            print("✗ SCD30: No I2C bus available")
            return
            
        try:
            self.sensor = adafruit_scd30.SCD30(self.i2c)
            self.sensor_available = True
            self.status_message = "Ready"
            print("✓ SCD30 sensor initialized")
        except Exception as e:
            self.status_message = "Error: Init Failed"
            print("✗ SCD30 init failed: {}".format(e))
            self.sensor_available = False

    def get_reading(self):
        if not self.sensor_available:
            return None
            
        # SCD30 updates every ~2 seconds. We just read the current buffer.
        if self.sensor.data_available:
            try:
                self.last_reading = {
                    "co2": int(self.sensor.CO2),
                    "temp": round(self.sensor.temperature, 1),
                    "humidity": round(self.sensor.relative_humidity, 1)
                }
                return self.last_reading
            except Exception as e:
                print("SCD30 read error: {}".format(e))
        
        return self.last_reading

    def register_routes(self, server):
        @server.route("/scd30/data", methods=['GET'])
        def api_data(request: Request):
            data = self.get_reading()
            if data:
                # Optimized string formatting (No json import)
                json_str = '{{"co2": {}, "temp": {}, "humidity": {}}}'.format(
                    data["co2"], data["temp"], data["humidity"]
                )
                return Response(request, json_str, content_type="application/json")
            return Response(request, '{"error": "Sensor unavailable"}', content_type="application/json")

    def get_dashboard_html(self):
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        
        # Use spans with IDs so we can update them via JS
        cur = self.last_reading
        
        return """
        <div class="module">
            <h3>SCD30 Sensor</h3>
            <div style="border-left: 6px solid {status_color}; padding-left: 12px; margin-bottom: 15px;">
                <strong>Status:</strong> {status}
            </div>
            <p style="font-size: 1.2em;">
                <strong><span id="scd30-co2">{co2}</span> ppm</strong><br>
                <span id="scd30-temp">{temp}</span> °C, <span id="scd30-hum">{hum}</span>% RH
            </p>
            <button onclick="fetchSCD30()">Update Reading</button>
            <p id="scd30-debug" style="font-size: 0.8em; color: #666; min-height: 1.2em;"></p>
            
            <script>
            function fetchSCD30() {{
                const debug = document.getElementById('scd30-debug');
                debug.innerText = "Fetching...";
                fetch('/scd30/data')
                    .then(r => r.json())
                    .then(d => {{
                        if(d.error) {{
                            debug.innerText = "Error: " + d.error;
                        }} else {{
                            // Update DOM elements directly
                            document.getElementById('scd30-co2').innerText = d.co2;
                            document.getElementById('scd30-temp').innerText = d.temp;
                            document.getElementById('scd30-hum').innerText = d.humidity;
                            debug.innerText = "Updated " + new Date().toLocaleTimeString();
                        }}
                    }})
                    .catch(e => {{ debug.innerText = "Network Error"; }});
            }}
            </script>
        </div>
        """.format(
            status_color=status_color, 
            status=self.status_message, 
            co2=cur['co2'],
            temp=cur['temp'],
            hum=cur['humidity']
        )

    def update(self):
        # Optional: Periodic background tasks
        pass
