# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`sht45_module`
====================================================

SHT45 Temperature and Humidity Sensor Module for PicoWicd system.

Provides comprehensive I2C access to all Adafruit SHT45 sensor parameters
including temperature, humidity, precision modes, heater control, reset
functionality, and advanced sensor features through web interface.

* Author(s): PicoWicd Development Team

Implementation Notes
--------------------

**Hardware:**

* Designed for use with Adafruit SHT45 Temperature & Humidity Sensor
* Uses I2C communication (GP4=SDA, GP5=SCL)
* Requires adafruit_sht4x library

**Software and Dependencies:**

* Adafruit CircuitPython firmware for Raspberry Pi Pico 2 W
* adafruit_sht4x library
* adafruit_httpserver
* PicoWicd foundation system

**Notes:**

* Supports all SHT45 measurement modes and heater settings
* Web interface provides real-time sensor monitoring and configuration
* Automatic error handling for missing or failed hardware
* Sensor reset functionality for recovery from stuck states

"""

# === CONFIGURATION PARAMETERS ===
SENSOR_READ_INTERVAL = 2.0      # seconds between automatic readings
TEMPERATURE_UNITS = "C"         # "C" for Celsius, "F" for Fahrenheit  
DEFAULT_PRECISION_MODE = "HIGH" # "HIGH", "MED", "LOW"
DEFAULT_HEATER_MODE = "NONE"    # "NONE", "LOW_100MS", "LOW_1S", "MED_100MS", "MED_1S", "HIGH_100MS", "HIGH_1S"
ENABLE_AUTO_UPDATES = True      # Enable automatic sensor readings in update loop
LOG_SENSOR_READINGS = False     # Log each sensor reading to foundation
# === END CONFIGURATION ===

import time
import board
import busio
from module_base import PicowicdModule
from adafruit_httpserver import Request, Response

# Try to import SHT4x library, create mock if not available
try:
    import adafruit_sht4x
    SHT4X_AVAILABLE = True
except ImportError:
    print("Warning: adafruit_sht4x library not found - using mock for testing")
    # Create mock classes for testing without hardware
    class MockMode:
        NOHEAT_HIGHPRECISION = 0
        NOHEAT_MEDPRECISION = 1  
        NOHEAT_LOWPRECISION = 2
        LOWHEAT_100MS = 3
        LOWHEAT_1S = 4
        MEDHEAT_100MS = 5
        MEDHEAT_1S = 6
        HIGHHEAT_100MS = 7
        HIGHHEAT_1S = 8
        
    class MockSHT4x:
        def __init__(self, i2c):
            self.mode = 0
            self.serial_number = 0x12345678
            
        @property
        def measurements(self):
            import random
            return (22.5 + random.random() * 5, 65.0 + random.random() * 10)
    
    # Create mock module
    class adafruit_sht4x:
        Mode = MockMode
        SHT4x = MockSHT4x
    
    SHT4X_AVAILABLE = False

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/picowicd/picowicd.git"


class SHT45Module(PicowicdModule):
    """
    SHT45 Temperature and Humidity Sensor Module for PicoWicd system.
    
    Provides comprehensive web interface and management for SHT45 sensor hardware.
    Supports all measurement modes, heater settings, reset functionality, and 
    advanced sensor features available through the Adafruit SHT4x library.
    
    :param foundation: PicoWicd foundation instance for system integration
    :type foundation: PicowicdFoundation
    """
    
    def __init__(self, foundation):
        """
        Initialize SHT45 Module.
        
        Sets up module identification and configuration, then initializes
        I2C communication and sensor hardware.
        
        :param foundation: PicoWicd foundation instance
        :type foundation: PicowicdFoundation
        """
        super().__init__(foundation)
        self.name = "SHT45 Sensor"
        
        # Configuration from module parameters
        self.read_interval = SENSOR_READ_INTERVAL
        self.temperature_units = TEMPERATURE_UNITS
        self.auto_updates_enabled = ENABLE_AUTO_UPDATES
        self.log_readings = LOG_SENSOR_READINGS
        
        # Sensor state tracking
        self.sensor_available = False
        self.last_reading_time = 0
        self.last_temperature = None
        self.last_humidity = None
        self.current_mode = DEFAULT_PRECISION_MODE
        self.current_heater = DEFAULT_HEATER_MODE
        
        # Status and error tracking
        self.status_message = "SHT45 module initialized"
        self.last_error = None
        
        # Initialize I2C and sensor hardware
        self._initialize_sensor()
        
        self.foundation.startup_print("SHT45 module created")
        self.foundation.startup_print(f"Read interval: {self.read_interval}s")
        self.foundation.startup_print(f"Temperature units: {self.temperature_units}")

    def _initialize_sensor(self):
        """
        Initialize I2C bus and SHT45 sensor hardware.
        
        Sets up I2C communication on GP4(SDA)/GP5(SCL) and attempts to
        connect to SHT45 sensor. Handles initialization errors gracefully.
        """
        try:
            # Set up I2C bus (GP4=SDA, GP5=SCL to match other modules)
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.foundation.startup_print("I2C bus initialized (GP5=SCL, GP4=SDA)")
            
            if not SHT4X_AVAILABLE:
                self.foundation.startup_print("Using mock SHT4x for testing (library not installed)")
            
            # Initialize SHT45 sensor (real or mock)
            self.sht45 = adafruit_sht4x.SHT4x(self.i2c)
            self.sensor_available = True
            
            # Get sensor serial number for identification
            try:
                self.sensor_serial = self.sht45.serial_number
                self.foundation.startup_print(f"SHT45 found! Serial: 0x{self.sensor_serial:08X}")
            except Exception as e:
                self.sensor_serial = None
                self.foundation.startup_print(f"SHT45 serial read failed: {e}")
            
            # Set default mode
            try:
                if DEFAULT_PRECISION_MODE == "HIGH":
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
                elif DEFAULT_PRECISION_MODE == "MED":
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_MEDPRECISION  
                else:  # LOW
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_LOWPRECISION
                
                self.foundation.startup_print(f"SHT45 mode set to: {DEFAULT_PRECISION_MODE} precision")
                self.status_message = f"SHT45 ready (Serial: 0x{self.sensor_serial:08X})" if self.sensor_serial else "SHT45 ready"
                
            except Exception as e:
                self.foundation.startup_print(f"SHT45 mode setting failed: {e}")
                self.status_message = "SHT45 connected but mode setting failed"
                
        except Exception as e:
            self.sensor_available = False
            self.sht45 = None
            self.i2c = None
            self.last_error = f"SHT45 initialization failed: {e}"
            self.status_message = self.last_error
            self.foundation.startup_print(self.last_error)

    def get_sensor_reading(self):
        """
        Get current temperature and humidity readings from SHT45 sensor.
        
        Reads sensor data and converts temperature units based on configuration.
        Handles sensor communication errors gracefully.
        
        :return: Dictionary containing sensor readings and metadata
        :rtype: dict
        """
        if not self.sensor_available or not self.sht45:
            return {
                "success": False,
                "error": "Sensor not available",
                "temperature": None,
                "humidity": None,
                "temperature_units": self.temperature_units,
                "timestamp": time.monotonic()
            }
        
        try:
            # Get measurements from sensor
            temperature_c, humidity = self.sht45.measurements
            
            # Convert temperature if needed
            if self.temperature_units == "F":
                temperature = (temperature_c * 9/5) + 32
            else:
                temperature = temperature_c
            
            # Update module state
            self.last_temperature = temperature
            self.last_humidity = humidity
            self.last_reading_time = time.monotonic()
            
            # Log reading if enabled
            if self.log_readings:
                self.foundation.startup_print(f"SHT45: {temperature:.1f}°{self.temperature_units}, {humidity:.1f}%RH")
            
            return {
                "success": True,
                "error": None,
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "temperature_units": self.temperature_units,
                "timestamp": self.last_reading_time
            }
            
        except Exception as e:
            error_msg = f"Reading failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SHT45 error: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "temperature": None,
                "humidity": None,
                "temperature_units": self.temperature_units,
                "timestamp": time.monotonic()
            }

    def set_measurement_mode(self, mode):
        """
        Set SHT45 measurement precision mode.
        
        Changes the sensor's measurement precision which affects accuracy
        and measurement time. Higher precision takes longer but provides
        more accurate readings.
        
        :param mode: Measurement mode ("HIGH", "MED", "LOW")
        :type mode: str
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.sht45:
            return False, "Sensor not available"
        
        try:
            # Map mode strings to adafruit_sht4x constants
            mode_map = {
                "HIGH": adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION,
                "MED": adafruit_sht4x.Mode.NOHEAT_MEDPRECISION,
                "LOW": adafruit_sht4x.Mode.NOHEAT_LOWPRECISION
            }
            
            if mode not in mode_map:
                return False, f"Invalid mode: {mode}. Use HIGH, MED, or LOW"
            
            # Set the new mode
            self.sht45.mode = mode_map[mode]
            self.current_mode = mode
            
            self.foundation.startup_print(f"SHT45 mode changed to: {mode}")
            self.status_message = f"Mode: {mode} precision"
            
            return True, f"Mode set to {mode} precision"
            
        except Exception as e:
            error_msg = f"Mode change failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SHT45 mode error: {error_msg}")
            return False, error_msg

    def set_heater_mode(self, heater_mode):
        """
        Set SHT45 heater mode for condensation removal and decontamination.
        
        The built-in heater can reach 60°C to remove condensation, burn off
        contaminants, and maintain accuracy in high humidity environments.
        
        :param heater_mode: Heater setting
        :type heater_mode: str
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.sht45:
            return False, "Sensor not available"
        
        try:
            # Map heater strings to adafruit_sht4x constants
            heater_map = {
                "NONE": adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION,  # Use current precision with no heat
                "LOW_100MS": adafruit_sht4x.Mode.LOWHEAT_100MS,
                "LOW_1S": adafruit_sht4x.Mode.LOWHEAT_1S,
                "MED_100MS": adafruit_sht4x.Mode.MEDHEAT_100MS,
                "MED_1S": adafruit_sht4x.Mode.MEDHEAT_1S,
                "HIGH_100MS": adafruit_sht4x.Mode.HIGHHEAT_100MS,
                "HIGH_1S": adafruit_sht4x.Mode.HIGHHEAT_1S
            }
            
            if heater_mode not in heater_map:
                valid_modes = ", ".join(heater_map.keys())
                return False, f"Invalid heater mode: {heater_mode}. Use: {valid_modes}"
            
            # Set the new heater mode
            self.sht45.mode = heater_map[heater_mode]
            self.current_heater = heater_mode
            
            # Update precision tracking if switching to no heat
            if heater_mode == "NONE":
                # Maintain current precision level
                if self.current_mode == "HIGH":
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
                elif self.current_mode == "MED":
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_MEDPRECISION
                else:  # LOW
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_LOWPRECISION
            
            heater_description = {
                "NONE": "disabled",
                "LOW_100MS": "low heat for 100ms",
                "LOW_1S": "low heat for 1 second", 
                "MED_100MS": "medium heat for 100ms",
                "MED_1S": "medium heat for 1 second",
                "HIGH_100MS": "high heat for 100ms",
                "HIGH_1S": "high heat for 1 second"
            }
            
            desc = heater_description.get(heater_mode, heater_mode)
            self.foundation.startup_print(f"SHT45 heater set to: {desc}")
            self.status_message = f"Heater: {desc}"
            
            return True, f"Heater set to {desc}"
            
        except Exception as e:
            error_msg = f"Heater change failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SHT45 heater error: {error_msg}")
            return False, error_msg

    def reset_sensor(self):
        """
        Perform soft reset of SHT45 sensor.
        
        Sends reset command to clear any stuck states or errors.
        Useful for recovering from communication failures or unusual readings.
        
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.sht45:
            return False, "Sensor not available"
        
        try:
            # The SHT4x library doesn't expose reset directly, but we can simulate
            # by reinitializing the sensor connection
            self.foundation.startup_print("SHT45: Performing sensor reset...")
            
            # Clear any cached state
            self.last_temperature = None
            self.last_humidity = None
            self.last_reading_time = 0
            self.last_error = None
            
            # Reinitialize the sensor to clear any stuck states
            old_sensor = self.sht45
            self.sht45 = adafruit_sht4x.SHT4x(self.i2c)
            
            # Verify sensor is responding after reset
            test_serial = self.sht45.serial_number
            if test_serial != self.sensor_serial:
                self.foundation.startup_print(f"Warning: Serial changed after reset: 0x{test_serial:08X}")
            
            # Restore previous mode settings
            if self.current_mode == "HIGH":
                self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
            elif self.current_mode == "MED":
                self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_MEDPRECISION
            else:  # LOW
                self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_LOWPRECISION
            
            # Reset heater mode to none
            self.current_heater = "NONE"
            
            self.foundation.startup_print("SHT45: Reset completed successfully")
            self.status_message = "Sensor reset completed"
            
            return True, "Sensor reset completed successfully"
            
        except Exception as e:
            error_msg = f"Reset failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SHT45 reset error: {error_msg}")
            return False, error_msg

    def get_sensor_info(self):
        """
        Get comprehensive sensor information and status.
        
        Retrieves sensor identification, current settings, and operational status.
        Useful for diagnostics and system monitoring.
        
        :return: Dictionary containing complete sensor information
        :rtype: dict
        """
        return {
            "available": self.sensor_available,
            "serial_number": self.sensor_serial,
            "serial_hex": f"0x{self.sensor_serial:08X}" if self.sensor_serial else "N/A",
            "current_mode": self.current_mode,
            "current_heater": self.current_heater,
            "last_reading_time": self.last_reading_time,
            "last_temperature": self.last_temperature,
            "last_humidity": self.last_humidity,
            "temperature_units": self.temperature_units,
            "status_message": self.status_message,
            "last_error": self.last_error,
            "library_available": SHT4X_AVAILABLE
        }

    def register_routes(self, server):
        """
        Register HTTP routes for SHT45 web interface.
        
        Provides REST endpoints for sensor readings and control.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        """
        
        @server.route("/sht45-reading", methods=['POST'])
        def sht45_reading(request: Request):
            """Handle sensor reading requests."""
            try:
                reading = self.get_sensor_reading()
                
                if reading['success']:
                    response_text = f"Temperature: {reading['temperature']}°{reading['temperature_units']}<br>"
                    response_text += f"Humidity: {reading['humidity']}%<br>"
                    response_text += f"Reading time: {reading['timestamp']:.1f}s"
                    
                    self.status_message = f"Last: {reading['temperature']}°{reading['temperature_units']}, {reading['humidity']}%"
                    
                else:
                    response_text = f"Reading failed: {reading['error']}"
                    self.status_message = f"Error: {reading['error']}"
                
                return Response(request, response_text, content_type="text/html")
                
            except Exception as e:
                error_msg = f"Route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/sht45-mode", methods=['POST'])
        def sht45_mode(request: Request):
            """Handle measurement mode change requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                mode = None
                if "mode=HIGH" in body:
                    mode = "HIGH"
                elif "mode=MED" in body:
                    mode = "MED"  
                elif "mode=LOW" in body:
                    mode = "LOW"
                
                if not mode:
                    return Response(request, "No valid mode specified", content_type="text/plain")
                
                success, message = self.set_measurement_mode(mode)
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Mode route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/sht45-heater", methods=['POST'])
        def sht45_heater(request: Request):
            """Handle heater control requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                heater_mode = None
                heater_options = ["NONE", "LOW_100MS", "LOW_1S", "MED_100MS", "MED_1S", "HIGH_100MS", "HIGH_1S"]
                
                for option in heater_options:
                    if f"heater={option}" in body:
                        heater_mode = option
                        break
                
                if not heater_mode:
                    return Response(request, "No valid heater mode specified", content_type="text/plain")
                
                success, message = self.set_heater_mode(heater_mode)
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Heater route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/sht45-info", methods=['POST'])
        def sht45_info(request: Request):
            """Handle sensor information requests."""
            try:
                info = self.get_sensor_info()
                
                response_html = f"""
                <strong>Sensor Information:</strong><br>
                • Serial: {info['serial_hex']}<br>
                • Mode: {info['current_mode']} precision<br>
                • Heater: {info['current_heater']}<br>
                • Library: {'Real SHT4x' if info['library_available'] else 'Mock/Testing'}<br>
                • Status: {'Available' if info['available'] else 'Unavailable'}
                """
                
                if info['last_temperature'] is not None:
                    response_html += f"<br>• Last: {info['last_temperature']:.1f}°{info['temperature_units']}, {info['last_humidity']:.1f}%RH"
                
                if info['last_error']:
                    response_html += f"<br>• Error: {info['last_error']}"
                
                return Response(request, response_html, content_type="text/html")
                
            except Exception as e:
                error_msg = f"Info route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/sht45-reset", methods=['POST'])
        def sht45_reset(request: Request):
            """Handle sensor reset requests."""
            try:
                success, message = self.reset_sensor()
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Reset route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")
        
        self.foundation.startup_print("SHT45 reading, mode, info, heater, and reset routes registered")

    def get_dashboard_html(self):
        """
        Generate HTML dashboard widget for SHT45 control.
        
        Creates interactive web interface with sensor readings display
        and control buttons including heater control and reset functionality.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
        # Complete dashboard with heater control and reset
        sensor_info_line = f"Serial: 0x{self.sensor_serial:08X}" if self.sensor_serial else "No serial available"
        if not SHT4X_AVAILABLE:
            sensor_info_line += " (Mock)"
        
        # Status indicators with colors
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        error_display = f"<br><span style='color: #dc3545;'><strong>Error:</strong> {self.last_error}</span>" if self.last_error else ""
        
        # Show last reading with timestamp if available
        last_reading = ""
        if self.last_temperature is not None and self.last_humidity is not None:
            reading_time = time.monotonic() - self.last_reading_time if self.last_reading_time > 0 else 0
            last_reading = f"<br><strong>Last Reading:</strong> {self.last_temperature:.1f}°{self.temperature_units}, {self.last_humidity:.1f}%RH ({reading_time:.0f}s ago)"
        
        return f'''
        <div class="module">
            <h3>SHT45 Temperature & Humidity Sensor</h3>
            <div class="status" style="border-left: 4px solid {status_color};">
                <strong>Status:</strong> <span style="color: {status_color};">{self.status_message}</span><br>
                <strong>Sensor:</strong> {sensor_info_line}<br>
                <strong>Mode:</strong> <span id="current-mode">{self.current_mode}</span> precision<br>
                <strong>Heater:</strong> <span id="current-heater">{self.current_heater}</span>{last_reading}{error_display}
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Sensor Control</h4>
                <button id="sht45-reading-btn" onclick="getSHT45Reading()" style="background: #007bff;">Get Reading</button>
                <button id="sht45-info-btn" onclick="getSHT45Info()" style="background: #17a2b8;">Sensor Info</button>
                <button id="sht45-reset-btn" onclick="resetSHT45()" style="background: #dc3545;">Reset Sensor</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Precision Mode</h4>
                <button id="mode-high-btn" onclick="setSHT45Mode('HIGH')" style="background: #28a745;">High Precision</button>
                <button id="mode-med-btn" onclick="setSHT45Mode('MED')" style="background: #ffc107; color: #212529;">Med Precision</button>
                <button id="mode-low-btn" onclick="setSHT45Mode('LOW')" style="background: #fd7e14;">Low Precision</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Heater Control (60°C)</h4>
                <button id="heater-none-btn" onclick="setSHT45Heater('NONE')" style="background: #6c757d;">No Heat</button>
                <button id="heater-low-btn" onclick="setSHT45Heater('LOW_1S')" style="background: #20c997;">Low 1s</button>
                <button id="heater-med-btn" onclick="setSHT45Heater('MED_1S')" style="background: #fd7e14;">Med 1s</button>
                <button id="heater-high-btn" onclick="setSHT45Heater('HIGH_1S')" style="background: #dc3545;">High 1s</button>
            </div>
            
            <div id="sht45-status" class="status" style="margin-top: 10px; background: #e7f3ff; border-left: 4px solid #007bff;">
                <strong>Ready:</strong> SHT45 Module - Step 8 reset functionality complete!
            </div>
        </div>

        <script>
        function getSHT45Reading() {{
            const btn = document.getElementById('sht45-reading-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/sht45-reading', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('sht45-status').innerHTML = '<strong>Latest Reading:</strong><br>' + result;
                    document.getElementById('sht45-status').style.background = '#d4edda';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #28a745';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('sht45-status').innerHTML = '<strong>Reading Error:</strong><br>' + error.message;
                    document.getElementById('sht45-status').style.background = '#f8d7da';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function getSHT45Info() {{
            const btn = document.getElementById('sht45-info-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Getting...';

            fetch('/sht45-info', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('sht45-status').innerHTML = result;
                    document.getElementById('sht45-status').style.background = '#e2e3e5';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #6c757d';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('sht45-status').innerHTML = '<strong>Info Error:</strong><br>' + error.message;
                    document.getElementById('sht45-status').style.background = '#f8d7da';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSHT45Mode(mode) {{
            const buttons = ['mode-high-btn', 'mode-med-btn', 'mode-low-btn'];
            const originalTexts = {{}};
            
            buttons.forEach(id => {{
                const btn = document.getElementById(id);
                originalTexts[id] = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Setting...';
            }});

            fetch('/sht45-mode', {{ 
                method: 'POST',
                body: 'mode=' + mode
            }})
                .then(response => response.text())
                .then(result => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('sht45-status').innerHTML = '<strong>Mode Changed:</strong><br>' + result;
                    document.getElementById('sht45-status').style.background = '#d1ecf1';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #17a2b8';
                    document.getElementById('current-mode').textContent = mode;
                }})
                .catch(error => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('sht45-status').innerHTML = '<strong>Mode Error:</strong><br>' + error.message;
                    document.getElementById('sht45-status').style.background = '#f8d7da';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSHT45Heater(heaterMode) {{
            const buttons = ['heater-none-btn', 'heater-low-btn', 'heater-med-btn', 'heater-high-btn'];
            const originalTexts = {{}};
            
            buttons.forEach(id => {{
                const btn = document.getElementById(id);
                originalTexts[id] = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Setting...';
            }});

            fetch('/sht45-heater', {{ 
                method: 'POST',
                body: 'heater=' + heaterMode
            }})
                .then(response => response.text())
                .then(result => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('sht45-status').innerHTML = '<strong>Heater Changed:</strong><br>' + result;
                    document.getElementById('sht45-status').style.background = '#fff3cd';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #ffc107';
                    document.getElementById('current-heater').textContent = heaterMode;
                }})
                .catch(error => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('sht45-status').innerHTML = '<strong>Heater Error:</strong><br>' + error.message;
                    document.getElementById('sht45-status').style.background = '#f8d7da';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function resetSHT45() {{
            if (!confirm('Reset SHT45 sensor? This will clear current readings and restore default settings.')) {{
                return;
            }}
            
            const btn = document.getElementById('sht45-reset-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Resetting...';

            fetch('/sht45-reset', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('sht45-status').innerHTML = '<strong>Reset Complete:</strong><br>' + result;
                    document.getElementById('sht45-status').style.background = '#fff3cd';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #ffc107';
                    
                    document.getElementById('current-mode').textContent = 'HIGH';
                    document.getElementById('current-heater').textContent = 'NONE';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('sht45-status').innerHTML = '<strong>Reset Error:</strong><br>' + error.message;
                    document.getElementById('sht45-status').style.background = '#f8d7da';
                    document.getElementById('sht45-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        </script>
        '''

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Will handle automatic sensor readings and status updates.
        Implementation will be added in subsequent steps.
        """
        pass

    def cleanup(self):
        """
        Cleanup method called during system shutdown.
        
        Performs any necessary cleanup operations before module shutdown.
        Currently no cleanup is required but method is provided for completeness.
        """
        if self.sensor_available:
            self.foundation.startup_print("SHT45 cleanup: Sensor shutdown")
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