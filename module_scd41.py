# module_scd41.py (Refactored with Dashboard UI)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import adafruit_scd4x
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class SCD41Module(WicdpicoModule):
    def __init__(self, foundation, i2c_bus):
        super().__init__(foundation)
        self.name = "SCD41 CO2 Sensor"
        self.foundation = foundation
        self.i2c = i2c_bus  # Accept the shared I2C bus
        self.scd41 = None
        self.sensor_available = False
        self.last_reading_time = 0
        self.last_co2 = None
        self.last_temp = None
        self.last_humidity = None
        self.sensor_serial = "N/A"
        self.status_message = "Initializing..."
        self.last_error = None
        self._initialize_sensor()
        self.foundation.startup_print(f"SCD41 module created. Status: '{self.status_message}'")

    def _initialize_sensor(self):
        if not self.i2c:
            self.status_message = "Error: I2C Not Available"
            self.last_error = "Foundation failed to provide I2C bus."
            self.sensor_available = False
            return
        try:
            self.scd41 = adafruit_scd4x.SCD4X(self.i2c)
            serial_num = self.scd41.serial_number
            self.sensor_serial = f"{serial_num[0]:04X}-{serial_num[1]:04X}-{serial_num[2]:04X}"
            self.sensor_available = True
            self.status_message = "Ready (Single-Shot Mode)"
        except Exception as e:
            self.sensor_available = False
            self.last_error = f"SCD41 initialization failed: {e}"
            self.status_message = "Error: Not Found"

    def get_sensor_reading(self):
        if not self.sensor_available:
            return {"success": False, "error": "Sensor not available"}
        
        try:
            self.scd41.measure_single_shot()
            time.sleep(5) 
            
            co2_ppm = self.scd41.CO2
            temp_c = round(self.scd41.temperature, 1)
            humidity = round(self.scd41.relative_humidity, 1)
            
            self.last_co2 = int(co2_ppm)
            self.last_temp = temp_c
            self.last_humidity = humidity
            self.last_reading_time = time.monotonic()
            
            return { "success": True, "co2": self.last_co2, "temperature": temp_c, "humidity": humidity }
        except Exception as e:
            self.last_error = f"Reading failed: {e}"
            return {"success": False, "error": self.last_error}

    def set_altitude(self, altitude):
        if not self.sensor_available:
            return False, "Sensor not available"
        try:
            self.scd41.altitude = altitude
            return True, f"Altitude set to {altitude}m"
        except Exception as e:
            return False, str(e)

    def update(self):
        pass

    def register_routes(self, server):
        @server.route("/scd41/read", methods=['POST'])
        def read_route(request: Request):
            result_dict = self.get_sensor_reading()
            if result_dict.get("success"):
                response_text = f"CO2: {result_dict['co2']} ppm, Temp: {result_dict['temperature']}°C, RH: {result_dict['humidity']}%"
                return Response(request, response_text, content_type="text/plain")
            else:
                error_msg = result_dict.get('error', 'Unknown error')
                return Response(request, f"Failed: {error_msg}", content_type="text/plain")
        self.foundation.startup_print("SCD41 route '/scd41/read' registered.")

    def get_dashboard_html(self):
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        error_html = f'<br><span class="error-text"><strong>Error:</strong> {self.last_error}</span>' if self.last_error else ""
        
        if self.last_co2 is not None:
            age = time.monotonic() - self.last_reading_time
            last_reading_text = f"<strong>{self.last_co2} ppm</strong>, {self.last_temp}°C, {self.last_humidity}% RH ({int(age)}s ago)"
        else:
            last_reading_text = "No readings yet"

        return f'''
        <div class="module">
            <h3>{self.name}</h3>
            <div class="status" style="border-left-color: {status_color};">
                <strong>Status:</strong> <span style="color: {status_color};">{self.status_message}</span><br>
                <strong>Last Reading:</strong> <span id="scd41-last-reading">{last_reading_text}</span>
                {error_html}
            </div>
            <p><small>Serial: {self.sensor_serial}</small></p>
            <button id="scd41-read-btn" onclick="getSCD41Reading()">Get Fresh Reading (takes 5s)</button>
        </div>
        <script>
        function getSCD41Reading() {{
            const statusSpan = document.getElementById('scd41-last-reading');
            const button = document.getElementById('scd41-read-btn');
            statusSpan.innerHTML = '<strong>Reading... (Please wait 5 seconds)</strong>';
            button.disabled = true;

            fetch('/scd41/read', {{ method: 'POST' }})
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