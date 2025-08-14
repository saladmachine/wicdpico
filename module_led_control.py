"""
LED Control Module - Visual Status and User Interaction
=======================================================

Provides comprehensive LED control functionality including manual toggle,
automatic blinky patterns, and system status indication. Integrates with
the wicdpico foundation for web-based control and visual feedback.

Hardware Requirements
--------------------
* Raspberry Pi Pico 2 W onboard LED (GPIO 25)
* No additional hardware required

Software Dependencies
--------------------
* digitalio (built-in CircuitPython)
* board (built-in CircuitPython)
* time (built-in CircuitPython)

Features
--------
* **Manual Control**: Direct LED on/off via web interface
* **Blinky Mode**: Configurable automatic blinking patterns
* **Status Indication**: Visual feedback for system states
* **Web Integration**: Browser-based control interface
* **Mode Management**: Seamless switching between manual and automatic modes

Configuration
------------
Blink interval configured via settings.toml:

.. code-block:: toml

    BLINK_INTERVAL = "0.5"  # Seconds between blinks

Usage Examples
-------------

.. code-block:: python

    # Basic LED control setup
    foundation = WicdpicoFoundation()
    led_module = LEDControlModule(foundation)
    foundation.register_module("led", led_module)
    
    # Manual control
    led_module.led_state = True   # Turn on
    led_module.led.value = True
    
    # Enable blinky mode
    led_module.blinky_enabled = True

Web Interface Features
---------------------
* Toggle LED button for manual on/off control
* Blinky mode button for automatic blinking
* Real-time status display
* Automatic mode switching prevention
"""
import digitalio
import board
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class LEDControlModule(WicdpicoModule):
    """
    LED Control Module for visual status indication and user interaction.
    
    Provides comprehensive LED control with manual toggle, automatic blinky
    patterns, and web-based interface. Manages LED state transitions and
    prevents conflicting control modes.
    
    :param foundation: WicdPico foundation instance for system integration
    :type foundation: WicdpicoFoundation
    
    **Basic Usage:**
    
    .. code-block:: python
    
        # Initialize LED control
        foundation = WicdpicoFoundation()
        led_module = LEDControlModule(foundation)
        foundation.register_module("led", led_module)
        
        # Manual LED control
        led_module.set_led(True)   # Turn on
        led_module.set_led(False)  # Turn off
        
        # Enable automatic blinking
        led_module.enable_blinky(True)
    
    **Web Interface Integration:**
    
    The module automatically provides web endpoints for browser-based control:
    
    * ``/led-toggle`` - Toggle LED on/off
    * ``/led-blinky`` - Enable/disable blinky mode
    
    **State Management:**
    
    The module manages three distinct states:
    
    * **Manual Mode**: Direct user control via toggle
    * **Blinky Mode**: Automatic blinking at configured interval  
    * **Idle**: LED off, ready for mode selection
    """
    
    def __init__(self, foundation):
        """
        Initialize LED control hardware and state management.
        
        Sets up GPIO control for onboard LED, initializes state variables,
        and configures blink timing from foundation configuration.
        
        :param foundation: Foundation instance for system integration
        :type foundation: WicdpicoFoundation
        """
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

    def set_led(self, state):
        """
        Set LED to specific state with mode management.
        
        Directly controls LED state while properly managing mode flags
        to prevent conflicts between manual and automatic control.
        
        :param state: Desired LED state
        :type state: bool
        """
        self.led_state = state
        self.led.value = state
        
    def enable_blinky(self, enabled):
        """
        Enable or disable automatic blinky mode.
        
        Controls automatic LED blinking functionality. When enabled,
        disables manual mode to prevent conflicts.
        
        :param enabled: True to enable blinky, False to disable
        :type enabled: bool
        """
        self.blinky_enabled = enabled
        if enabled:
            self.manual_mode = False
        else:
            self.set_led(False)  # Turn off when stopping blinky

    def register_routes(self, server):
        """
        Register LED control web endpoints.
        
        Adds HTTP routes for web-based LED control including manual
        toggle and blinky mode management.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        """

        @server.route("/led-toggle", methods=['POST'])
        def led_toggle(request: Request):
            """
            Toggle LED on/off manually via web interface.
            
            Switches LED state and disables blinky mode to prevent
            conflicts between manual and automatic control.
            
            :param request: HTTP request object
            :type request: Request
            :return: HTTP response with LED status
            :rtype: Response
            """
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
            """
            Toggle blinky mode via web interface.
            
            Enables or disables automatic LED blinking. Manages mode
            transitions and provides appropriate user feedback.
            
            :param request: HTTP request object
            :type request: Request
            :return: HTTP response with blinky status
            :rtype: Response
            """
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
        """
        Return HTML for LED control interface.
        
        Generates interactive web dashboard widget with LED control
        buttons and real-time status display.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
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
        """
        Called from main loop - handle blinky timing and state management.
        
        Manages automatic LED blinking when blinky mode is enabled.
        Called continuously by the foundation main loop for real-time
        LED state updates.
        
        **Blinky Logic:**
        
        * Only operates when blinky_enabled is True
        * Respects manual_mode to prevent conflicts
        * Uses configured blink_interval for timing
        * Toggles LED state at each interval
        """
        if not self.blinky_enabled or self.manual_mode:
            return

        current_time = time.monotonic()

        if current_time - self.last_blink >= self.blink_interval:
            self.led_state = not self.led_state
            self.led.value = self.led_state
            self.last_blink = current_time