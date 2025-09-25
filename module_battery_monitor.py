# module_battery_monitor.py
import board
import analogio
import json
import os
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class BatteryMonitorModule(WicdpicoModule):
    """
    Battery Monitor Module with automatic logging of power state changes.
    """
    USB_THRESHOLD = 4.4
    BATTERY_THRESHOLD = 4.2

    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Battery Monitor"
        self.version = "v3.0"
        self.power_state = "UNKNOWN"
        self.log_file_path = "/sd/power.csv"

        try:
            self.adc = analogio.AnalogIn(board.VOLTAGE_MONITOR)
            self.voltage_available = True
            self._check_power_state() # Perform initial check
            self.last_known_power_state = self.power_state # Initialize tracking variable
            self.foundation.startup_print("Internal VSYS voltage monitoring initialized")
        except Exception as e:
            self.voltage_available = False
            self.foundation.startup_print("Voltage monitoring failed: {}".format(e))

    def update(self):
        """
        Called by the main loop to continuously check for power state changes.
        """
        if not self.voltage_available:
            return

        # Get the latest power state
        self._check_power_state()

        # If the state has changed from the last one we logged, log it.
        if self.power_state != self.last_known_power_state and self.power_state != "UNKNOWN":
            self._log_power_change()
            self.last_known_power_state = self.power_state # Update state after logging

    def _log_power_change(self):
        """Logs the new power state to a CSV file on the SD card."""
        sd_manager = self.foundation.get_module('sd_manager')
        rtc = self.foundation.get_module('rtc')

        # Only proceed if both SD card and RTC are available
        if not (sd_manager and sd_manager.card_available and rtc):
            return

        try:
            now = rtc.current_time
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        except Exception:
            timestamp = "N/A"

        csv_row = f"{timestamp},{self.power_state}\n"

        try:
            header_needed = False
            try:
                os.stat(self.log_file_path)
            except OSError:
                header_needed = True

            with open(self.log_file_path, "a") as f:
                if header_needed:
                    header = "Timestamp,PowerState\n"
                    f.write(header)
                f.write(csv_row)
        except Exception as e:
            print(f"Failed to log power state: {e}")


    def get_voltage(self):
        """Gets current system voltage from the VSYS pin."""
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
        """Updates the internal power_state based on current voltage."""
        voltage = self.get_voltage()
        if voltage is None:
            return
        
        current_state = self.power_state
        if voltage > self.USB_THRESHOLD:
            self.power_state = "USB"
        elif voltage < self.BATTERY_THRESHOLD:
            self.power_state = "BATTERY"
        elif self.power_state == "UNKNOWN":
             # Assign a state if we start in the middle threshold
            self.power_state = "USB" if voltage > 4.3 else "BATTERY"


    def get_routes(self):
        """Return the routes for this module."""
        return [
            ("/battery-status", self.get_battery_status),
        ]

    def register_routes(self, server):
        """Register all routes for this module with the server."""
        for route, handler in self.get_routes():
            server.route(route, methods=['GET', 'POST'])(handler)

    def get_battery_status(self, request: Request):
        """HTTP handler to get current battery voltage and power source."""
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

    def get_dashboard_html(self):
        """Generate HTML template for the enhanced battery monitor widget."""
        return """
        <div class="module">
            <h2>Battery Monitor</h2>
            <p>Monitors the Pico's power source and voltage.</p>
            <div class="control-group">
                <button id="battery-status-btn" onclick="getBatteryStatus()">Get Status</button>
            </div>
            <div id="battery-status-display" style="margin-top: 10px;">
                <div><strong>Voltage:</strong> <span id="voltage-value">--</span> V</div>
                <div><strong>Power Source:</strong> <span id="power-source-value">--</span></div>
            </div>
            <p id="battery-error-display" style="color: red;"></p>
        </div>
        <script>
        function getBatteryStatus() {{
            const btn = document.getElementById('battery-status-btn');
            const voltageEl = document.getElementById('voltage-value');
            const sourceEl = document.getElementById('power-source-value');
            const errorEl = document.getElementById('battery-error-display');
            
            btn.disabled = true;
            btn.textContent = 'Reading...';
            errorEl.textContent = '';

            fetch('/battery-status')
                .then(response => response.json())
                .then(data => {{
                    if (data.error) {{
                        errorEl.textContent = 'Error: ' + data.error;
                        voltageEl.textContent = '--';
                        sourceEl.textContent = '--';
                    }} else {{
                        voltageEl.textContent = data.voltage;
                        sourceEl.textContent = data.power_state;
                    }}
                }})
                .catch(error => {{
                    errorEl.textContent = 'Error: Failed to fetch status.';
                }})
                .finally(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Get Status';
                }});
        }}
        document.addEventListener('DOMContentLoaded', getBatteryStatus);
        </script>
        """.format(version=self.version)