import json
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class BH1750Module(WicdpicoModule):
    """
    Ambient Light Sensor Module (BH1750)
    Provides light sensing and dashboard integration.
    """

    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Ambient Light"
        self.version = "v1.0"
        self.lux = None
        self.available = False

        try:
            import board
            import busio
            import adafruit_bh1750
            self.i2c = foundation.i2c
            self.sensor = adafruit_bh1750.BH1750(self.i2c)
            self.available = True
            foundation.startup_print("BH1750 sensor initialized.")
        except Exception as e:
            self.available = False
            foundation.startup_print(f"BH1750 unavailable: {e}")

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
            ("/light", self.handle_light_request)
        ]

    def register_routes(self, server):
        for route, handler in self.get_routes():
            server.route(route, methods=["GET", "POST"])(handler)

    def handle_light_request(self, request: Request):
        reading = self.get_light()
        return Response(request, json.dumps(reading), content_type="application/json")

    def get_dashboard_html(self):
        # FIX: matches battery monitor and RTC—no width/max-width/margin on outer div
        return """
        <div class="module">
            <h2>Ambient Light (BH1750)</h2>
            <div class="control-group">
                <button id="light-btn" onclick="getLux()">Read Light Level</button>
            </div>
            <div style="margin-top: 10px;">
                <div><strong>Lux:</strong> <span id="lux-value">--</span></div>
            </div>
            <div id="light-error-display" style="color: red;"></div>
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
        </script>
        """