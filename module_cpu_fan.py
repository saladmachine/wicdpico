"""
WicdPico CPU Fan Module - Final Version
A stable, UI-controlled fan module using a single PWM initialization
and the countio library for RPM feedback. Includes responsive UI elements.
"""

from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
import json
import time
import board
import pwmio
import countio

# --- Hardware Configuration ---
FAN_PWM_PIN = board.GP15
FAN_TACHOMETER_PIN = board.GP17
PULSES_PER_REVOLUTION = 2

class CpuFanModule(WicdpicoModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self._foundation = foundation
        
        # --- State Variables ---
        self._fan_speed_percent = 100
        self._fan_rpm = 0
        self._last_rpm_update = 0
        self._last_action = "Initialized"

        # --- Stable Hardware Initialization (Initialize ONCE) ---
        self._fan_pwm = pwmio.PWMOut(FAN_PWM_PIN, frequency=25000)
        self._tachometer = countio.Counter(FAN_TACHOMETER_PIN)
        self.set_fan_speed(self._fan_speed_percent) # Start the fan
        print("✓ CPU Fan module initialized.")

    def set_fan_speed(self, percent):
        """Sets the fan speed by adjusting the PWM duty cycle."""
        self._fan_speed_percent = max(0, min(100, int(percent)))
        self._fan_pwm.duty_cycle = int(self._fan_speed_percent / 100 * 65535)
        self._last_action = f"Speed set to {self._fan_speed_percent}%"
        print(f"SERIAL DEBUG: Speed set to {self._fan_speed_percent}%")

    def update(self):
        """The 'daemon' method, called continuously to measure RPM."""
        now = time.monotonic()
        if now - self._last_rpm_update > 2: # Update RPM every 2 seconds
            self._last_rpm_update = now
            
            # Use the delta method for stable RPM measurement
            start_count = self._tachometer.count
            time.sleep(0.5)
            end_count = self._tachometer.count
            
            pulses = end_count - start_count
            pulses_per_second = pulses / 0.5
            self._fan_rpm = int((pulses_per_second / PULSES_PER_REVOLUTION) * 60)

    def register_routes(self, server):
        """Registers all the web server API endpoints for this module."""
        @server.route("/cpu_fan/status", methods=["GET"])
        def get_status(request: Request):
            status_data = {
                "speed": self._fan_speed_percent,
                "rpm": self._fan_rpm,
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
        return f"""
<div class="card cpu-fan-card">
  <h2 class="card-title">CPU Fan Controller</h2>
  <div class="rpm-display"><span id="rpm">--</span> RPM</div>
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
    .rpm-display {{ font-size: 3em; font-weight: bold; text-align: center; margin: 20px 0; }}
</style>
<script>
    const slider = document.getElementById('speed-slider');
    const speedLabel = document.getElementById('speed-label');
    const rpmLabel = document.getElementById('rpm');
    const lastActionLabel = document.getElementById('last-action');
    let debounceTimer;

    function updateUI(data) {{
        rpmLabel.innerText = data.rpm;
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

    function turnOn() {{ fetch('/cpu_fan/turn_on', {{method:'POST'}}); }}
    function turnOff() {{ fetch('/cpu_fan/turn_off', {{method:'POST'}}); }}

    setInterval(fetchStatus, 2000);
    fetchStatus(); // Initial fetch
</script>
"""
