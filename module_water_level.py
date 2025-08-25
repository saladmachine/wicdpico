# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`water_level_module`
====================================================

EPT Technology FS-IR02B Water Level Sensor Module for WicdPico system.

Provides comprehensive digital input access to FS-IR02B optical water level sensor
including water detection, level monitoring, refill event logging, and advanced
sensor features through web interface.

* Author(s): WicdPico Development Team

Implementation Notes
--------------------

**Hardware:**

* Designed for use with EPT Technology FS-IR02B Water Level Sensor
* Uses digital input communication (configurable GPIO pin)
* 3-wire connection: VCC, GND, Signal

**Software and Dependencies:**

* Adafruit CircuitPython firmware for Raspberry Pi Pico 2 W
* digitalio library (built-in CircuitPython)
* adafruit_httpserver
* WicdPico foundation system

**Notes:**

* Supports water presence detection (HIGH when water present, LOW when absent)
* Web interface provides real-time monitoring and event logging
* Automatic error handling for missing or failed hardware
* Refill event detection and timestamping
* Configurable sensitivity and polling intervals

"""

# === CONFIGURATION PARAMETERS ===
SENSOR_READ_INTERVAL = 1.0       # seconds between automatic readings
DEFAULT_GPIO_PIN = "GP6"         # Default GPIO pin for sensor signal
REFILL_DEBOUNCE_TIME = 2.0       # seconds to wait before logging new refill event
ENABLE_AUTO_UPDATES = True       # Enable automatic sensor readings in update loop
LOG_SENSOR_READINGS = False      # Log each sensor reading to foundation
LOG_REFILL_EVENTS = True         # Log water refill events
INVERT_SIGNAL = True             # Set True if sensor logic is inverted
# === END CONFIGURATION ===

import time
import board
import digitalio
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/wicdpico/wicdpico.git"


class WaterLevelModule(WicdpicoModule):
    """
    EPT Technology FS-IR02B Water Level Sensor Module for WicdPico system.
    
    Provides comprehensive web interface and management for FS-IR02B sensor hardware.
    Supports water level detection, refill event logging, and monitoring features
    available through the optical water level sensor.
    
    :param foundation: WicdPico foundation instance for system integration
    :type foundation: WicdpicoFoundation
    """
    
    def __init__(self, foundation, gpio_pin=None):
        """
        Initialize Water Level Module.
        
        Sets up module identification and configuration, then initializes
        digital input communication and sensor hardware.
        
        :param foundation: WicdPico foundation instance
        :type foundation: WicdpicoFoundation
        :param gpio_pin: GPIO pin name for sensor signal (e.g., "GP6")
        :type gpio_pin: str
        """
        super().__init__(foundation)
        self.name = "FS-IR02B Water Level Sensor"
        
        # Configuration from module parameters
        self.read_interval = SENSOR_READ_INTERVAL
        self.gpio_pin_name = gpio_pin or DEFAULT_GPIO_PIN
        self.auto_updates_enabled = ENABLE_AUTO_UPDATES
        self.log_readings = LOG_SENSOR_READINGS
        self.log_refill_events = LOG_REFILL_EVENTS
        self.refill_debounce_time = REFILL_DEBOUNCE_TIME
        self.invert_signal = INVERT_SIGNAL
        
        # Sensor state tracking
        self.sensor_available = False
        self.last_reading_time = 0
        self.last_water_present = None
        self.current_water_present = False
        self.refill_count = 0
        self.last_refill_time = 0
        self.refill_events = []  # List of timestamped refill events
        
        # Status and error tracking
        self.status_message = "Water level module initialized"
        self.last_error = None
        
        # Initialize GPIO and sensor hardware
        self._initialize_sensor()
        
        self.foundation.startup_print("Water level module created")
        self.foundation.startup_print(f"GPIO pin: {self.gpio_pin_name}")
        self.foundation.startup_print(f"Read interval: {self.read_interval}s")

    def _initialize_sensor(self):
        """
        Initialize GPIO pin and FS-IR02B sensor hardware.
        
        Sets up digital input on specified GPIO pin and attempts to
        connect to water level sensor. Handles initialization errors gracefully.
        """
        try:
            # Convert pin name to board pin object
            pin_obj = getattr(board, self.gpio_pin_name)
            
            # Set up digital input pin
            self.sensor_pin = digitalio.DigitalInOut(pin_obj)
            self.sensor_pin.direction = digitalio.Direction.INPUT
            self.sensor_pin.pull = digitalio.Pull.DOWN  # Pull down for stable reading
            
            self.foundation.startup_print(f"GPIO {self.gpio_pin_name} initialized as digital input")
            
            # Test initial reading
            try:
                test_reading = self.sensor_pin.value
                if self.invert_signal:
                    test_reading = not test_reading
                
                self.foundation.startup_print(f"FS-IR02B test reading: {'Water Present' if test_reading else 'No Water'}")
                self.current_water_present = test_reading
                self.last_water_present = test_reading
                
            except Exception as e:
                self.foundation.startup_print(f"Warning: Initial sensor reading failed: {e}")
            
            self.sensor_available = True
            self.foundation.startup_print(f"FS-IR02B initialized on pin {self.gpio_pin_name}")
            self.status_message = f"FS-IR02B ready on {self.gpio_pin_name}"
            
        except Exception as e:
            self.sensor_available = False
            self.sensor_pin = None
            self.last_error = f"FS-IR02B initialization failed: {e}"
            self.status_message = self.last_error
            self.foundation.startup_print(self.last_error)

    def get_sensor_reading(self):
        """
        Get current water level reading from FS-IR02B sensor.
        
        Reads sensor data and detects refill events based on state changes.
        Handles sensor communication errors gracefully.
        
        :return: Dictionary containing sensor readings and metadata
        :rtype: dict
        """
        if not self.sensor_available:
            return {
                "success": False,
                "error": "Sensor not available",
                "water_present": None,
                "refill_detected": False,
                "refill_count": self.refill_count,
                "timestamp": time.monotonic()
            }
        
        try:
            # Read digital input
            raw_reading = self.sensor_pin.value
            
            # Apply signal inversion if configured
            water_present = not raw_reading if self.invert_signal else raw_reading
            
            # Detect refill events (transition from no water to water)
            refill_detected = False
            current_time = time.monotonic()
            
            if (self.last_water_present is not None and 
                not self.last_water_present and water_present and
                (current_time - self.last_refill_time) > self.refill_debounce_time):
                
                # Refill event detected
                refill_detected = True
                self.refill_count += 1
                self.last_refill_time = current_time
                
                # Add to refill events log (keep last 50 events)
                refill_event = {
                    "timestamp": current_time,
                    "count": self.refill_count,
                    "time_str": f"{current_time:.1f}s"
                }
                self.refill_events.append(refill_event)
                if len(self.refill_events) > 50:
                    self.refill_events.pop(0)
                
                if self.log_refill_events:
                    self.foundation.startup_print(f"Water refill detected! Count: {self.refill_count}")
            
            # Update module state
            self.last_water_present = self.current_water_present
            self.current_water_present = water_present
            self.last_reading_time = current_time
            
            # Log reading if enabled
            if self.log_readings:
                self.foundation.startup_print(f"FS-IR02B: {'Water Present' if water_present else 'No Water'}")
            
            return {
                "success": True,
                "error": None,
                "water_present": water_present,
                "refill_detected": refill_detected,
                "refill_count": self.refill_count,
                "timestamp": self.last_reading_time
            }
            
        except Exception as e:
            error_msg = f"Reading failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"FS-IR02B error: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "water_present": None,
                "refill_detected": False,
                "refill_count": self.refill_count,
                "timestamp": time.monotonic()
            }

    def reset_refill_counter(self):
        """
        Reset the refill event counter and clear event log.
        
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        try:
            self.refill_count = 0
            self.refill_events = []
            self.last_refill_time = 0
            
            self.foundation.startup_print("FS-IR02B: Refill counter reset")
            self.status_message = "Refill counter reset"
            
            return True, "Refill counter reset successfully"
            
        except Exception as e:
            error_msg = f"Reset failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"FS-IR02B reset error: {error_msg}")
            return False, error_msg

    def get_refill_events(self, limit=10):
        """
        Get recent refill events.
        
        :param limit: Maximum number of recent events to return
        :type limit: int
        :return: List of recent refill events
        :rtype: list
        """
        return self.refill_events[-limit:] if limit > 0 else self.refill_events

    def get_sensor_info(self):
        """
        Get comprehensive sensor information and status.
        
        :return: Dictionary containing complete sensor information
        :rtype: dict
        """
        return {
            "available": self.sensor_available,
            "gpio_pin": self.gpio_pin_name,
            "last_reading_time": self.last_reading_time,
            "current_water_present": self.current_water_present,
            "refill_count": self.refill_count,
            "last_refill_time": self.last_refill_time,
            "refill_debounce_time": self.refill_debounce_time,
            "invert_signal": self.invert_signal,
            "status_message": self.status_message,
            "last_error": self.last_error,
            "total_refill_events": len(self.refill_events)
        }

    def register_routes(self, server):
        """
        Register HTTP routes for water level sensor web interface.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        """
        
        @server.route("/water-level-reading", methods=['POST'])
        def water_level_reading(request: Request):
            """Handle sensor reading requests."""
            try:
                reading = self.get_sensor_reading()
                
                if reading['success']:
                    water_status = "Water Present" if reading['water_present'] else "No Water"
                    response_text = f"Water Status: {water_status}<br>"
                    response_text += f"Refill Count: {reading['refill_count']}<br>"
                    response_text += f"Reading time: {reading['timestamp']:.1f}s"
                    
                    if reading['refill_detected']:
                        response_text += "<br><strong>🌊 REFILL DETECTED!</strong>"
                    
                    self.status_message = f"Status: {water_status}"
                    
                else:
                    response_text = f"Reading failed: {reading['error']}"
                    self.status_message = f"Error: {reading['error']}"
                
                return Response(request, response_text, content_type="text/html")
                
            except Exception as e:
                error_msg = f"Route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/water-level-reset", methods=['POST'])
        def water_level_reset(request: Request):
            """Handle refill counter reset requests."""
            try:
                success, message = self.reset_refill_counter()
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Reset route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/water-level-info", methods=['POST'])
        def water_level_info(request: Request):
            """Handle sensor information requests."""
            try:
                info = self.get_sensor_info()
                
                response_html = f"""
                <strong>Sensor Information:</strong><br>
                • GPIO Pin: {info['gpio_pin']}<br>
                • Water Present: {'Yes' if info['current_water_present'] else 'No'}<br>
                • Refill Count: {info['refill_count']}<br>
                • Signal Inverted: {'Yes' if info['invert_signal'] else 'No'}<br>
                • Status: {'Available' if info['available'] else 'Unavailable'}
                """
                
                if info['last_refill_time'] > 0:
                    time_since_refill = time.monotonic() - info['last_refill_time']
                    response_html += f"<br>• Last Refill: {time_since_refill:.0f}s ago"
                
                if info['last_error']:
                    response_html += f"<br>• Error: {info['last_error']}"
                
                return Response(request, response_html, content_type="text/html")
                
            except Exception as e:
                error_msg = f"Info route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/water-level-events", methods=['POST'])
        def water_level_events(request: Request):
            """Handle refill events display requests."""
            try:
                events = self.get_refill_events(limit=10)
                
                if events:
                    response_html = "<strong>Recent Refill Events:</strong><br>"
                    for event in reversed(events):  # Show most recent first
                        response_html += f"• Refill #{event['count']} at {event['time_str']}<br>"
                else:
                    response_html = "No refill events recorded"
                
                return Response(request, response_html, content_type="text/html")
                
            except Exception as e:
                error_msg = f"Events route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")
        
        self.foundation.startup_print("Water level reading, reset, info, and events routes registered")

    def get_dashboard_html(self):
        """
        Generate HTML dashboard widget for water level sensor control.
        
        Creates interactive web interface with sensor readings display
        and control buttons for all water level sensor features.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
        # Sensor information display
        sensor_info_line = f"GPIO: {self.gpio_pin_name}"
        if self.invert_signal:
            sensor_info_line += " (Inverted)"
        
        # Status indicators with colors
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        water_color = "#007bff" if self.current_water_present else "#6c757d"
        error_display = f"<br><span style='color: #dc3545;'><strong>Error:</strong> {self.last_error}</span>" if self.last_error else ""
        
        # Show last reading with timestamp if available
        last_reading = ""
        if self.last_reading_time > 0:
            reading_time = time.monotonic() - self.last_reading_time if self.last_reading_time > 0 else 0
            water_status = "Water Present" if self.current_water_present else "No Water"
            last_reading = f"<br><strong>Last Reading:</strong> {water_status} ({reading_time:.0f}s ago)"
        
        return f'''
        <div class="module">
            <h3>FS-IR02B Water Level Sensor</h3>
            <div class="status" style="border-left: 4px solid {status_color};">
                <strong>Status:</strong> <span style="color: {status_color};">{self.status_message}</span><br>
                <strong>Sensor:</strong> {sensor_info_line}<br>
                <strong>Water Present:</strong> <span id="current-water-status" style="color: {water_color};">{'Yes' if self.current_water_present else 'No'}</span><br>
                <strong>Refill Count:</strong> <span id="current-refill-count">{self.refill_count}</span>{last_reading}{error_display}
            </div>
            
            <div id="water-level-status" class="status" style="margin-top: 10px; background: #e7f3ff; border-left: 4px solid #007bff;">
                <strong>Ready:</strong> FS-IR02B Water Level Sensor Module initialized!
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Sensor Control</h4>
                <button id="water-level-reading-btn" onclick="getWaterLevelReading()" style="background: #007bff;">Get Reading</button>
                <button id="water-level-info-btn" onclick="getWaterLevelInfo()" style="background: #17a2b8;">Sensor Info</button>
                <button id="water-level-events-btn" onclick="getWaterLevelEvents()" style="background: #28a745;">View Events</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Refill Management</h4>
                <button id="reset-refill-btn" onclick="resetRefillCounter()" style="background: #dc3545;">Reset Counter</button>
            </div>
        </div>

        <script>
        function getWaterLevelReading() {{
            const btn = document.getElementById('water-level-reading-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/water-level-reading', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = '<strong>Latest Reading:</strong><br>' + result;
                    document.getElementById('water-level-status').style.background = '#d4edda';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #28a745';
                    
                    // Update display values if reading successful
                    if (result.includes('Water Present')) {{
                        document.getElementById('current-water-status').textContent = 'Yes';
                        document.getElementById('current-water-status').style.color = '#007bff';
                    }} else if (result.includes('No Water')) {{
                        document.getElementById('current-water-status').textContent = 'No';
                        document.getElementById('current-water-status').style.color = '#6c757d';
                    }}
                    
                    // Update refill count if present in response
                    const refillMatch = result.match(/Refill Count: (\\d+)/);
                    if (refillMatch) {{
                        document.getElementById('current-refill-count').textContent = refillMatch[1];
                    }}
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = '<strong>Reading Error:</strong><br>' + error.message;
                    document.getElementById('water-level-status').style.background = '#f8d7da';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function getWaterLevelInfo() {{
            const btn = document.getElementById('water-level-info-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Getting...';

            fetch('/water-level-info', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = result;
                    document.getElementById('water-level-status').style.background = '#e2e3e5';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #6c757d';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = '<strong>Info Error:</strong><br>' + error.message;
                    document.getElementById('water-level-status').style.background = '#f8d7da';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function getWaterLevelEvents() {{
            const btn = document.getElementById('water-level-events-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Loading...';

            fetch('/water-level-events', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = result;
                    document.getElementById('water-level-status').style.background = '#d1ecf1';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #17a2b8';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = '<strong>Events Error:</strong><br>' + error.message;
                    document.getElementById('water-level-status').style.background = '#f8d7da';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function resetRefillCounter() {{
            if (!confirm('Reset refill counter? This will clear all refill event history.')) {{
                return;
            }}
            
            const btn = document.getElementById('reset-refill-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Resetting...';

            fetch('/water-level-reset', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = '<strong>Reset Complete:</strong><br>' + result;
                    document.getElementById('water-level-status').style.background = '#fff3cd';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #ffc107';
                    
                    // Reset display counter
                    document.getElementById('current-refill-count').textContent = '0';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('water-level-status').innerHTML = '<strong>Reset Error:</strong><br>' + error.message;
                    document.getElementById('water-level-status').style.background = '#f8d7da';
                    document.getElementById('water-level-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        </script>
        '''

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Handles automatic sensor readings if enabled.
        """
        if self.auto_updates_enabled and self.sensor_available:
            current_time = time.monotonic()
            if current_time - self.last_reading_time >= self.read_interval:
                self.get_sensor_reading()

    def cleanup(self):
        """
        Cleanup method called during system shutdown.
        """
        if self.sensor_available and self.sensor_pin:
            try:
                self.sensor_pin.deinit()
                self.foundation.startup_print("Water level cleanup: GPIO pin released")
            except:
                pass

    @property
    def sensor_info(self):
        """
        Get sensor information and status (legacy property).
        
        :return: Dictionary containing sensor status information
        :rtype: dict
        
        .. deprecated::
           Use get_sensor_info() method instead for complete information.
        """
        return self.get_sensor_info()