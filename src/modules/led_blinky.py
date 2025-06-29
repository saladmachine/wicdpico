import board
import digitalio
from adafruit_httpserver import Request, Response
from ..foundation.module_base import PicowidModule

class LEDBlinkyModule(PicowidModule):
    """Simple LED control module for testing foundation"""
    
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "LED Blinky"
        
        # Initialize LED
        try:
            self.led = digitalio.DigitalInOut(board.LED)
            self.led.direction = digitalio.Direction.OUTPUT
            self.led.value = False
            self.led_state = False
            self.enabled = True
            foundation.startup_print("LED Blinky module initialized")
        except Exception as e:
            foundation.startup_print(f"LED Blinky init failed: {e}")
            self.enabled = False
    
    def register_routes(self, server):
        """Register web endpoints"""
        @server.route("/led_toggle", methods=['POST'])
        def handle_led_toggle(request: Request):
            if not self.enabled:
                return Response(request, "LED module not available", status=500)
            
            try:
                self.led_state = not self.led_state
                self.led.value = self.led_state
                state_text = "ON" if self.led_state else "OFF"
                return Response(request, f"LED is now {state_text}")
            except Exception as e:
                return Response(request, f"LED control error: {e}", status=500)
        
        @server.route("/led_status", methods=['GET'])
        def handle_led_status(request: Request):
            if not self.enabled:
                return Response(request, "disabled")
            state_text = "ON" if self.led_state else "OFF"
            return Response(request, state_text)
    
    def get_dashboard_html(self):
        """Return HTML for dashboard integration"""
        if not self.enabled:
            return '<div class="module-disabled">LED Blinky: Not Available</div>'
        
        return '''
        <div class="led-blinky-module">
            <h3>LED Control</h3>
            <button id="led-toggle-btn" onclick="toggleLED()">Toggle LED</button>
            <div id="led-status">LED Status: <span id="led-state">OFF</span></div>
        </div>
        
        <script>
        function toggleLED() {
            fetch('/led_toggle', { method: 'POST' })
            .then(response => response.text())
            .then(result => {
                document.getElementById('led-status').innerHTML = result;
                updateLEDState();
            })
            .catch(error => {
                document.getElementById('led-status').innerHTML = 'Error: ' + error.message;
            });
        }
        
        function updateLEDState() {
            fetch('/led_status')
            .then(response => response.text())
            .then(state => {
                document.getElementById('led-state').textContent = state;
            });
        }
        
        // Update status on page load
        updateLEDState();
        </script>
        '''
    
    def update(self):
        """Called from main loop - nothing needed for LED"""
        pass
    
    def cleanup(self):
        """Turn off LED on shutdown"""
        if self.enabled:
            try:
                self.led.value = False
            except:
                pass