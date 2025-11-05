# module_rtc.py
import time
import json
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
from adafruit_pcf8523.pcf8523 import PCF8523


class RTCModule(WicdpicoModule):
    """
    RTC Control Module that provides time exclusively in UTC for logging stability.
    This version focuses on setting the time accurately based on the configured base offset (-5).
    """
    
    def __init__(self, foundation):
        """Initializes the RTC using the foundation's shared I2C bus."""
        super().__init__(foundation)
        self.name = "RTC Control"
        self.version = "v1.10 (Setter Enforced)"
        self.rtc_available = False

        self.base_offset_hours = self.foundation.config.TIMEZONE_OFFSET_HOURS
        self.base_offset_seconds = self.base_offset_hours * 3600
        self.foundation.startup_print("✓ RTC Base Offset: UTC{}".format(self.base_offset_hours))

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

    def _get_utc_time_struct(self):
        """Calculates the current UTC struct_time based on the local time stored on the chip."""
        if not self.rtc_available:
            return None
        
        try:
            local_time_struct = self.rtc.datetime
            local_timestamp = time.mktime(local_time_struct)
            
            # Convert to UTC epoch time by removing the base offset
            utc_timestamp = local_timestamp - self.base_offset_seconds
            
            # Convert back to UTC struct_time using time.localtime() as gmtime() replacement
            utc_time_struct = time.localtime(utc_timestamp) 
            return utc_time_struct
        except Exception as e:
            self.foundation.startup_print("FATAL RTC Error in _get_utc_time_struct: {}".format(e))
            return None
        
    def get_formatted_utc_time(self):
        """
        Returns the current time as a formatted UTC string (ISO 8601 compatible 'Z').
        This is the only method other modules should use for logging timestamps.
        """
        utc_struct = self._get_utc_time_struct()
        if utc_struct is None:
            return "N/A"
            
        try:
            # Format: YYYY-MM-DDTHH:MM:SSZ (The standard ISO 8601 UTC format)
            return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
                utc_struct.tm_year,
                utc_struct.tm_mon,
                utc_struct.tm_mday,
                utc_struct.tm_hour,
                utc_struct.tm_min,
                utc_struct.tm_sec
            )
        except Exception as e:
            self.foundation.startup_print("FATAL RTC Formatting Error: {}".format(e))
            return "N/A"


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
        """Return RTC time as UTC timestamp for browser (legacy format)."""
        try:
            if not self.rtc_available:
                return Response(request, json.dumps({"error": "RTC not available"}), content_type="application/json")

            local_time_struct = self.rtc.datetime
            battery_low = self.rtc.battery_low
            local_timestamp = time.mktime(local_time_struct)

            # Convert local time (RTC) to UTC for browser
            utc_timestamp = local_timestamp - self.base_offset_seconds 
            
            # Note: The manual -3600 correction was removed in v1.9, which is correct, 
            # and should allow the display to be accurate now that the set-time is fixed.

            status = {
                "timestamp": utc_timestamp,
                "battery_low": battery_low
            }
            return Response(request, json.dumps(status), content_type="application/json")

        except Exception as e:
            return Response(request, json.dumps({"error": "Error reading RTC: {}".format(e)}), content_type="application/json")

    def rtc_set_time(self, request: Request):
        """Set RTC time to local time (UTC + offset)."""
        try:
            if not self.rtc_available:
                return Response(request, "RTC not available", content_type="text/plain")

            data = json.loads(request.body)
            utc_timestamp = int(data['timestamp'])
            
            # CRITICAL FIX: Ensure the time is set using the CORRECT base offset (-5)
            # The local time stored on the chip will now be the correct Standard Time.
            local_timestamp = utc_timestamp + self.base_offset_seconds
            new_time = time.localtime(local_timestamp)
            self.rtc.datetime = new_time

            # Display only UTC for browser feedback (using localtime() as gmtime() replacement)
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
        # Deprecated: Other modules should use get_formatted_utc_time()
        if self.rtc_available:
            try:
                return self.rtc.datetime
            except Exception:
                return None
        return None