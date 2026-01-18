import board
import analogio
import json
import os
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class BatteryMonitorModule(WicdpicoModule):
    """
    Battery Monitor Module for WicdPico system.
    Detects USB/Battery transitions, logs events, and provides dashboard controls.
    """
    USB_THRESHOLD = 4.3
    BATTERY_THRESHOLD = 4.2

    def __init__(self, foundation):
        super().__init__()
        self.foundation = foundation
        self.name = "Battery Monitor"
        self.version = "v4.0"
        self.power_state = "UNKNOWN"
        self.log_file_path = "/sd/power_events.csv"
        self.voltage_available = False

        try:
            self.adc = analogio.AnalogIn(board.VOLTAGE_MONITOR)
            self.voltage_available = True
            self._check_power_state()
            self.last_known_power_state = self.power_state
            self.foundation.startup_print("Internal VSYS voltage monitoring initialized")
        except Exception as e:
            self.voltage_available = False
            self.foundation.startup_print("Voltage monitoring failed: {}".format(e))

        # RTC for timestamps, optional
        self.rtc = None
        self.rtc_available = False
        try:
            from adafruit_pcf8523.pcf8523 import PCF8523
            self.rtc = PCF8523(foundation.i2c)
            self.rtc_available = True
            foundation.startup_print("RTC initialized for Battery Monitor.")
        except Exception as e:
            self.rtc_available = False
            foundation.startup_print("Battery Monitor RTC unavailable: {}".format(e))

        self.csv_header_written = False

    def update(self):
        """Check for power state changes and log transitions."""
        if not self.voltage_available:
            return
        self._check_power_state()
        if self.power_state != self.last_known_power_state and self.power_state != "UNKNOWN":
            self._log_power_change()
            self.last_known_power_state = self.power_state

    def _get_timestamp(self):
        """Return RTC or monotonic timestamp."""
        if self.rtc_available and self.rtc is not None:
            dt = self.rtc.datetime
            return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                dt.tm_year, dt.tm_mon, dt.tm_mday, dt.tm_hour, dt.tm_min, dt.tm_sec
            )
        else:
            return "uptime_{:.1f}s".format(time.monotonic())

    def _log_power_change(self):
        """Log transition to CSV with timestamp, power state, voltage."""
        try:
            # Write header if needed
            if not self.csv_header_written:
                try:
                    os.stat(self.log_file_path)
                except OSError:
                    with open(self.log_file_path, "w") as f:
                        f.write("Timestamp,PowerState,Voltage\n")
                self.csv_header_written = True
            with open(self.log_file_path, "a") as f:
                f.write("{},{},{}\n".format(self._get_timestamp(), self.power_state, self.get_voltage()))
        except Exception as e:
            print("Failed to log power state: {}".format(e))

    def get_voltage(self):
        """Return system voltage from VSYS pin."""
        if not self.voltage_available:
            return None
        try:
            raw_value = self.adc.value
            voltage = (raw_value * 3.0 * 3.3) / 65535.0
            return round(voltage, 2)
        except Exception as e:
            self.foundation.startup_print("Error reading voltage: {}".format(e))
            return None

    def _check_power_state(self):
        """Determine power state from voltage thresholds."""
        voltage = self.get_voltage()
        if voltage is None:
            return
        if voltage > self.USB_THRESHOLD:
            self.power_state = "USB"
        elif voltage < self.BATTERY_THRESHOLD:
            self.power_state = "BATTERY"
        elif self.power_state == "UNKNOWN":
            # Assign a state if we start in between thresholds
            self.power_state = "USB" if voltage > 4.3 else "BATTERY"

    def get_routes(self):
        return [
            ("/battery-status", self.get_battery_status),
            ("/read-power-events", self.handle_read_events),
            ("/clear-power-events", self.handle_clear_events),
        ]

    def register_routes(self, server):
        for route, handler in self.get_routes():
            server.route(route, methods=['POST'])(handler)

    def get_battery_status(self, request: Request):
        """Return voltage and power state as JSON."""
        if not self.voltage_available:
            return Response(request, json.dumps({"error": "Monitoring unavailable"}), content_type="application/json")
        self._check_power_state()
        voltage = self.get_voltage()
        if voltage is None:
            return Response(request, json.dumps({"error": "Error reading voltage"}), content_type="application/json")
        status = {
            "voltage": voltage,
            "power_state": self.power_state
        }
        return Response(request, json.dumps(status), content_type="application/json")

    def handle_read_events(self, request: Request):
        try:
            with open(self.log_file_path, "r") as f:
                log = f.read()
            return Response(request, log, content_type="text/plain")
        except Exception as e:
            return Response(request, "Error reading power event log: {}".format(e), content_type="text/plain")

    def handle_clear_events(self, request: Request):
        try:
            with open(self.log_file_path, "w") as f:
                f.write("Timestamp,PowerState,Voltage\n")
            self.csv_header_written = True
            return Response(request, "Power event log cleared.", content_type="text/plain")
        except Exception as e:
            return Response(request, "Error clearing power event log: {}".format(e), content_type="text/plain")

    def get_dashboard_html(self):
        return """
        <div class="module">
            <h2>Battery Monitor</h2>
            <p>Monitors the Pico's power source and voltage.</p>
            <div class="control-group">
                <button id="battery-status-btn" onclick="getBatteryStatus()">Get Status</button>
                <button id="read-power-events-btn" onclick="readPowerEvents()">Read Power Event Log</button>
                <button id="clear-power-events-btn" onclick="clearPowerEvents()">Clear Power Event Log</button>
            </div>
            <div id="battery-status-display" style="margin-top: 10px;">
                <div><strong>Voltage:</strong> <span id="voltage-value">--</span> V</div>
                <div><strong>Power Source:</strong> <span id="power-source-value">--</span></div>
            </div>
            <p id="battery-error-display" style="color: red;"></p>
            <p id="power-event-status" style="font-size:0.92em;"></p>
        </div>
        <script>
        function getBatteryStatus() {
            const btn = document.getElementById('battery-status-btn');
            const voltageEl = document.getElementById('voltage-value');
            const sourceEl = document.getElementById('power-source-value');
            const errorEl = document.getElementById('battery-error-display');
            btn.disabled = true;
            btn.textContent = 'Reading...';
            errorEl.textContent = '';
            fetch('/battery-status', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        errorEl.textContent = 'Error: ' + data.error;
                        voltageEl.textContent = '--';
                        sourceEl.textContent = '--';
                    } else {
                        voltageEl.textContent = data.voltage;
                        sourceEl.textContent = data.power_state;
                    }
                })
                .catch(error => {
                    errorEl.textContent = 'Error: Failed to fetch status.';
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = 'Get Status';
                });
        }
        document.addEventListener('DOMContentLoaded', getBatteryStatus);

        function readPowerEvents() {
            const btn = document.getElementById('read-power-events-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';
            fetch('/read-power-events', {method: 'POST'})
                .then(response => response.text())
                .then(log => {
                    alert('Power Events Log:\\n' + log);
                    document.getElementById('power-event-status').textContent = 'Log displayed.';
                })
                .catch(error => {
                    document.getElementById('power-event-status').textContent = 'Error: ' + error.message;
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = 'Read Power Event Log';
                });
        }

        function clearPowerEvents() {
            const btn = document.getElementById('clear-power-events-btn');
            btn.disabled = true;
            btn.textContent = 'Clearing...';
            fetch('/clear-power-events', {method: 'POST'})
                .then(response => response.text())
                .then(message => {
                    document.getElementById('power-event-status').textContent = message;
                })
                .catch(error => {
                    document.getElementById('power-event-status').textContent = 'Error: ' + error.message;
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.textContent = 'Clear Power Event Log';
                });
        }
        </script>
        """