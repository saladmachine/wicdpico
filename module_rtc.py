# module_rtc.py
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
from adafruit_pcf8523.pcf8523 import PCF8523

class RTCModule(WicdpicoModule):
    """
    RTC Control Module that provides time exclusively in UTC for logging stability.
    Includes Heartbeat UI for reliable client-side time.
    """
    
    def __init__(self, foundation):
        """Initializes the RTC using the foundation's shared I2C bus."""
        super().__init__()
        self.foundation = foundation
        self.name = "RTC Clock"
        self.version = "v2.0 (Heartbeat)"
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
            return "1970-01-01T00:00:00Z"
            
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
            return "1970-01-01T00:00:00Z"

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
                return Response(request, '{"error": "RTC not available"}', content_type="application/json")

            local_time_struct = self.rtc.datetime
            battery_low = self.rtc.battery_low
            local_timestamp = time.mktime(local_time_struct)

            # Convert to UTC for browser
            utc_timestamp = local_timestamp - self.base_offset_seconds 
            
            # JSON-free string construction
            json_response = '{{"timestamp": {}, "battery_low": {}}}'.format(
                int(utc_timestamp), 
                "true" if battery_low else "false"
            )
            return Response(request, json_response, content_type="application/json")

        except Exception as e:
            return Response(request, '{{"error": "{}"}}'.format(str(e)), content_type="application/json")

    def rtc_set_time(self, request: Request):
        try:
            if not self.rtc_available:
                return Response(request, "RTC not available", content_type="text/plain")

            # Parse simple JSON body manually: {"timestamp": 123456789}
            body = request.body.decode('utf-8')
            # Extract numbers only
            import re
            match = re.search(r'\d+', body)
            if not match:
                 return Response(request, "Error: Invalid timestamp", content_type="text/plain")
                 
            utc_timestamp = int(match.group(0))
            
            # CRITICAL FIX: Ensure the time is set using the CORRECT base offset (-5)
            local_timestamp = utc_timestamp + self.base_offset_seconds
            new_time = time.localtime(local_timestamp)
            self.rtc.datetime = new_time

            formatted_time = self.get_formatted_utc_time()
            success_msg = "RTC time set. UTC: {}".format(formatted_time)
            return Response(request, success_msg, content_type="text/plain")

        except Exception as e:
            error_msg = "Error setting RTC time: {}".format(e)
            return Response(request, error_msg, content_type="text/plain")

    def get_dashboard_html(self):
        """Generates the HTML dashboard widget for RTC control."""
        
        # Initial status
        clock_state = "Connecting..."
        
        return """
        <div class="module">
            <h2>System Clock</h2>
            <div style="font-family: monospace; font-size: 1.8em; text-align: center; margin: 10px 0; padding: 10px; background: #eee; border-radius: 4px;">
                <span id="rtc-clock">--:--:--</span>
                <div id="rtc-date" style="font-size: 0.4em; color: #666;">--</div>
            </div>
            
            <div style="text-align: center; margin-bottom: 10px;">
                <span id="rtc-heartbeat" style="font-size: 0.8em; color:orange;">● Syncing...</span>
            </div>

            <div class="control-group">
                <button id="rtc-sync-btn" onclick="syncBrowserTime()">Sync to Browser Time</button>
            </div>
        </div>
        <script>
        let serverOffsetSeconds = 0;
        let lastSyncTime = 0;
        let heartbeatInterval = null;

        // Formats a date object to HH:MM:SS
        function formatTime(date) {{
            return date.toLocaleTimeString('en-GB'); // 24-hour format
        }}

        // Updates the visual clock every second based on local time + offset
        function updateClock() {{
            const now = new Date();
            // serverTime = localTime + offset
            const serverTime = new Date(now.getTime() + (serverOffsetSeconds * 1000));
            
            document.getElementById('rtc-clock').textContent = formatTime(serverTime);
            document.getElementById('rtc-date').textContent = serverTime.toLocaleDateString();
        }}

        // The Heartbeat: Pings the server to check connectivity and update offset
        function doHeartbeat() {{
            const hb = document.getElementById('rtc-heartbeat');
            hb.style.color = 'orange'; // Pinging
            
            const reqStart = Date.now();
            
            fetch('/rtc-status', {{ method: 'POST' }})
                .then(r => r.json())
                .then(data => {{
                    if(data.error) {{
                        hb.textContent = "● Error: " + data.error;
                        hb.style.color = 'red';
                        return;
                    }}
                    
                    const reqEnd = Date.now();
                    const latency = (reqEnd - reqStart) / 2; // Est. one-way trip
                    
                    // data.timestamp is UTC seconds from Pico
                    // We compare it to browser UTC to find the offset
                    const serverTimeMs = data.timestamp * 1000;
                    const browserTimeMs = Date.now(); // UTC
                    
                    // Improve offset calculation
                    // Ideally we just want the clock to match the server
                    // serverOffset = serverTime - browserTime
                    serverOffsetSeconds = (serverTimeMs - browserTimeMs) / 1000;

                    hb.textContent = "● Connected (Battery: " + (data.battery_low ? "LOW" : "OK") + ")";
                    hb.style.color = 'green';
                }})
                .catch(err => {{
                    hb.textContent = "● Offline";
                    hb.style.color = 'red';
                }});
        }}

        function syncBrowserTime() {{
            const btn = document.getElementById('rtc-sync-btn');
            btn.disabled = true;
            btn.textContent = 'Syncing...';
            
            // Send current browser UTC time
            const utc_timestamp = Math.floor(Date.now() / 1000);
            
            fetch('/rtc-set-time', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},  // Technically sending JSON string
                body: JSON.stringify({{ timestamp: utc_timestamp }})
            }})
            .then(r => r.text())
            .then(msg => {{
                alert(msg);
                doHeartbeat(); // Refresh immediately
            }})
            .finally(() => {{
                btn.disabled = false;
                btn.textContent = 'Sync to Browser Time';
            }});
        }}

        // Init
        setInterval(updateClock, 1000); // Visual tick every 1s
        setInterval(doHeartbeat, 10000); // 10s Heartbeat
        doHeartbeat(); // Initial ping
        </script>
        """.format(version=self.version)