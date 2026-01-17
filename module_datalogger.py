# module_datalogger.py
import os
import time
import re
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response, GET, POST

class DataloggerModule(WicdpicoModule):
    """
    A module for manual and automatic data logging to an SD card.
    Tailored for WicdAir (SCD30 + RTC).
    """

    def __init__(self, foundation):
        super().__init__()
        self.foundation = foundation
        self.name = "Data Logger"
        self.version = "v2.5 (WicdAir)"
        self.log_file_path = "/sd/wicdair_log.csv"
        
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
        sd_ok = sd_manager and sd_manager.card_available

        rtc = self.foundation.get_module('rtc')
        scd30 = self.foundation.get_module('scd30')
        
        # BH1750 is optional/removed for WicdAir
        
        if not rtc: return "Error: RTC module missing."
        if not scd30: return "Error: SCD30 module missing."

        try:
            # FIX: Use the reliable, formatted UTC time string from the RTCModule
            timestamp = rtc.get_formatted_utc_time()
        except Exception:
            timestamp = "1970-01-01T00:00:00Z"

        try:
            # SCD30 returns a dict with co2, temperature, humidity
            scd_data = scd30.get_reading()
            if not scd_data:
                print("[DataLog Debug] get_reading returned None/Empty")
                co2, temp, humidity = "N/A", "N/A", "N/A"
            else:
                co2 = scd_data.get('co2', 'N/A')
                temp = scd_data.get('temp', 'N/A') 
                humidity = scd_data.get('humidity', 'N/A')
        except Exception as e:
            print("[DataLog Debug] Sensor Read Error: {}".format(e))
            co2, temp, humidity = "N/A", "N/A", "N/A"

        # CSV Format: Timestamp(UTC), CO2(ppm), Temp(C), RH(%)
        csv_row = "{},{},{},{}\n".format(timestamp, co2, temp, humidity)

        if sd_ok:
            try:
                header_needed = False
                try:
                    os.stat(self.log_file_path)
                except OSError:
                    header_needed = True

                with open(self.log_file_path, "a") as f:
                    if header_needed:
                        header = "Timestamp_UTC,CO2_ppm,Temperature_C,Humidity_RH\n"
                        f.write(header)
                    f.write(csv_row)
                return "Logged to SD: {} ppm CO2".format(co2)
            except Exception as e:
                return "Error writing to file: {}".format(e)
        else:
            # Fallback: Print to console so user can verify logic
            print("[DataLog] " + csv_row.strip())
            return "SD Missing - Logged to Console: {} ppm".format(co2)

    def handle_log_request(self, request: Request):
        """Handles the 'Log Data' button press."""
        result = self._perform_log()
        return Response(request, result, content_type="text/plain")

    def start_logging(self, request: Request):
        """Handles the 'Start Log' button press."""
        sd_manager = self.foundation.get_module('sd_manager')
        if not sd_manager or not sd_manager.card_available:
            # Warn but allow console logging
            pass 

        try:
            # Manual JSON parsing to avoid module dependency
            body = request.body.decode('utf-8')
            match = re.search(r'\d+', body)
            if match:
                interval = int(match.group(0))
            else:
                interval = 60
                
            if interval < 5: interval = 5 # Safety limit

            self.log_interval = interval
            self.is_logging = True
            self.last_log_time = time.monotonic() # Start timer immediately
            return Response(request, "Logging Started ({}s interval)".format(self.log_interval), content_type="text/plain")
        except Exception as e:
            return Response(request, "Error: {}".format(e), content_type="text/plain")

    def stop_logging(self, request: Request):
        """Handles the 'Stop Log' button press."""
        self.is_logging = False
        return Response(request, "Logging Stopped.", content_type="text/plain")
        
    def update(self):
        """Called continuously by the main loop to handle the timer."""
        if self.is_logging:
            now = time.monotonic()
            if (now - self.last_log_time) > self.log_interval:
                self._perform_log()
                self.last_log_time = now

    def get_dashboard_html(self):
        """Generates the HTML dashboard card for the logger."""
        # Determine initial button state based on actual server state
        if self.is_logging:
            btn_text = "Stop Log"
            btn_disabled = "disabled" # Input disabled
        else:
            btn_text = "Start Log"
            btn_disabled = "" 

        return """
        <div class="module">
            <h2>{name}</h2>
            
            <div class="control-group">
                <p><strong>Manual Log:</strong></p>
                <button id="log-data-btn" onclick="logDataNow()">Log Data Now</button>
            </div>

            <div class="control-group" style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
                <p><strong>Automatic Logging:</strong></p>
                <label for="log-interval">Log every (seconds):</label>
                <input type="number" id="log-interval" value="{log_interval}" style="width: 80px; padding: 5px;" {btn_disabled}>
                <button id="toggle-log-btn" onclick="toggleLogging()">{btn_text}</button>
            </div>
            <p id="log-status" style="font-size:0.9em; min-height:20px;"></p>
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
        """.format(
            name=self.name,
            log_interval=self.log_interval,
            btn_text=btn_text,
            btn_disabled=btn_disabled
        )