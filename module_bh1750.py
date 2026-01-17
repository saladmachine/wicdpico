# module_bh1750.py
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class BH1750Module(WicdpicoModule):
    """
    Ambient Light Sensor Module (BH1750)
    Provides light sensing, event recording, and dashboard integration.
    """

    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Ambient Light"
        self.version = "v1.1"
        self.lux = None
        self.available = False
        self.recording_events = False
        self.last_lux = None
        self.lux_threshold = 5  # Hysteresis threshold
        self.dark_count = 0
        self.current_event = None
        self.event_log_filename = "/sd/Light_events.csv"
        self.csv_header_written = False
        self.i2c = foundation.i2c
        self.rtc = None
        self.rtc_available = False

        try:
            import board
            import adafruit_bh1750
            self.sensor = adafruit_bh1750.BH1750(self.i2c)
            self.available = True
            foundation.startup_print("BH1750 sensor initialized.")
        except Exception as e:
            self.available = False
            # FIXED F-STRING VIOLATION
            foundation.startup_print("BH1750 unavailable: {}".format(e))

        # Try to set up RTC (as in module_scd41.py)
        try:
            from adafruit_pcf8523.pcf8523 import PCF8523
            self.rtc = PCF8523(self.i2c)
            self.rtc_available = True
            foundation.startup_print("RTC initialized for BH1750 module.")
        except Exception as e:
            self.rtc_available = False
            foundation.startup_print("BH1750 RTC unavailable: {}".format(e))

    def get_light(self):
        if not self.available:
            return {"success": False, "error": "BH1750 not available"}
        try:
            self.lux = self.sensor.lux
            return {"success": True, "lux": round(self.lux, 2)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_routes(self):
        return [
            ("/light", self.handle_light_request),
            ("/toggle-event-recording", self.handle_toggle_recording),
            ("/read-light-events", self.handle_read_events),
            ("/clear-light-events", self.handle_clear_events),
        ]

    def register_routes(self, server):
        for route, handler in self.get_routes():
            server.route(route, methods=["POST"])(handler)

    def handle_light_request(self, request: Request):
        reading = self.get_light()
        # Optimization: Manual JSON construction
        if reading.get("success"):
            json_str = '{{"success": true, "lux": {}}}'.format(reading['lux'])
        else:
            # Escape quotes in error message just in case
            error_msg = reading.get('error', 'Unknown').replace('"', '\\"')
            json_str = '{{"success": false, "error": "{}"}}'.format(error_msg)
            
        return Response(request, json_str, content_type="application/json")

    def handle_toggle_recording(self, request: Request):
        self.recording_events = not self.recording_events
        if self.recording_events:
            self.dark_count = 0
            self.current_event = None
        state = "started" if self.recording_events else "stopped"
        # FIXED F-STRING VIOLATION
        return Response(request, "Light event recording {}.".format(state), content_type="text/plain")

    def handle_read_events(self, request: Request):
        try:
            with open(self.event_log_filename, "r") as f:
                log = f.read()
            return Response(request, log, content_type="text/plain")
        except Exception as e:
            # FIXED F-STRING VIOLATION
            return Response(request, "Error reading event log: {}".format(e), content_type="text/plain")

    def handle_clear_events(self, request: Request):
        try:
            with open(self.event_log_filename, "w") as f:
                f.write("timestamp,lux,event\n")
            self.csv_header_written = True
            return Response(request, "Light event log cleared.", content_type="text/plain")
        except Exception as e:
            # FIXED F-STRING VIOLATION
            return Response(request, "Error clearing event log: {}".format(e), content_type="text/plain")

    def _get_timestamp(self):
        # Match the SCD41 pattern: use RTC if available, else monotonic time
        if self.rtc_available and self.rtc is not None:
            dt = self.rtc.datetime
            return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                dt.tm_year, dt.tm_mon, dt.tm_mday, dt.tm_hour, dt.tm_min, dt.tm_sec
            )
        else:
            return "uptime_{:.1f}s".format(time.monotonic())

    def _log_event(self, lux, event_type):
        # Write event row to CSV, using correct timestamp
        if not self.csv_header_written:
            try:
                with open(self.event_log_filename, "r") as f:
                    pass
            except:
                with open(self.event_log_filename, "w") as f:
                    f.write("timestamp,lux,event\n")
                self.csv_header_written = True

        try:
            with open(self.event_log_filename, "a") as f:
                f.write("{},{},{}\n".format(self._get_timestamp(), lux, event_type))
        except Exception:
            pass

    def update(self):
        reading = self.get_light()
        if not reading["success"]:
            return

        lux = reading["lux"]
        self.last_lux = lux

        if self.recording_events:
            if lux > self.lux_threshold:
                self.dark_count = 0
                if self.current_event is None:
                    self.current_event = {"start_lux": lux}
                    self._log_event(lux, "start")
            else:
                if self.current_event is not None:
                    self.dark_count += 1
                    if self.dark_count >= 3:
                        self._log_event(lux, "stop")
                        self.current_event = None
                        self.dark_count = 0

    def get_dashboard_html(self):
        # The HTML/JS section appears to be F-string compliant (it uses standard Python strings)
        return """
        <div class="module">
            <h2>Ambient Light (BH1750)</h2>
            <div class="control-group">
                <button id="light-btn" onclick="getLux()">Read Light Level</button>
            </div>
            <div style="margin-top: 10px;">
                <div><strong>Lux:</strong> <span id="lux-value">--</span></div>
            </div>
            <div class="control-group" style="margin-top: 18px;">
                <button id="toggle-event-btn" onclick="toggleEventRecording()">Start Light Event Recording</button>
                <button id="read-events-btn" onclick="readLightEvents()">Read Light Events Log</button>
                <button id="clear-events-btn" onclick="clearLightEvents()">Clear Light Events Log</button>
            </div>
            <div id="light-error-display" style="color: red;"></div>
            <div id="event-log-status" style="margin-top:8px;font-size:0.92em;"></div>
        </div>
        <script>
        function getLux() {
            const btn = document.getElementById('light-btn');
            const luxEl = document.getElementById('lux-value');
            const errorEl = document.getElementById('light-error-display');

            btn.disabled = true;
            btn.textContent = 'Reading...';
            errorEl.textContent = '';

            fetch('/light', {method:'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        luxEl.textContent = data.lux;
                        errorEl.textContent = '';
                    } else {
                        errorEl.textContent = 'Error: ' + data.error;
                        luxEl.textContent = '--';
                    }
                })
                .catch(error => {
                    errorEl.textContent = 'Error: Failed to fetch status.';
                    luxEl.textContent = '--';
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = 'Read Light Level';
                });
        }
        document.addEventListener('DOMContentLoaded', getLux);

        let eventRecording = false;

        function toggleEventRecording() {
            const btn = document.getElementById('toggle-event-btn');
            btn.disabled = true;
            btn.textContent = (eventRecording ? 'Stopping...' : 'Starting...');
            fetch('/toggle-event-recording', {method:'POST'})
                .then(response => response.text())
                .then(message => {
                    eventRecording = !eventRecording;
                    btn.textContent = eventRecording ? 'Stop Light Event Recording' : 'Start Light Event Recording';
                    document.getElementById('event-log-status').textContent = message;
                })
                .catch(error => {
                    document.getElementById('event-log-status').textContent = 'Error: ' + error.message;
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = 'Start Light Event Recording';
                });
        }

        function readLightEvents() {
            const btn = document.getElementById('read-events-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';
            fetch('/read-light-events', {method:'POST'})
                .then(response => response.text())
                .then(log => {
                    alert('Light Events Log:\\n' + log);
                    document.getElementById('event-log-status').textContent = 'Log displayed.';
                })
                .catch(error => {
                    document.getElementById('event-log-status').textContent = 'Error: ' + error.message;
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = 'Read Light Events Log';
                });
        }

        function clearLightEvents() {
            const btn = document.getElementById('clear-events-btn');
            btn.disabled = true;
            btn.textContent = 'Clearing...';
            fetch('/clear-light-events', {method:'POST'})
                .then(response => response.text())
                .then(message => {
                    document.getElementById('event-log-status').textContent = message;
                })
                .catch(error => {
                    document.getElementById('event-log-status').textContent = 'Error: ' + error.message;
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = 'Clear Light Events Log';
                });
        }
        </script>
        """