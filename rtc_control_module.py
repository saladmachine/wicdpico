# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import board
import busio
from module_base import PicowicdModule # Assuming module_base.py now defines PicowicdModule
from adafruit_httpserver import Request, Response
from adafruit_pcf8523.pcf8523 import PCF8523

class RTCControlModule(PicowicdModule): # Updated base class name here as well for direct usage
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "RTC Control" # Corrected module name

        try:
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.rtc = PCF8523(self.i2c)
            self.rtc_available = True
            self.foundation.startup_print("RTC PCF8523 initialized successfully.")
        except Exception as e:
            self.rtc_available = False
            self.foundation.startup_print(f"RTC initialization failed: {str(e)}. RTC will be unavailable.")

        self.days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        self.last_update_time = time.monotonic()
        self.update_interval = 10 # seconds

    def register_routes(self, server):
        @server.route("/rtc-status", methods=['POST'])
        def rtc_status(request: Request):
            try:
                if not self.rtc_available:
                    return Response(request, "RTC not available", content_type="text/plain")

                current_time = self.rtc.datetime
                battery_low = self.rtc.battery_low
                lost_power = self.rtc.lost_power

                if battery_low or lost_power:
                    self.foundation.startup_print("RTC: Battery low or power lost detected. Setting time to 2000/01/01 00:00:00.")
                    t = time.struct_time((2000, 1, 1, 0, 0, 0, 5, -1, -1))
                    self.rtc.datetime = t
                    current_time = self.rtc.datetime
                    battery_low = self.rtc.battery_low
                    lost_power = self.rtc.lost_power

                    status_prefix = "RTC Reset: "
                else:
                    status_prefix = "RTC Status: "

                formatted_time = f"{self.days[current_time.tm_wday]} {current_time.tm_mon}/{current_time.tm_mday}/{current_time.tm_year} {current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}"

                status_text = f"Time: {formatted_time}<br>"
                status_text += f"Battery Low: {'Yes' if battery_low else 'No'}<br>"
                status_text += f"Lost Power: {'Yes' if lost_power else 'No'}"

                self.foundation.startup_print(f"{status_prefix}{formatted_time}, Bat Low: {battery_low}, Lost Pwr: {lost_power}")

                return Response(request, status_text, content_type="text/html")

            except Exception as e:
                error_msg = f"Error reading/setting RTC: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

    def get_dashboard_html(self):
        return '''
        <div class="module">
            <h3>RTC Control</h3>
            <div class="control-group">
                <button id="rtc-status-btn" onclick="getRTCStatus()">Get RTC Status</button>
            </div>
            <p id="rtc-display-status">RTC Status: Click button</p>
        </div>

        <script>
        // JavaScript for Get RTC Status
        function getRTCStatus() {
            const btn = document.getElementById('rtc-status-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/rtc-status', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'Get RTC Status';
                    document.getElementById('rtc-display-status').innerHTML = 'RTC Status: ' + result;
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'Get RTC Status';
                    document.getElementById('rtc-display-status').textContent = 'Error: ' + error.message;
                });
        }
        </script>
        '''

    def update(self):
        # FIX: Commented out the body of the update method to stop printing "Live RTC" updates.
        # The method itself remains to avoid AttributeError if foundation_core.py calls it.
        # This will prevent the "Live RTC..." messages from being printed.
        pass

    def cleanup(self):
        pass