# module_rtc.py
import time
import json
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
from adafruit_pcf8523.pcf8523 import PCF8523


class RTCModule(WicdpicoModule):
    """
    RTC Control Module that uses a configured timezone offset.
    """

    def __init__(self, foundation):
        """Initializes the RTC using the foundation's shared I2C bus."""
        super().__init__(foundation)
        self.name = "RTC Control"
        self.version = ""
        self.rtc_available = False

        offset_hours = self.foundation.config.TIMEZONE_OFFSET_HOURS
        self.timezone_offset_seconds = offset_hours * 3600
        self.foundation.startup_print("✓ RTC using timezone offset: UTC{}".format(offset_hours))



        self.i2c = self.foundation.i2c
        if self.i2c is None:
            self.foundation.startup_print("✗ RTCModule: I2C bus not available from foundation.")
            return

        try:
            self.rtc = PCF8523(self.i2c)
            self.rtc_available = True
            self.foundation.startup_print("✓ RTC pcf8523 initialized successfully.")
        except Exception as e:
            self.rtc_available = False
            self.foundation.startup_print("✗ RTC initialization failed: {}. RTC will be unavailable.".format(e))

    def get_routes(self):
        return [
            ("/rtc-status", self.rtc_status),
            ("/rtc-set-time", self.rtc_set_time),
        ]

    def register_routes(self, server):
        """Registers all routes for this module with the given server."""
        for route, handler in self.get_routes():
            server.route(route, methods=['POST'])(handler)

    def rtc_status(self, request: Request):
        """Return RTC time as UTC timestamp for browser."""
        try:
            if not self.rtc_available:
                return Response(request, json.dumps({"error": "RTC not available"}), content_type="application/json")

            local_time_struct = self.rtc.datetime
            battery_low = self.rtc.battery_low
            local_timestamp = time.mktime(local_time_struct)

            # Convert local time (RTC) to UTC for browser
            utc_timestamp = local_timestamp - self.timezone_offset_seconds

            status = {
                "timestamp": utc_timestamp,
                "battery_low": battery_low
            }
            return Response(request, json.dumps(status), content_type="application/json")

        except Exception as e:
            return Response(request, json.dumps({"error": "Error reading RTC: {}".format(e)}), content_type="application/json")

    def rtc_set_time(self, request: Request):
        """Set RTC time to local time (UTC + offset), and display only UTC for feedback."""
        try:
            if not self.rtc_available:
                return Response(request, "RTC not available", content_type="text/plain")

            data = json.loads(request.body)
            utc_timestamp = int(data['timestamp'])

            # Store as local time on RTC
            local_timestamp = utc_timestamp + self.timezone_offset_seconds
            new_time = time.localtime(local_timestamp)
            self.rtc.datetime = new_time

            # Display only UTC for browser time
            # Format: YYYY-MM-DD HH:MM:SS UTC
            utc_time_struct = time.localtime(utc_timestamp)
            formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} UTC".format(
                utc_time_struct.tm_year,
                utc_time_struct.tm_mon,
                utc_time_struct.tm_mday,
                utc_time_struct.tm_hour,
                utc_time_struct.tm_min,
                utc_time_struct.tm_sec
            )
            success_msg = "RTC time set. UTC: {}".format(formatted_time)
            return Response(request, success_msg, content_type="text/plain")

        except Exception as e:
            error_msg = "Error setting RTC time: {}".format(e)
            return Response(request, error_msg, content_type="text/plain")

    def get_dashboard_html(self):
        """Generates the HTML dashboard widget for RTC control."""
        return """
        <div class="module">
            <h2>RTC Control {version}</h2>
            <div class="control-group">
                <button id="rtc-status-btn" onclick="getRTCStatus()">Get RTC Status</button>
                <button id="rtc-set-time-btn" onclick="setRTCTime()">Set Time from Browser</button>
            </div>
            <p id="rtc-display-status">RTC Status: Click button</p>
            <p id="rtc-set-status"></p>
        </div>
        <script>
        function getRTCStatus() {{
            const btn = document.getElementById('rtc-status-btn');
            const displayEl = document.getElementById('rtc-display-status');
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/rtc-status', {{ method: 'POST' }})
                .then(r => r.json())
                .then(data => {{
                    if(data.error) {{
                        displayEl.innerHTML = "RTC Status: <br>Error: " + data.error;
                        return;
                    }}
                    // Interpret as local time in browser (it is sent as UTC)
                    const dt = new Date(data.timestamp * 1000);
                    const options = {{
                        year: 'numeric', month: 'numeric', day: 'numeric',
                        hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true
                    }};
                    const formattedTime = dt.toLocaleString(undefined, options);
                    const batteryStatus = data.battery_low ? "Low" : "OK";
                    displayEl.innerHTML = "RTC Status: <br>Time: " + formattedTime + "<br>Battery: " + batteryStatus;
                }})
                .catch(err => {{
                    displayEl.textContent = 'Error: ' + err.message;
                }})
                .finally(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Get RTC Status';
                }});
        }}
        function setRTCTime() {{
            const btn = document.getElementById('rtc-set-time-btn');
            const statusEl = document.getElementById('rtc-set-status');
            btn.disabled = true;
            btn.textContent = 'Setting...';

            // This is UTC seconds since epoch
            const utc_timestamp = Math.floor(new Date().getTime() / 1000);

            fetch('/rtc-set-time', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ timestamp: utc_timestamp }})
            }})
                .then(r => r.text())
                .then(result => {{
                    statusEl.textContent = result;
                    statusEl.style.color = 'green';
                    getRTCStatus();
                }})
                .catch(err => {{
                    statusEl.textContent = 'Error: ' + err.message;
                    statusEl.style.color = 'red';
                }})
                .finally(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Set Time from Browser';
                }});
        }}
        </script>
        """.format(version=self.version)

    @property
    def current_time(self):
        if self.rtc_available:
            try:
                return self.rtc.datetime
            except Exception:
                return None
        return None