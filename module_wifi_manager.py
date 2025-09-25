# module_wifi_manager.py
import time
import json
import wifi
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class WifiManagerModule(WicdpicoModule):
    """
    Manages the Wi-Fi hotspot timeout feature with a countdown display.
    """
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "WiFi Manager"
        self.version = "v1.1" # Version updated for new feature
        
        self.timeout_disabled = False
        self.ap_is_off_and_logged = False
        self.last_activity_time = time.monotonic()
        
        self.timeout_seconds = self.foundation.config.WIFI_AP_TIMEOUT_MINUTES * 60

    def get_routes(self):
        """Returns the list of routes for this module."""
        return [
            ("/toggle-hotspot-control", self.toggle_hotspot_control),
            ("/get-hotspot-status", self.get_hotspot_status),
        ]

    def register_routes(self, server):
        """Register all routes for this module with the server."""
        for route, handler in self.get_routes():
            server.route(route, methods=['POST', 'GET'])(handler)

    def _shut_down_wifi_and_sleep(self):
        """Shuts down the Wi-Fi AP to save power after a timeout."""
        self.foundation.startup_print("Initiating Wi-Fi AP shutdown due to inactivity...")
        try:
            if wifi.radio.enabled:
                wifi.radio.stop_ap()
                self.foundation.startup_print("Wi-Fi AP shut down.")
            else:
                self.foundation.startup_print("Wi-Fi AP already off.")
        except Exception as e:
            self.foundation.startup_print("Error shutting down AP: {}".format(e))

    def update(self):
        """
        Called from the main loop to check for the AP timeout.
        """
        if self.timeout_disabled:
            return
            
        now = time.monotonic()
        if wifi.radio.enabled:
            elapsed = now - self.last_activity_time
            if elapsed > self.timeout_seconds and not self.ap_is_off_and_logged:
                self._shut_down_wifi_and_sleep()
                self.ap_is_off_and_logged = True
        elif not self.ap_is_off_and_logged:
            self.ap_is_off_and_logged = True

    def toggle_hotspot_control(self, request: Request):
        """Handler for toggling the timeout or shutting down the AP."""
        self.last_activity_time = time.monotonic()

        if not self.timeout_disabled:
            self.timeout_disabled = True
            return Response(request, "Automatic timeout disabled. Hotspot will remain open.", content_type="text/plain")
        else:
            self._shut_down_wifi_and_sleep()
            self.ap_is_off_and_logged = True
            return Response(request, "Hotspot closed. Power cycle required to restart.", content_type="text/plain")

    def get_hotspot_status(self, request: Request):
        """Handler for getting the current status of the timeout feature."""
        self.last_activity_time = time.monotonic()
        
        # --- NEW: Calculate time remaining on the server ---
        now = time.monotonic()
        elapsed = now - self.last_activity_time
        time_remaining = max(0, self.timeout_seconds - elapsed)

        status = {
            "timeout_disabled": self.timeout_disabled,
            "time_remaining": int(time_remaining)
        }
        return Response(request, json.dumps(status), content_type="application/json")
        
    def get_dashboard_html(self):
        """Returns the HTML card for the Wi-Fi Hotspot Timeout controls."""
        return """
        <div class="module" id="hotspot-timeout-card">
          <h3>Wi-Fi Hotspot Timeout</h3>
          <p id="hotspot-timeout-desc">
            By default, the Wi-Fi hotspot (AP) will shut down after a period of inactivity for security and power saving.
          </p>
          <p id="countdown-container">
            Hotspot will close in: <span id="countdown-display" style="font-weight: bold;">--:--</span>
          </p>
          <button id="hotspot-btn" onclick="toggleHotspotControl()">Loading...</button>
          <div id="hotspot-result"></div>
        </div>
        <script>
        // --- NEW: Logic for the countdown timer ---
        let countdownInterval = null;

        function startCountdown(totalSeconds) {
            if (countdownInterval) {
                clearInterval(countdownInterval);
            }

            let remaining = totalSeconds;
            const display = document.getElementById('countdown-display');

            countdownInterval = setInterval(() => {
                if (remaining <= 0) {
                    clearInterval(countdownInterval);
                    display.textContent = "Closed";
                    return;
                }
                
                remaining--;
                
                const minutes = Math.floor(remaining / 60);
                const seconds = remaining % 60;
                display.textContent = String(minutes).padStart(2, '0') + ":" + String(seconds).padStart(2, '0');

            }, 1000);
        }

        function updateHotspotButtonState() {
            fetch('/get-hotspot-status')
                .then(response => response.json())
                .then(status => {
                    const btn = document.getElementById('hotspot-btn');
                    const countdownContainer = document.getElementById('countdown-container');

                    if (status.timeout_disabled) {
                        btn.textContent = 'Close Hotspot Now';
                        // NEW: Hide countdown when timeout is disabled
                        countdownContainer.style.display = 'none';
                        if (countdownInterval) clearInterval(countdownInterval);
                    } else {
                        btn.textContent = 'Keep Hotspot Open';
                        // NEW: Show countdown and start it
                        countdownContainer.style.display = 'block';
                        startCountdown(status.time_remaining);
                    }
                })
                .catch(() => {
                    document.getElementById('hotspot-btn').textContent = 'Status Unavailable';
                });
        }

        function toggleHotspotControl() {
            const btn = document.getElementById('hotspot-btn');
            const resultEl = document.getElementById('hotspot-result');
            
            if (btn.textContent === 'Close Hotspot Now') {
                if (confirm("Are you sure you want to close the Wi-Fi hotspot? A physical power cycle will be required to restart it.")) {
                    fetchAndHandleToggle(btn, resultEl);
                }
            } else {
                fetchAndHandleToggle(btn, resultEl);
            }
        }

        function fetchAndHandleToggle(btn, resultEl) {
            const isClosing = btn.textContent === 'Close Hotspot Now';
            btn.disabled = true;

            fetch('/toggle-hotspot-control', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    resultEl.textContent = result;
                    updateHotspotButtonState();
                    if (result.includes("Hotspot closed")) {
                        btn.disabled = true;
                    } else {
                        btn.disabled = false;
                    }
                })
                .catch(error => {
                    if (isClosing && error.message.includes('Failed to fetch')) {
                        resultEl.textContent = 'Success! Hotspot has been shut down.';
                    } else {
                        resultEl.textContent = 'Error: ' + error.message;
                        btn.disabled = false;
                        updateHotspotButtonState();
                    }
                });
        }

        document.addEventListener('DOMContentLoaded', updateHotspotButtonState);
        </script>
        """