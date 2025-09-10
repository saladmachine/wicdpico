# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`scd41_module`
====================================================

SCD41 CO2, Temperature, and Humidity Sensor Module for WicdPico system.

Provides comprehensive I2C access to all SCD41 sensor parameters
including CO2 measurement, temperature, humidity, calibration,
automatic baseline correction, altitude compensation, and advanced
sensor features through web interface.

* Author(s): WicdPico Development Team

Implementation Notes
--------------------

**Hardware:**

* Designed for use with SCD41 CO2, Temperature & Humidity Sensor
* Uses I2C communication (GP4=SDA, GP5=SCL)
* Requires adafruit_scd4x library

**Software and Dependencies:**

* Adafruit CircuitPython firmware for Raspberry Pi Pico 2 W
* adafruit_scd4x library
* adafruit_httpserver
* WicdPico foundation system

**Notes:**

* Supports CO2 measurement (400-40000 ppm), temperature, and humidity
* Web interface provides real-time monitoring and configuration
* Automatic error handling for missing or failed hardware
* Calibration and baseline correction functionality
* Temperature offset and altitude compensation

"""

# === CONFIGURATION PARAMETERS ===
SENSOR_READ_INTERVAL = 5.0      # seconds between automatic readings (SCD41 needs time)
CO2_UNITS = "ppm"               # CO2 in parts per million
TEMPERATURE_UNITS = "C"         # "C" for Celsius, "F" for Fahrenheit  
HUMIDITY_UNITS = "%"            # Relative humidity percentage
ENABLE_AUTO_UPDATES = True      # Enable automatic sensor readings in update loop
LOG_SENSOR_READINGS = False     # Log each sensor reading to foundation
AUTO_BASELINE_CORRECTION = True # Enable automatic baseline correction
TEMPERATURE_OFFSET = 4.0        # Temperature offset in °C (sensor self-heating compensation)
ALTITUDE_METERS = 0             # Altitude above sea level in meters
# === END CONFIGURATION ===

import time
import board
import busio
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

# Remove mock data code
try:
    import adafruit_scd4x
    SCD4X_AVAILABLE = True
except ImportError:
    print("Error: adafruit_scd4x library not found. SCD41 sensor will not function.")
    SCD4X_AVAILABLE = False

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/wicdpico/wicdpico.git"


class SCD41Module(WicdpicoModule):
    """
    SCD41 CO2, Temperature, and Humidity Sensor Module for WicdPico system.
    
    Provides comprehensive web interface and management for SCD41 sensor hardware.
    Supports CO2 measurement, environmental monitoring, calibration, and all
    advanced sensor features available through the Adafruit SCD4x library.
    
    :param foundation: WicdPico foundation instance for system integration
    :type foundation: WicdpicoFoundation
    """
    
    # SCD41 I2C address
    SCD41_DEFAULT_ADDRESS = 0x62
    
    def __init__(self, foundation):
        """
        Initialize SCD41 Module.
        
        Sets up module identification and configuration, then initializes
        I2C communication and sensor hardware.
        
        :param foundation: WicdPico foundation instance
        :type foundation: WicdpicoFoundation
        """
        super().__init__(foundation)
        self.name = "SCD41 CO2 Sensor"
        
        # Configuration from module parameters
        self.read_interval = SENSOR_READ_INTERVAL
        self.co2_units = CO2_UNITS
        self.temperature_units = TEMPERATURE_UNITS
        self.humidity_units = HUMIDITY_UNITS
        self.auto_updates_enabled = ENABLE_AUTO_UPDATES
        self.log_readings = LOG_SENSOR_READINGS
        
        # Sensor state tracking
        self.sensor_available = False
        self.last_reading_time = 0
        self.last_co2 = None
        self.last_temperature = None
        self.last_humidity = None
        self.measurement_active = False
        self.temperature_offset = TEMPERATURE_OFFSET
        self.altitude = ALTITUDE_METERS
        self.auto_baseline = AUTO_BASELINE_CORRECTION
        
        # Status and error tracking
        self.status_message = "SCD41 module initialized"
        self.last_error = None
        
        # Initialize I2C and sensor hardware
        self._initialize_sensor()
        
        self.foundation.startup_print("SCD41 module created")
        self.foundation.startup_print(f"Read interval: {self.read_interval}s")
        self.foundation.startup_print(f"Temperature units: {self.temperature_units}")

    def _initialize_sensor(self):
        """
        Initialize I2C bus and SCD41 sensor hardware.
        
        Sets up I2C communication on GP4(SDA)/GP5(SCL) and attempts to
        connect to SCD41 sensor. Handles initialization errors gracefully.
        """
        try:
            # Set up I2C bus (GP4=SDA, GP5=SCL to match other modules)
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.foundation.startup_print("I2C bus initialized (GP5=SCL, GP4=SDA)")
            
            if not SCD4X_AVAILABLE:
                self.foundation.startup_print("Using mock SCD4x for testing (library not installed)")
            
            # Test if device is actually present by scanning I2C
            while not self.i2c.try_lock():
                pass
            
            try:
                addresses = self.i2c.scan()
                if not SCD4X_AVAILABLE:
                    # Mock mode
                    self.foundation.startup_print("SCD41 mock mode - simulating device")
                elif self.SCD41_DEFAULT_ADDRESS not in addresses:
                    raise Exception("SCD41 device not found on I2C bus at 0x62")
                else:
                    self.foundation.startup_print(f"SCD41 found at I2C address 0x{self.SCD41_DEFAULT_ADDRESS:02X}")
                    
            finally:
                self.i2c.unlock()
            
            # Initialize SCD41 sensor (real or mock)
            self.scd41 = adafruit_scd4x.SCD4X(self.i2c)
            self.sensor_available = True
            
            # Get sensor serial number for identification
            try:
                self.sensor_serial = self.scd41.serial_number
                if isinstance(self.sensor_serial, (list, tuple)):
                    serial_str = "-".join([f"{x:04X}" for x in self.sensor_serial])
                else:
                    serial_str = f"{self.sensor_serial:08X}"
                self.foundation.startup_print(f"SCD41 Serial: {serial_str}")
            except Exception as e:
                self.sensor_serial = None
                self.foundation.startup_print(f"SCD41 serial read failed: {e}")
            
            # Configure sensor settings
            try:
                # Set temperature offset for self-heating compensation
                self.scd41.temperature_offset = self.temperature_offset
                self.foundation.startup_print(f"Temperature offset set to: {self.temperature_offset}°C")
                
                # Set altitude compensation
                self.scd41.altitude = self.altitude
                self.foundation.startup_print(f"Altitude set to: {self.altitude}m")
                
                # Set automatic baseline correction
                self.scd41.automatic_self_calibration = self.auto_baseline
                self.foundation.startup_print(f"Auto baseline correction: {'enabled' if self.auto_baseline else 'disabled'}")
                
                # Start periodic measurements
                self.scd41.start_periodic_measurement()
                self.measurement_active = True
                self.foundation.startup_print("SCD41 periodic measurements started")
                
                # Test if sensor is actually responding by checking data ready
                time.sleep(1)  # Wait a moment for first measurement
                if hasattr(self.scd41, 'data_ready'):
                    data_ready = self.scd41.data_ready
                    self.foundation.startup_print(f"SCD41 data ready status: {data_ready}")
                
                self.status_message = f"SCD41 ready (Serial: {serial_str})" if self.sensor_serial else "SCD41 ready"
                
            except Exception as e:
                self.foundation.startup_print(f"SCD41 configuration failed: {e}")
                self.status_message = "SCD41 connected but configuration failed"
                
        except Exception as e:
            self.sensor_available = False
            self.scd41 = None
            self.i2c = None
            self.last_error = f"SCD41 initialization failed: {e}"
            self.status_message = self.last_error
            self.foundation.startup_print(self.last_error)

    def get_sensor_reading(self):
        """
        Get current CO2, temperature, and humidity readings from SCD41 sensor.
        
        Reads sensor data and converts temperature units based on configuration.
        Handles sensor communication errors gracefully.
        
        :return: Dictionary containing sensor readings and metadata
        :rtype: dict
        """
        if not self.sensor_available or not self.scd41:
            return {
                "success": False,
                "error": "Sensor not available",
                "co2": None,
                "temperature": None,
                "humidity": None,
                "units": {
                    "co2": self.co2_units,
                    "temperature": self.temperature_units,
                    "humidity": self.humidity_units
                },
                "timestamp": time.monotonic()
            }
        
        try:
            # Check if data is ready (if supported)
            if hasattr(self.scd41, 'data_ready') and not self.scd41.data_ready:
                return {
                    "success": False,
                    "error": "Sensor data not ready - measurements may still be starting",
                    "co2": None,
                    "temperature": None,
                    "humidity": None,
                    "units": {
                        "co2": self.co2_units,
                        "temperature": self.temperature_units,
                        "humidity": self.humidity_units
                    },
                    "timestamp": time.monotonic()
                }
            
            # Get measurements from sensor
            co2_ppm = self.scd41.CO2
            temperature_c = self.scd41.temperature
            humidity_percent = self.scd41.relative_humidity
            
            # Convert temperature if needed
            if self.temperature_units == "F":
                temperature = (temperature_c * 9/5) + 32
            else:
                temperature = temperature_c
            
            # Update module state
            self.last_co2 = co2_ppm
            self.last_temperature = temperature
            self.last_humidity = humidity_percent
            self.last_reading_time = time.monotonic()
            
            # Log reading if enabled
            if self.log_readings:
                self.foundation.startup_print(f"SCD41: {co2_ppm}ppm CO2, {temperature:.1f}°{self.temperature_units}, {humidity_percent:.1f}%RH")
            
            return {
                "success": True,
                "error": None,
                "co2": int(co2_ppm),
                "temperature": round(temperature, 1),
                "humidity": round(humidity_percent, 1),
                "units": {
                    "co2": self.co2_units,
                    "temperature": self.temperature_units,
                    "humidity": self.humidity_units
                },
                "timestamp": self.last_reading_time
            }
            
        except Exception as e:
            error_msg = f"Reading failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 error: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "co2": None,
                "temperature": None,
                "humidity": None,
                "units": {
                    "co2": self.co2_units,
                    "temperature": self.temperature_units,
                    "humidity": self.humidity_units
                },
                "timestamp": time.monotonic()
            }

    def set_temperature_offset(self, offset):
        """
        Set SCD41 temperature offset for self-heating compensation.
        
        The SCD41 generates heat during operation which can affect temperature readings.
        This offset compensates for that effect.
        
        :param offset: Temperature offset in °C (typically 4°C)
        :type offset: float
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            self.scd41.temperature_offset = offset
            self.temperature_offset = offset
            
            self.foundation.startup_print(f"SCD41 temperature offset set to: {offset}°C")
            self.status_message = f"Temp offset: {offset}°C"
            
            return True, f"Temperature offset set to {offset}°C"
            
        except Exception as e:
            error_msg = f"Temperature offset change failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 temp offset error: {error_msg}")
            return False, error_msg

    def set_altitude(self, altitude_meters):
        """
        Set SCD41 altitude compensation.
        
        Altitude affects CO2 readings due to air pressure differences.
        Set the altitude above sea level for accurate readings.
        
        :param altitude_meters: Altitude in meters above sea level
        :type altitude_meters: int
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            self.scd41.altitude = altitude_meters
            self.altitude = altitude_meters
            
            self.foundation.startup_print(f"SCD41 altitude set to: {altitude_meters}m")
            self.status_message = f"Altitude: {altitude_meters}m"
            
            return True, f"Altitude set to {altitude_meters}m above sea level"
            
        except Exception as e:
            error_msg = f"Altitude change failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 altitude error: {error_msg}")
            return False, error_msg

    def set_auto_baseline_correction(self, enabled):
        """
        Enable or disable automatic baseline correction.
        
        When enabled, the sensor automatically calibrates its baseline
        CO2 reading over time. Should be enabled for most applications.
        
        :param enabled: True to enable, False to disable
        :type enabled: bool
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            self.scd41.automatic_self_calibration = enabled
            self.auto_baseline = enabled
            
            status = "enabled" if enabled else "disabled"
            self.foundation.startup_print(f"SCD41 auto baseline correction {status}")
            self.status_message = f"Auto baseline: {status}"
            
            return True, f"Auto baseline correction {status}"
            
        except Exception as e:
            error_msg = f"Auto baseline change failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 baseline error: {error_msg}")
            return False, error_msg

    def force_calibration(self, target_co2_ppm):
        """
        Force calibration to a known CO2 concentration.
        
        Use this when the sensor is in a known CO2 environment.
        Typically 400ppm for outdoor air.
        
        :param target_co2_ppm: Known CO2 concentration (400-2000 ppm)
        :type target_co2_ppm: int
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        if not (400 <= target_co2_ppm <= 2000):
            return False, "Target CO2 must be between 400-2000 ppm"
        
        try:
            # Stop measurements for calibration
            if self.measurement_active:
                self.scd41.stop_periodic_measurement()
                time.sleep(0.5)
            
            # Perform forced calibration
            self.scd41.force_calibration(target_co2_ppm)
            
            # Restart measurements
            self.scd41.start_periodic_measurement()
            self.measurement_active = True
            
            self.foundation.startup_print(f"SCD41 force calibrated to {target_co2_ppm} ppm")
            self.status_message = f"Calibrated to {target_co2_ppm} ppm"
            
            return True, f"Force calibration completed at {target_co2_ppm} ppm"
            
        except Exception as e:
            error_msg = f"Force calibration failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 calibration error: {error_msg}")
            
            # Try to restart measurements
            try:
                self.scd41.start_periodic_measurement()
                self.measurement_active = True
            except:
                pass
                
            return False, error_msg

    def single_shot_measurement(self):
        """
        Take a single measurement (alternative to continuous mode).
        
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            # Stop periodic measurements
            if self.measurement_active:
                self.scd41.stop_periodic_measurement()
                self.measurement_active = False
                time.sleep(0.5)
            
            # Take single shot measurement
            self.scd41.measure_single_shot()
            
            # Wait for measurement to complete (about 5 seconds)
            time.sleep(5.5);
            
            # Get the reading
            reading = self.get_sensor_reading();
            
            self.foundation.startup_print("SCD41 single shot measurement completed")
            self.status_message = "Single shot measurement taken"
            
            return True, "Single shot measurement completed"
            
        except Exception as e:
            error_msg = f"Single shot measurement failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 single shot error: {error_msg}")
            return False, error_msg

    def start_continuous_measurement(self):
        """
        Start continuous periodic measurements.
        
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            if not self.measurement_active:
                self.scd41.start_periodic_measurement()
                self.measurement_active = True
            
            self.foundation.startup_print("SCD41 continuous measurements started")
            self.status_message = "Continuous measurements active"
            
            return True, "Continuous measurements started"
            
        except Exception as e:
            error_msg = f"Start continuous failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 start error: {error_msg}")
            return False, error_msg

    def stop_continuous_measurement(self):
        """
        Stop continuous periodic measurements.
        
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            if self.measurement_active:
                self.scd41.stop_periodic_measurement()
                self.measurement_active = False
            
            self.foundation.startup_print("SCD41 continuous measurements stopped")
            self.status_message = "Continuous measurements stopped"
            
            return True, "Continuous measurements stopped"
            
        except Exception as e:
            error_msg = f"Stop continuous failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 stop error: {error_msg}")
            return False, error_msg

    def reset_sensor(self):
        """
        Perform soft reset of SCD41 sensor.
        
        Reinitializes the sensor and restarts measurements.
        
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            self.foundation.startup_print("SCD41: Performing sensor reset...")
            
            # Stop measurements
            if self.measurement_active:
                self.scd41.stop_periodic_measurement()
                self.measurement_active = False
                time.sleep(0.5)
            
            # Reinitialize sensor
            self.scd41.reinit()
            time.sleep(1)
            
            # Restore settings
            self.scd41.temperature_offset = self.temperature_offset
            self.scd41.altitude = self.altitude
            self.scd41.automatic_self_calibration = self.auto_baseline
            
            # Restart measurements
            self.scd41.start_periodic_measurement()
            self.measurement_active = True
            
            # Clear cached state
            self.last_co2 = None
            self.last_temperature = None
            self.last_humidity = None
            self.last_reading_time = 0
            self.last_error = None
            
            self.foundation.startup_print("SCD41: Reset completed successfully")
            self.status_message = "Sensor reset completed"
            
            return True, "Sensor reset completed successfully"
            
        except Exception as e:
            error_msg = f"Reset failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 reset error: {error_msg}")
            return False, error_msg

    def factory_reset(self):
        """
        Perform factory reset of SCD41 sensor.
        
        Resets all calibration and configuration to factory defaults.
        
        :return: Tuple of (success, message)
        :rtype: tuple[bool, str]
        """
        if not self.sensor_available or not self.scd41:
            return False, "Sensor not available"
        
        try:
            # Stop measurements
            if self.measurement_active:
                self.scd41.stop_periodic_measurement()
                self.measurement_active = False
                time.sleep(0.5)
            
            # Factory reset
            self.scd41.factory_reset()
            time.sleep(1)
            
            # Reinitialize with default settings
            self.scd41.reinit()
            time.sleep(1)
            
            # Apply our configuration
            self.scd41.temperature_offset = self.temperature_offset
            self.scd41.altitude = self.altitude
            self.scd41.automatic_self_calibration = self.auto_baseline
            
            # Restart measurements
            self.scd41.start_periodic_measurement()
            self.measurement_active = True
            
            self.foundation.startup_print("SCD41: Factory reset completed")
            self.status_message = "Factory reset completed"
            
            return True, "Factory reset completed - all settings restored to defaults"
            
        except Exception as e:
            error_msg = f"Factory reset failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SCD41 factory reset error: {error_msg}")
            return False, error_msg

    def get_sensor_info(self):
        """
        Get comprehensive sensor information and status.
        
        :return: Dictionary containing complete sensor information
        :rtype: dict
        """
        serial_info = "N/A"
        if self.sensor_serial:
            if isinstance(self.sensor_serial, (list, tuple)):
                serial_info = "-".join([f"{x:04X}" for x in self.sensor_serial])
            else:
                serial_info = f"{self.sensor_serial:08X}"
        
        return {
            "available": self.sensor_available,
            "serial_number": serial_info,
            "measurement_active": self.measurement_active,
            "temperature_offset": self.temperature_offset,
            "altitude": self.altitude,
            "auto_baseline_correction": self.auto_baseline,
            "last_reading_time": self.last_reading_time,
            "last_co2": self.last_co2,
            "last_temperature": self.last_temperature,
            "last_humidity": self.last_humidity,
            "units": {
                "co2": self.co2_units,
                "temperature": self.temperature_units,
                "humidity": self.humidity_units
            },
            "status_message": self.status_message,
            "last_error": self.last_error,
            "library_available": SCD4X_AVAILABLE
        }

    def register_routes(self, server):
        """
        Register HTTP routes for SCD41 web interface.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        """
        
        @server.route("/scd41-reading", methods=['POST'])
        def scd41_reading(request: Request):
            """Handle sensor reading requests."""
            try:
                reading = self.get_sensor_reading()
                
                if reading['success']:
                    response_text = f"CO2: {reading['co2']} {reading['units']['co2']}<br>"
                    response_text += f"Temperature: {reading['temperature']}°{reading['units']['temperature']}<br>"
                    response_text += f"Humidity: {reading['humidity']}{reading['units']['humidity']}<br>"
                    response_text += f"Reading time: {reading['timestamp']:.1f}s"
                    
                    self.status_message = f"Last: {reading['co2']}ppm, {reading['temperature']}°{reading['units']['temperature']}"
                    
                else:
                    response_text = f"Reading failed: {reading['error']}"
                    self.status_message = f"Error: {reading['error']}"
                
                return Response(request, response_text, content_type="text/html")
                
            except Exception as e:
                error_msg = f"Route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/scd41-temp-offset", methods=['POST'])
        def scd41_temp_offset(request: Request):
            """Handle temperature offset change requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                import re
                match = re.search(r'offset=([\d.]+)', body)
                if not match:
                    return Response(request, "No valid temperature offset specified", content_type="text/plain")
                
                offset = float(match.group(1))
                success, message = self.set_temperature_offset(offset)
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Temperature offset route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/scd41-altitude", methods=['POST'])
        def scd41_altitude(request: Request):
            """Handle altitude change requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                import re
                match = re.search(r'altitude=(\d+)', body)
                if not match:
                    return Response(request, "No valid altitude specified", content_type="text/plain")
                
                altitude = int(match.group(1))
                success, message = self.set_altitude(altitude)
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Altitude route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/scd41-baseline", methods=['POST'])
        def scd41_baseline(request: Request):
            """Handle auto baseline correction requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                if "baseline=ENABLE" in body:
                    enabled = True
                elif "baseline=DISABLE" in body:
                    enabled = False
                else:
                    return Response(request, "No valid baseline command specified", content_type="text/plain")
                
                success, message = self.set_auto_baseline_correction(enabled)
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Baseline route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/scd41-calibration", methods=['POST'])
        def scd41_calibration(request: Request):
            """Handle force calibration requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                import re
                match = re.search(r'co2=(\d+)', body)
                if not match:
                    return Response(request, "No valid CO2 concentration specified", content_type="text/plain")
                
                co2_ppm = int(match.group(1))
                success, message = self.force_calibration(co2_ppm)
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Calibration route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/scd41-measurement", methods=['POST'])
        def scd41_measurement(request: Request):
            """Handle measurement control requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                if "mode=START" in body:
                    success, message = self.start_continuous_measurement()
                elif "mode=STOP" in body:
                    success, message = self.stop_continuous_measurement()
                elif "mode=SINGLE" in body:
                    success, message = self.single_shot_measurement()
                else:
                    return Response(request, "No valid measurement command specified", content_type="text/plain")
                
                if success:
                    response_text = f"✓ {message}"
                else:
                    response_text = f"✗ {message}"
                
                return Response(request, response_text, content_type="text/plain")
                
            except Exception as e:
                error_msg = f"Measurement route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/scd41-info", methods=['POST'])
        def scd41_info(request: Request):
            """Handle sensor information requests."""
            try:
                info = self.get_sensor_info()
                
                response_html = f"""
                <strong>Sensor Information:</strong><br>
                • Serial: {info['serial_number']}<br>
                • Measurements: {'Active' if info['measurement_active'] else 'Stopped'}<br>
                • Temp Offset: {info['temperature_offset']}°C<br>
                • Altitude: {info['altitude']}m<br>
                • Auto Baseline: {'Enabled' if info['auto_baseline_correction'] else 'Disabled'}<br>
                • Library: {'Real SCD4x' if info['library_available'] else 'Mock/Testing'}<br>
                • Status: {'Available' if info['available'] else 'Unavailable'}
                """
                
                if info['last_co2'] is not None:
                    response_html += f"<br>• Last: {info['last_co2']}ppm, {info['last_temperature']:.1f}°{info['units']['temperature']}, {info['last_humidity']:.1f}%RH"
                
                if info['last_error']:
                    response_html += f"<br>• Error: {info['last_error']}"
                
                return Response(request, response_html, content_type="text/html")
                
            except Exception as e:
                error_msg = f"Info route error: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/scd41-reset", methods=['POST'])
        def scd41_reset(request: Request):
            """Handle sensor reset requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                if "reset=FACTORY" in body:
                    success, message = self.factory_reset()
                else:
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
        
        self.foundation.startup_print("SCD41 reading, temp-offset, altitude, baseline, calibration, measurement, info, and reset routes registered")

    def get_dashboard_html(self):
        """
        Generate HTML dashboard widget for SCD41 control.
        
        Creates interactive web interface with sensor readings display
        and control buttons for all SCD41 features.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
        # Sensor information display
        sensor_info_line = f"Serial: {self.sensor_serial}" if self.sensor_serial else "No serial available"
        if not SCD4X_AVAILABLE:
            sensor_info_line += " (Mock)"
        
        # Status indicators with colors
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        measurement_color = "#28a745" if self.measurement_active else "#6c757d"
        baseline_color = "#28a745" if self.auto_baseline else "#6c757d"
        error_display = f"<br><span style='color: #dc3545;'><strong>Error:</strong> {self.last_error}</span>" if self.last_error else ""
        
        # Show last reading with timestamp if available
        last_reading = ""
        if self.last_co2 is not None:
            reading_time = time.monotonic() - self.last_reading_time if self.last_reading_time > 0 else 0
            last_reading = f"<br><strong>Last Reading:</strong> {self.last_co2}ppm CO2, {self.last_temperature:.1f}°{self.temperature_units}, {self.last_humidity:.1f}%RH ({reading_time:.0f}s ago)"
        
        return f'''
        <div class="module">
            <h3>SCD41 CO2, Temperature & Humidity Sensor</h3>
            <div class="status" style="border-left: 4px solid {status_color};">
                <strong>Status:</strong> <span style="color: {status_color};">{self.status_message}</span><br>
                <strong>Sensor:</strong> {sensor_info_line}<br>
                <strong>Measurements:</strong> <span id="current-measurement" style="color: {measurement_color};">{'Active' if self.measurement_active else 'Stopped'}</span><br>
                <strong>Temp Offset:</strong> <span id="current-offset">{self.temperature_offset}</span>°C<br>
                <strong>Altitude:</strong> <span id="current-altitude">{self.altitude}</span>m<br>
                <strong>Auto Baseline:</strong> <span id="current-baseline" style="color: {baseline_color};">{'Enabled' if self.auto_baseline else 'Disabled'}</span>{last_reading}{error_display}
            </div>
            
            <div id="scd41-status" class="status" style="margin-top: 10px; background: #e7f3ff; border-left: 4px solid #007bff;">
                <strong>Ready:</strong> SCD41 CO2 Sensor Module initialized!
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Sensor Control</h4>
                <button id="scd41-reading-btn" onclick="getSCD41Reading()" style="background: #007bff;">Get Reading</button>
                <button id="scd41-info-btn" onclick="getSCD41Info()" style="background: #17a2b8;">Sensor Info</button>
                <button id="scd41-reset-btn" onclick="resetSCD41()" style="background: #dc3545;">Reset Sensor</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Measurement Control</h4>
                <button id="measurement-start-btn" onclick="setSCD41Measurement('START')" style="background: #28a745;">Start Continuous</button>
                <button id="measurement-stop-btn" onclick="setSCD41Measurement('STOP')" style="background: #6c757d;">Stop Continuous</button>
                <button id="measurement-single-btn" onclick="setSCD41Measurement('SINGLE')" style="background: #fd7e14;">Single Shot</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Configuration</h4>
                <button id="baseline-enable-btn" onclick="setSCD41Baseline('ENABLE')" style="background: #28a745;">Enable Auto Baseline</button>
                <button id="baseline-disable-btn" onclick="setSCD41Baseline('DISABLE')" style="background: #6c757d;">Disable Auto Baseline</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Temperature Offset (°C)</h4>
                <button id="offset-2-btn" onclick="setSCD41TempOffset(2.0)" style="background: #20c997;">2.0°C</button>
                <button id="offset-4-btn" onclick="setSCD41TempOffset(4.0)" style="background: #007bff;">4.0°C (Default)</button>
                <button id="offset-6-btn" onclick="setSCD41TempOffset(6.0)" style="background: #fd7e14;">6.0°C</button>
                <input type="number" id="custom-offset" min="0" max="20" step="0.1" value="4.0" style="width: 60px; margin: 0 5px;">
                <button id="offset-custom-btn" onclick="setSCD41TempOffsetCustom()" style="background: #17a2b8;">Set Custom</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Altitude (meters)</h4>
                <button id="altitude-0-btn" onclick="setSCD41Altitude(0)" style="background: #007bff;">Sea Level</button>
                <button id="altitude-500-btn" onclick="setSCD41Altitude(500)" style="background: #28a745;">500m</button>
                <button id="altitude-1000-btn" onclick="setSCD41Altitude(1000)" style="background: #ffc107; color: #212529;">1000m</button>
                <input type="number" id="custom-altitude" min="0" max="3000" value="0" style="width: 70px; margin: 0 5px;">
                <button id="altitude-custom-btn" onclick="setSCD41AltitudeCustom()" style="background: #17a2b8;">Set Custom</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Calibration</h4>
                <button id="calibrate-400-btn" onclick="setSCD41Calibration(400)" style="background: #28a745;">400ppm (Outdoor)</button>
                <button id="calibrate-1000-btn" onclick="setSCD41Calibration(1000)" style="background: #ffc107; color: #212529;">1000ppm</button>
                <input type="number" id="custom-co2" min="400" max="2000" value="400" style="width: 70px; margin: 0 5px;">
                <button id="calibrate-custom-btn" onclick="setSCD41CalibrationCustom()" style="background: #17a2b8;">Force Calibrate</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Factory Reset</h4>
                <button id="factory-reset-btn" onclick="factoryResetSCD41()" style="background: #dc3545;">Factory Reset</button>
            </div>
        </div>

        <script>
        function getSCD41Reading() {{
            const btn = document.getElementById('scd41-reading-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/scd41-reading', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = '<strong>Latest Reading:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#d4edda';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #28a745';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = '<strong>Reading Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function getSCD41Info() {{
            const btn = document.getElementById('scd41-info-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Getting...';

            fetch('/scd41-info', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = result;
                    document.getElementById('scd41-status').style.background = '#e2e3e5';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #6c757d';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = '<strong>Info Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSCD41Measurement(mode) {{
            const buttons = ['measurement-start-btn', 'measurement-stop-btn', 'measurement-single-btn'];
            const originalTexts = {{}};
            
            buttons.forEach(id => {{
                const btn = document.getElementById(id);
                originalTexts[id] = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Setting...';
            }});

            fetch('/scd41-measurement', {{ 
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
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Measurement Control:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#d1ecf1';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #17a2b8';
                    
                    const measurementSpan = document.getElementById('current-measurement');
                    if (mode === 'START') {{
                        measurementSpan.textContent = 'Active';
                        measurementSpan.style.color = '#28a745';
                    }} else if (mode === 'STOP') {{
                        measurementSpan.textContent = 'Stopped';
                        measurementSpan.style.color = '#6c757d';
                    }}
                }})
                .catch(error => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Measurement Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSCD41Baseline(command) {{
            const buttons = ['baseline-enable-btn', 'baseline-disable-btn'];
            const originalTexts = {{}};
            
            buttons.forEach(id => {{
                const btn = document.getElementById(id);
                originalTexts[id] = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Setting...';
            }});

            fetch('/scd41-baseline', {{ 
                method: 'POST',
                body: 'baseline=' + command
            }})
                .then(response => response.text())
                .then(result => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Baseline Changed:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#fff3cd';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #ffc107';
                    
                    const baselineSpan = document.getElementById('current-baseline');
                    baselineSpan.textContent = command === 'ENABLE' ? 'Enabled' : 'Disabled';
                    baselineSpan.style.color = command === 'ENABLE' ? '#28a745' : '#6c757d';
                }})
                .catch(error => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Baseline Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSCD41TempOffset(offset) {{
            const buttons = ['offset-2-btn', 'offset-4-btn', 'offset-6-btn'];
            const originalTexts = {{}};
            
            buttons.forEach(id => {{
                const btn = document.getElementById(id);
                originalTexts[id] = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Setting...';
            }});

            fetch('/scd41-temp-offset', {{ 
                method: 'POST',
                body: 'offset=' + offset
            }})
                .then(response => response.text())
                .then(result => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Temperature Offset Changed:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#d1ecf1';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #17a2b8';
                    document.getElementById('current-offset').textContent = offset;
                }})
                .catch(error => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Temp Offset Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSCD41TempOffsetCustom() {{
            const customValue = document.getElementById('custom-offset').value;
            const offset = parseFloat(customValue);
            
            if (isNaN(offset) || offset < 0 || offset > 20) {{
                document.getElementById('scd41-status').innerHTML = '<strong>Error:</strong><br>Custom temperature offset must be between 0 and 20°C';
                document.getElementById('scd41-status').style.background = '#f8d7da';
                document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                return;
            }}
            
            setSCD41TempOffset(offset);
        }}
        
        function setSCD41Altitude(altitude) {{
            const buttons = ['altitude-0-btn', 'altitude-500-btn', 'altitude-1000-btn'];
            const originalTexts = {{}};
            
            buttons.forEach(id => {{
                const btn = document.getElementById(id);
                originalTexts[id] = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Setting...';
            }});

            fetch('/scd41-altitude', {{ 
                method: 'POST',
                body: 'altitude=' + altitude
            }})
                .then(response => response.text())
                .then(result => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Altitude Changed:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#d1ecf1';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #17a2b8';
                    document.getElementById('current-altitude').textContent = altitude;
                }})
                .catch(error => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Altitude Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSCD41AltitudeCustom() {{
            const customValue = document.getElementById('custom-altitude').value;
            const altitude = parseInt(customValue);
            
            if (isNaN(altitude) || altitude < 0 || altitude > 3000) {{
                document.getElementById('scd41-status').innerHTML = '<strong>Error:</strong><br>Custom altitude must be between 0 and 3000 meters';
                document.getElementById('scd41-status').style.background = '#f8d7da';
                document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                return;
            }}
            
            setSCD41Altitude(altitude);
        }}
        
        function setSCD41Calibration(co2_ppm) {{
            if (!confirm('Force calibration to ' + co2_ppm + ' ppm? Only do this when the sensor is in a known CO2 environment.')) {{
                return;
            }}
            
            const buttons = ['calibrate-400-btn', 'calibrate-1000-btn'];
            const originalTexts = {{}};
            
            buttons.forEach(id => {{
                const btn = document.getElementById(id);
                originalTexts[id] = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Calibrating...';
            }});

            fetch('/scd41-calibration', {{ 
                method: 'POST',
                body: 'co2=' + co2_ppm
            }})
                .then(response => response.text())
                .then(result => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Calibration Complete:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#fff3cd';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #ffc107';
                }})
                .catch(error => {{
                    buttons.forEach(id => {{
                        const btn = document.getElementById(id);
                        btn.disabled = false;
                        btn.textContent = originalTexts[id];
                    }});
                    
                    document.getElementById('scd41-status').innerHTML = '<strong>Calibration Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setSCD41CalibrationCustom() {{
            const customValue = document.getElementById('custom-co2').value;
            const co2_ppm = parseInt(customValue);
            
            if (isNaN(co2_ppm) || co2_ppm < 400 || co2_ppm > 2000) {{
                document.getElementById('scd41-status').innerHTML = '<strong>Error:</strong><br>Custom CO2 concentration must be between 400 and 2000 ppm';
                document.getElementById('scd41-status').style.background = '#f8d7da';
                document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                return;
            }}
            
            setSCD41Calibration(co2_ppm);
        }}
        
        function resetSCD41() {{
            if (!confirm('Reset SCD41 sensor? This will reinitialize the sensor and restart measurements.')) {{
                return;
            }}
            
            const btn = document.getElementById('scd41-reset-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Resetting...';

            fetch('/scd41-reset', {{ method: 'POST' }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = '<strong>Reset Complete:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#fff3cd';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #ffc107';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = '<strong>Reset Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function factoryResetSCD41() {{
            if (!confirm('FACTORY RESET SCD41? This will erase ALL calibration data and restore factory defaults. This cannot be undone!')) {{
                return;
            }}
            
            const btn = document.getElementById('factory-reset-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Factory Resetting...';

            fetch('/scd41-reset', {{ 
                method: 'POST',
                body: 'reset=FACTORY'
            }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = '<strong>Factory Reset Complete:</strong><br>' + result;
                    document.getElementById('scd41-status').style.background = '#fff3cd';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #ffc107';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('scd41-status').innerHTML = '<strong>Factory Reset Error:</strong><br>' + error.message;
                    document.getElementById('scd41-status').style.background = '#f8d7da';
                    document.getElementById('scd41-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        </script>
        '''

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Handles automatic sensor readings if enabled.
        """
        if self.auto_updates_enabled and self.sensor_available and self.measurement_active:
            current_time = time.monotonic()
            if current_time - self.last_reading_time >= self.read_interval:
                self.get_sensor_reading()

    def cleanup(self):
        """
        Cleanup method called during system shutdown.
        """
        if self.sensor_available and self.measurement_active:
            try:
                self.scd41.stop_periodic_measurement()
                self.foundation.startup_print("SCD41 cleanup: Measurements stopped")
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