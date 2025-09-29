"""
WicdPico EMC2101 Fan Module
Controls a PWM fan via Adafruit EMC2101 I2C Fan Controller.
Uses shared foundation I2C bus and Adafruit EMC2101 library.
Provides a dashboard widget with slider and buttons.
Follows the same pattern as other I2C modules in the repo.
Implements manual fan speed control according to Adafruit's official documentation.
"""

from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
import json

import adafruit_emc2101

class Emc2101Module(WicdpicoModule):
    VERSION = "1.9"

    def __init__(self, foundation):
        super().__init__(foundation)
        self._foundation = foundation
        self._i2c = self._foundation.i2c
        self._fan_speed_percent = 100
        self._last_action = "Initialized"
        self.available = False

        try:
            self.emc2101 = adafruit_emc2101.EMC2101(self._i2c)
            # Do NOT attempt to set LUT state; manual_fan_speed works by default per Adafruit docs
            self.available = True
            self._last_action = "EMC2101 initialized OK"
            self.set_fan_speed(self._fan_speed_percent)
        except Exception as e:
            self._last_action = "I2C init error: {}".format(e)
            self.available = False

    def set_fan_speed(self, percent):
        percent = max(0, min(100, int(percent)))
        self._fan_speed_percent = percent
        if not self.available:
            self._last_action = "EMC2101 not available"
            return
        try:
            # Set manual fan speed only, as per Adafruit official documentation
            self.emc2101.manual_fan_speed = self._fan_speed_percent
            self._last_action = "Speed set to {}%".format(self._fan_speed_percent)
        except Exception as e:
            self._last_action = "I2C error: {}".format(e)

    def update(self):
        pass

    def register_routes(self, server):
        @server.route("/emc2101/status", methods=["GET"])
        def get_status(request: Request):
            status_data = {
                "speed": self._fan_speed_percent,
                "last_action": self._last_action,
                "available": self.available
            }
            return Response(request, json.dumps(status_data), content_type="application/json")

        @server.route("/emc2101/set_speed", methods=["POST"])
        def set_speed(request: Request):
            try:
                data = json.loads(request.body)
                self.set_fan_speed(data["speed"])
                return Response(request, '{"status": "ok"}')
            except Exception:
                return Response(request, '{"status": "error"}', status=400)

        @server.route("/emc2101/turn_on", methods=["POST"])
        def turn_on(request: Request):
            self.set_fan_speed(100)
            return Response(request, '{"status": "ok"}')

        @server.route("/emc2101/turn_off", methods=["POST"])
        def turn_off(request: Request):
            self.set_fan_speed(0)
            return Response(request, '{"status": "ok"}')

    def get_dashboard_html(self):
        if not self.available:
            return """
            <div class="module">
                <h2>EMC2101 Fan Control {version}</h2>
                <div style="color: red;">EMC2101 not detected. Check wiring, power, and I2C address (default 0x4C).</div>
                <p id="fan-status">Last action: {last_action}</p>
            </div>
            """.format(version=self.VERSION, last_action=self._last_action)

        return """
        <div class="module">
            <h2>EMC2101 Fan Control {version}</h2>
            <div class="control-group">
                <input type="range" min="0" max="100" value="{speed}" id="fan-speed-slider" oninput="updateFanSpeedLabel(this.value)">
                <span id="fan-speed-label">{speed}%</span>
                <button onclick="setFanSpeed()">Set Speed</button>
                <button onclick="turnFanOn()">On</button>
                <button onclick="turnFanOff()">Off</button>
            </div>
            <p id="fan-status">Last action: {last_action}</p>
        </div>
        <script>
        function updateFanSpeedLabel(val) {{
            document.getElementById('fan-speed-label').textContent = val + '%';
        }}
        function setFanSpeed() {{
            var speed = document.getElementById('fan-speed-slider').value;
            fetch('/emc2101/set_speed', {{
                method: 'POST',
                headers: {{'Content-Type':'application/json'}},
                body: JSON.stringify({{speed: parseInt(speed)}})
            }}).then(() => getFanStatus());
        }}
        function turnFanOn() {{
            fetch('/emc2101/turn_on', {{method:'POST'}}).then(() => getFanStatus());
        }}
        function turnFanOff() {{
            fetch('/emc2101/turn_off', {{method:'POST'}}).then(() => getFanStatus());
        }}
        function getFanStatus() {{
            fetch('/emc2101/status').then(r => r.json()).then(data => {{
                document.getElementById('fan-status').textContent = 'Last action: ' + data.last_action;
                document.getElementById('fan-speed-slider').value = data.speed;
                updateFanSpeedLabel(data.speed);
            }});
        }}
        getFanStatus();
        </script>
        """.format(version=self.VERSION, speed=self._fan_speed_percent, last_action=self._last_action)