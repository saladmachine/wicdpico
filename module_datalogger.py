# module_datalogger.py
import os
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response, GET, POST

class DataloggerModule(WicdpicoModule):
    """
    A module for manual and automatic data logging to an SD card.
    """

    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Data Logger"
        self.version = "v2.0"
        self.log_file_path = "/sd/darkbox.csv"
        
        # State variables for automatic logging
        self.is_logging = False
        self.log_interval = 60  # Default interval in seconds
        self.last_log_time = 0

    def get_routes(self):
        return [
            ("/log-data", self.handle_log_request),
            ("/start-logging", self.start_logging),
            ("/stop-logging", self.stop_logging),
        ]

    def register_routes(self, server):
        """Registers all endpoints for the logger."""
        for route, handler in self.get_routes():
            server.route(route, methods=[POST])(handler)
            
    def _perform_log(self):
        """Gathers data and writes a single row to the CSV. Returns status string."""
        sd_manager = self.foundation.get_module('sd_manager')
        if not sd_manager or not sd_manager.card_available:
            return "Error: SD Card not available."

        rtc = self.foundation.get_module('rtc')
        scd41 = self.foundation.get_module('scd41')
        bh1750 = self.foundation.get_module('bh1750')

        if not all([rtc, scd41, bh1750]):
            return "Error: Required sensor modules not loaded."

        try:
            now = rtc.current_time
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        except Exception:
            timestamp = "N/A"

        try:
            scd_data = scd41.get_sensor_reading()
            co2 = scd_data.get('co2', 'N/A')
            temp = scd_data.get('temperature', 'N/A')
            humidity = scd_data.get('humidity', 'N/A')
        except Exception:
            co2, temp, humidity = "N/A", "N/A", "N/A"

        try:
            light_data = bh1750.get_light()
            lux = light_data.get('lux', 'N/A')
        except Exception:
            lux = "N/A"

        csv_row = f"{timestamp},{co2},{temp},{humidity},{lux}\n"

        try:
            header_needed = False
            try:
                os.stat(self.log_file_path)
            except OSError:
                header_needed = True

            with open(self.log_file_path, "a") as f:
                if header_needed:
                    header = "Timestamp,CO2_ppm,Temperature_C,Humidity_RH,Lux\n"
                    f.write(header)
                f.write(csv_row)
            return f"Data logged to {self.log_file_path}"
        except Exception as e:
            return f"Error writing to file: {e}"

    def handle_log_request(self, request: Request):
        """Handles the 'Log Data' button press."""
        result = self._perform_log()
        return Response(request, result, content_type="text/plain")

    def start_logging(self, request: Request):
        """Handles the 'Start Log' button press."""
        try:
            data = request.json()
            interval = int(data.get("interval", 60))
            if interval < 5: # Prevent too-frequent logging
                interval = 5
            self.log_interval = interval
            self.is_logging = True
            self.last_log_time = time.monotonic() # Start timer immediately
            return Response(request, f"Logging started every {self.log_interval} seconds.", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {e}", content_type="text/plain")

    def stop_logging(self, request: Request):
        """Handles the 'Stop Log' button press."""
        self.is_logging = False
        return Response(request, "Logging stopped.", content_type="text/plain")
        
    def update(self):
        """Called continuously by the main loop to handle the timer."""
        if self.is_logging:
            now = time.monotonic()
            if (now - self.last_log_time) > self.log_interval:
                self._perform_log()
                self.last_log_time = now

    def get_dashboard_html(self):
        """Generates the HTML dashboard card for the logger."""
        return f"""
        <div class="module">
            <h2>{self.name} {self.version}</h2>
            
            <div class="control-group">
                <p><strong>Manual Log:</strong></p>
                <button id="log-data-btn" onclick="logDataNow()">Log Data Now</button>
            </div>

            <div class="control-group" style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
                <p><strong>Automatic Logging:</strong></p>
                <label for="log-interval">Log every (seconds):</label>
                <input type="number" id="log-interval" value="{self.log_interval}" style="width: 80px; padding: 5px;">
                <button id="toggle-log-btn" onclick="toggleLogging()">Start Log</button>
            </div>
            <p id="log-status"></p>
        </div>
        <script>
        // For manual logging button
        function logDataNow() {{
            const btn = document.getElementById('log-data-btn');
            const statusEl = document.getElementById('log-status');
            btn.disabled = true;
            btn.textContent = 'Logging...';
            statusEl.textContent = '';
            fetch('/log-data', {{ method: 'POST' }})
                .then(r => r.text()).then(result => {{
                    statusEl.textContent = result;
                    statusEl.style.color = result.startsWith('Error') ? 'red' : 'green';
                }}).catch(err => {{
                    statusEl.textContent = 'Error: ' + err.message;
                    statusEl.style.color = 'red';
                }}).finally(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Log Data Now';
                }});
        }}

        // For automatic logging button
        function toggleLogging() {{
            const btn = document.getElementById('toggle-log-btn');
            const statusEl = document.getElementById('log-status');
            const intervalInput = document.getElementById('log-interval');
            const isLogging = btn.textContent === 'Stop Log';

            btn.disabled = true;
            statusEl.textContent = '';
            
            if (isLogging) {{
                // --- STOP LOGGING ---
                fetch('/stop-logging', {{ method: 'POST' }})
                    .then(r => r.text()).then(result => {{
                        statusEl.textContent = result;
                        statusEl.style.color = 'orange';
                        btn.textContent = 'Start Log';
                        intervalInput.disabled = false;
                    }}).catch(err => {{
                        statusEl.textContent = 'Error: ' + err.message;
                    }});
            }} else {{
                // --- START LOGGING ---
                const interval = intervalInput.value;
                fetch('/start-logging', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ interval: interval }})
                }}).then(r => r.text()).then(result => {{
                    statusEl.textContent = result;
                    statusEl.style.color = 'green';
                    btn.textContent = 'Stop Log';
                    intervalInput.disabled = true;
                }}).catch(err => {{
                    statusEl.textContent = 'Error: ' + err.message;
                }});
            }}
            btn.disabled = false;
        }}
        </script>
        """