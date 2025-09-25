# module_scd41.py (Refactored with Dashboard UI)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import adafruit_scd4x
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class SCD41Module(WicdpicoModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "SCD41 CO2 Sensor"
        self.foundation = foundation
        self.i2c = self.foundation.i2c  # Access the shared I2C bus from foundation, as with RTC
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
        self.foundation.startup_print("SCD41 module created. Status: '{}'".format(self.status_message))

    def _initialize_sensor(self):
        if not self.i2c:
            self.status_message = "Error: I2C Not Available"
            self.last_error = "Foundation failed to provide I2C bus."
            self.sensor_available = False
            return
        try:
            self.scd41 = adafruit_scd4x.SCD4X(self.i2c)
            serial_num = self.scd41.serial_number
            self.sensor_serial = "{:04X}-{:04X}-{:04X}".format(serial_num[0], serial_num[1], serial_num[2])
            self.sensor_available = True
            self.status_message = "Ready (Single-Shot Mode)"
        except Exception as e:
            self.sensor_available = False
            self.last_error = "SCD41 initialization failed: {}".format(e)
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
            self.last_error = "Reading failed: {}".format(e)
            return {"success": False, "error": self.last_error}

    def set_altitude(self, altitude):
        if not self.sensor_available:
            return False, "Sensor not available"
        try:
            self.scd41.altitude = altitude
            return True, "Altitude set to {}m".format(altitude)
        except Exception as e:
            return False, str(e)

    def update(self):
        pass

    def register_routes(self, server):
        @server.route("/scd41/read", methods=['POST'])
        def read_route(request: Request):
            result_dict = self.get_sensor_reading()
            if result_dict.get("success"):
                response_text = "CO2: {} ppm, Temp: {}°C, RH: {}%".format(
                    result_dict['co2'], result_dict['temperature'], result_dict['humidity']
                )
                return Response(request, response_text, content_type="text/plain")
            else:
                error_msg = result_dict.get('error', 'Unknown error')
                return Response(request, "Failed: {}".format(error_msg), content_type="text/plain")
        self.foundation.startup_print("SCD41 route '/scd41/read' registered.")

    def get_dashboard_html(self):
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        error_html = "<br><span class=\"error-text\"><strong>Error:</strong> {}</span>".format(self.last_error) if self.last_error else ""
        if self.last_co2 is not None:
            age = time.monotonic() - self.last_reading_time
            last_reading_text = "<strong>{} ppm</strong>, {}°C, {}% RH ({}s ago)".format(
                self.last_co2, self.last_temp, self.last_humidity, int(age)
            )
        else:
            last_reading_text = "No readings yet"
        return """
        <style>
        .module {{
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 18px 20px;
            margin: 10px auto;
            max-width: 420px;
            background: #fcfcfd;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }}
        .status {{
            border-left: 6px solid {status_color};
            padding-left: 12px;
            margin-bottom: 10px;
        }}
        .error-text {{
            color: #dc3545;
        }}
        #scd41-read-btn {{
            margin-top: 12px;
            width: 100%;
            padding: 12px;
            font-size: 1.05em;
            border-radius: 4px;
        }}
        </style>
        <div class="module">
            <h2>{name}</h2>
            <div class="status">
                <strong>Status:</strong> <span style="color: {status_color};">{status_message}</span><br>
                <strong>Last Reading:</strong> <span id="scd41-last-reading">{last_reading_text}</span>
                {error_html}
            </div>
            <p><small>Serial: {sensor_serial}</small></p>
            <button id="scd41-read-btn" onclick="getSCD41Reading()">Get Fresh Reading (takes 5s)</button>
        </div>
        <script>
        function getSCD41Reading() {{
            var statusSpan = document.getElementById('scd41-last-reading');
            var button = document.getElementById('scd41-read-btn');
            statusSpan.innerHTML = '<strong>Reading... (Please wait 5 seconds)</strong>';
            button.disabled = true;
            fetch('/scd41/read', {{ method: 'POST' }})
                .then(function(response) {{ return response.text(); }})
                .then(function(result) {{
                    statusSpan.innerHTML = '<strong>' + result + '</strong> (just now)';
                }})
                .catch(function(error) {{
                    statusSpan.textContent = 'Error: ' + error.message;
                }})
                .finally(function() {{
                    button.disabled = false;
                }});
        }}
        </script>
        """.format(
            status_color=status_color,
            name=self.name,
            status_message=self.status_message,
            last_reading_text=last_reading_text,
            error_html=error_html,
            sensor_serial=self.sensor_serial
        )