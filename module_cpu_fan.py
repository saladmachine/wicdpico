"""
WicdPico CPU Fan Module - Final Version (No RPM Display)
A stable, UI-controlled fan module using a non-blocking, time-delta
and count-delta approach for accurate RPM measurement.

RPM display has been removed as requested.
"""

from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
import json
import time
import board
import pwmio
import countio

# --- Hardware Configuration ---
FAN_PWM_PIN = board.GP2
FAN_TACHOMETER_PIN = board.GP9
PULSES_PER_REVOLUTION = 2
RPM_UPDATE_INTERVAL_S = 2.0 # How often to calculate RPM (in seconds)

class CpuFanModule(WicdpicoModule):
    VERSION = "1.2"

    def __init__(self, foundation):
        super().__init__(foundation)
        self._foundation = foundation
        
        # --- State Variables ---
        self._fan_speed_percent = 100
        self._last_action = "Initialized"

        # --- Hardware and RPM Timing Initialization ---
        self._fan_pwm = pwmio.PWMOut(FAN_PWM_PIN, frequency=25000)
        
        # External pull-up resistor is assumed for FAN_TACHOMETER_PIN
        self._tachometer = countio.Counter(FAN_TACHOMETER_PIN)
        
        # -- Initialize variables for delta measurement --
        self._last_rpm_update_time = time.monotonic()
        self._last_tachometer_count = self._tachometer.count 
        
        self.set_fan_speed(self._fan_speed_percent) # Start the fan

    def set_fan_speed(self, percent):
        self._fan_speed_percent = max(0, min(100, int(percent)))
        self._fan_pwm.duty_cycle = int(self._fan_speed_percent / 100 * 65535)
        self._last_action = "Speed set to {}%".format(self._fan_speed_percent)

    def update(self):
        # RPM measurement logic remains, but result is not displayed.
        now = time.monotonic()
        time_delta = now - self._last_rpm_update_time

        if time_delta >= RPM_UPDATE_INTERVAL_S:
            current_count = self._tachometer.count
            count_delta = current_count - self._last_tachometer_count
            # Calculation is retained for possible logging/future use
            # pulses_per_second = count_delta / time_delta
            # revolutions_per_second = pulses_per_second / PULSES_PER_REVOLUTION
            # self._fan_rpm = int(revolutions_per_second * 60)
            self._last_rpm_update_time = now
            self._last_tachometer_count = current_count

    def register_routes(self, server):
        @server.route("/cpu_fan/status", methods=["GET"])
        def get_status(request: Request):
            status_data = {
                "speed": self._fan_speed_percent,
                "last_action": self._last_action
            }
            return Response(request, json.dumps(status_data), content_type="application/json")

        @server.route("/cpu_fan/set_speed", methods=["POST"])
        def set_speed(request: Request):
            try:
                data = json.loads(request.body)
                self.set_fan_speed(data["speed"])
                return Response(request, '{"status": "ok"}')
            except Exception:
                return Response(request, '{"status": "error"}', status=400)

        @server.route("/cpu_fan/turn_on", methods=["POST"])
        def turn_on(request: Request):
            self.set_fan_speed(100)
            return Response(request, '{"status": "ok"}')

        @server.route("/cpu_fan/turn_off", methods=["POST"])
        def turn_off(request: Request):
            self.set_fan_speed(0)
            return Response(request, '{"status": "ok"}')

    def get_dashboard_html(self):
        """Returns the HTML and JavaScript for the control dashboard."""
        return """
<div class="card cpu-fan-card">
  <h2 class="card-title">CPU Fan Controller v{version}</h2>
  <label for="speed-slider">Speed: <span id="speed-label">--</span>%</label>
  <input id="speed-slider" class="slider" type="range" min="0" max="100" value="100">
  <hr style="margin: 20px 0;">
  <div class="buttons">
    <button class="on" onclick="turnOn()">TURN ON (100%)</button>
    <button class="off" onclick="turnOff()">TURN OFF (0%)</button>
  </div>
  <div style="text-align: center; margin-top: 15px; font-size: 0.8em; color: #888;">
    Last Action: <span id="last-action">...</span>
  </div>
</div>
<style>
    .card {{ box-sizing: border-box; width: 100%; }}
    .buttons {{ display: flex; gap: 10px; }}
    .buttons button {{ flex-grow: 1; }}
    .slider {{
        box-sizing: border-box;
        width: 100%; 
    }}
</style>
<script>
    const slider = document.getElementById('speed-slider');
    const speedLabel = document.getElementById('speed-label');
    const lastActionLabel = document.getElementById('last-action');
    let debounceTimer;

    function updateUI(data) {{
        speedLabel.innerText = data.speed;
        slider.value = data.speed;
        lastActionLabel.innerText = data.last_action;
    }}
    
    function fetchStatus() {{
        fetch('/cpu_fan/status').then(r => r.json()).then(data => updateUI(data));
    }}
    
    slider.addEventListener('input', (e) => {{
        const speed = e.target.value;
        speedLabel.innerText = speed;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {{
            fetch('/cpu_fan/set_speed', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{speed: parseInt(speed)}})
            }});
        }}, 250);
    }});
    slider.addEventListener('change', (e) => {{
        const speed = e.target.value;
        speedLabel.innerText = speed;
        fetch('/cpu_fan/set_speed', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{speed: parseInt(speed)}})
        }});
    }});

    function turnOn() {{ fetch('/cpu_fan/turn_on', {{method:'POST'}}); }}
    function turnOff() {{ fetch('/cpu_fan/turn_off', {{method:'POST'}}); }}

    setInterval(fetchStatus, 2000);
    fetchStatus(); // Initial fetch
</script>
""".format(version=self.VERSION)