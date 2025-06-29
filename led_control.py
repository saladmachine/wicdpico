"""
LED Control Module - Enhanced version with toggle and blinky modes
Adapted from picowide for modular foundation
"""
import digitalio
import board
import time
from module_base import PicowidModule
from adafruit_httpserver import Request, Response

class LEDControlModule(PicowidModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        
        # Initialize LED hardware
        self.led = digitalio.DigitalInOut(board.LED)
        self.led.direction = digitalio.Direction.OUTPUT
        
        # LED state management
        self.last_blink = time.monotonic()
        self.led_state = False
        self.blinky_enabled = False
        self.manual_mode = False  # Track if LED is manually controlled
        
        # Get blink interval from config
        self.blink_interval = foundation.config.BLINK_INTERVAL
        
    def register_routes(self, server):
        """Register LED control routes"""
        
        @server.route("/led-toggle", methods=['POST'])
        def led_toggle(request: Request):
            """Toggle LED on/off manually"""
            try:
                self.blinky_enabled = False  # Disable blinky when manually controlling
                self.manual_mode = True
                self.led_state = not self.led_state
                self.led.value = self.led_state
                
                status = "LED ON" if self.led_state else "LED OFF"
                self.foundation.startup_print(f"Manual LED: {status}")
                
                return Response(request, status, content_type="text/plain")
            except Exception as e:
                return Response(request, f"Error: {str(e)}", content_type="text/plain")
        
        @server.route("/led-blinky", methods=['POST'])
        def led_blinky(request: Request):
            """Toggle blinky mode"""
            try:
                self.manual_mode = False  # Exit manual mode
                self.blinky_enabled = not self.blinky_enabled
                
                if not self.blinky_enabled:
                    self.led.value = False  # Turn off when stopping blinky
                    
                status = "Blinky ON" if self.blinky_enabled else "Blinky OFF"
                next_action = "Stop Blinky" if self.blinky_enabled else "Start Blinky"
                
                self.foundation.startup_print(status)
                return Response(request, next_action, content_type="text/plain")
            except Exception as e:
                return Response(request, f"Error: {str(e)}", content_type="text/plain")
    
    def get_dashboard_html(self):
        """Return HTML for LED control interface"""
        return '''
        <div class="module">
            <h3>LED Control</h3>
            <div class="control-group">
                <button id="led-toggle-btn" onclick="toggleLED()">Toggle LED</button>
                <button id="led-blinky-btn" onclick="toggleBlinky()">Start Blinky</button>
            </div>
            <p id="led-status">LED Status: Ready</p>
        </div>
        
        <script>
        function toggleLED() {
            fetch('/led-toggle', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    document.getElementById('led-status').textContent = 'LED Status: ' + result;
                })
                .catch(error => {
                    document.getElementById('led-status').textContent = 'Error: ' + error.message;
                });
        }
        
        function toggleBlinky() {
            fetch('/led-blinky', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    document.getElementById('led-blinky-btn').textContent = result;
                    document.getElementById('led-status').textContent = 'Blinky mode updated';
                })
                .catch(error => {
                    document.getElementById('led-status').textContent = 'Error: ' + error.message;
                });
        }
        </script>
        '''
    
    def update(self):
        """Called from main loop - handle blinky timing"""
        if not self.blinky_enabled or self.manual_mode:
            return
            
        current_time = time.monotonic()
        
        if current_time - self.last_blink >= self.blink_interval:
            self.led_state = not self.led_state
            self.led.value = self.led_state
            self.last_blink = current_time