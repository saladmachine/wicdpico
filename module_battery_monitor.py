# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`battery_monitor_module`
====================================================

Battery monitoring module for WicdPico system using internal VSYS monitoring.

Provides web interface and monitoring for battery voltage using Pico 2 W's
built-in VOLTAGE_MONITOR pin.

* Author(s): WicdPico Development Team

Implementation Notes
--------------------

**Hardware:**

* Uses Pico 2 W's internal VOLTAGE_MONITOR (board.VOLTAGE_MONITOR)
* No external ADC required
* Monitors VSYS rail voltage directly
* Optional load testing with onboard LED

**Software and Dependencies:**

* Adafruit CircuitPython firmware for Raspberry Pi Pico 2 W
* analogio for ADC access
* adafruit_httpserver
* WicdPico foundation system

**Notes:**

* Internal voltage monitoring provides direct battery voltage reading
* Load testing accelerates battery drain for testing purposes
* Web interface provides voltage readings and load test controls
* CSV logging capability when SD card module available

"""

import board
import analogio
import digitalio
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/wicdpico/wicdpico.git"


class BatteryMonitorModule(WicdpicoModule):
    """
    Battery Monitor Module for WicdPico system.
    
    Provides internal VSYS voltage monitoring and load testing capabilities.
    Uses Pico 2 W's built-in VOLTAGE_MONITOR pin for accurate readings.
    
    :param foundation: WicdPico foundation instance for system integration
    :type foundation: WicdPico
    
    **Quickstart: Using the battery monitor**
    
    .. code-block:: python
    
        from foundation_core import WicdPico
        from module_battery_monitor import BatteryMonitorModule
        
        foundation = WicdPico()
        battery = BatteryMonitorModule(foundation)
        foundation.register_module("battery", battery)
        
        # Get current voltage
        voltage = battery.get_voltage()
        print("Battery voltage: " + str(voltage) + "V")
    """
    
    def __init__(self, foundation):
        """
        Initialize Battery Monitor Module.
        
        Sets up internal VSYS voltage monitoring using built-in ADC.
        Configures load testing and logging capabilities.
        
        :param foundation: WicdPico foundation instance
        :type foundation: WicdPico
        """
        super().__init__(foundation)
        self.name = "Battery Monitor"

        try:
            # Initialize ADC for internal VSYS monitoring
            self.adc = analogio.AnalogIn(board.VOLTAGE_MONITOR)
            self.voltage_available = True
            self.foundation.startup_print("Internal VSYS voltage monitoring initialized")
        except Exception as e:
            self.voltage_available = False
            self.foundation.startup_print("Voltage monitoring failed: " + str(e))

        # Module references (set after registration)
        self.led_module = None
        
        # Load test states
        self.load_test_active = False
        self.test_cycle_count = 0
        self.last_led_toggle = time.monotonic()
        self.led_toggle_interval = 0.1  # 100ms for high-power load
        
        # Logging states
        self.logging_active = False
        self.last_log_time = time.monotonic()
        self.log_interval = 60  # 1 minute between readings
        self.log_entries = []  # Store recent readings for web display
        self.max_log_entries = 20  # Keep last 20 readings in memory

    def get_voltage(self):
        """
        Get current battery voltage from internal VSYS monitoring.
        
        :return: Voltage in volts or None if unavailable
        :rtype: float or None
        
        .. note::
           Uses Pico 2 W's built-in voltage divider on VSYS rail.
           Voltage reading represents actual battery/supply voltage.
        """
        if not self.voltage_available:
            return None
            
        try:
            # Read ADC value and convert to voltage
            # Pico 2 W VOLTAGE_MONITOR has built-in voltage divider
            # Convert 16-bit ADC reading to voltage (3.3V reference)
            raw_value = self.adc.value
            voltage = (raw_value * 3.3) / 65535.0
            
            # VOLTAGE_MONITOR has 3:1 voltage divider, so multiply by 3
            actual_voltage = voltage * 3.0
            
            return round(actual_voltage, 2)
        except Exception as e:
            self.foundation.startup_print("Error reading voltage: " + str(e))
            return None

    def start_load_test(self):
        """
        Start high-power load test to accelerate battery drain.
        
        Uses rapid LED toggling and CPU activity to increase current draw.
        Useful for testing battery life and voltage curves.
        """
        if self.led_module:
            self.load_test_active = True
            self.test_cycle_count = 0
            self.foundation.startup_print("High-power load test started")
        else:
            self.foundation.startup_print("Load test requires LED module")

    def stop_load_test(self):
        """Stop high-power load test and return to normal operation."""
        self.load_test_active = False
        if self.led_module:
            self.led_module.set_led(False)  # Turn off LED
        self.foundation.startup_print("High-power load test stopped")

    def start_logging(self):
        """Start battery voltage logging."""
        self.logging_active = True
        self.last_log_time = time.monotonic()
        self.log_entries.clear()
        self.foundation.startup_print("Battery voltage logging started")

    def stop_logging(self):
        """Stop battery voltage logging."""
        self.logging_active = False
        self.foundation.startup_print("Battery voltage logging stopped")

    def _update_load_test(self):
        """Update load test state - rapid LED toggling for high current draw."""
        if not self.load_test_active or not self.led_module:
            return
            
        current_time = time.monotonic()
        if current_time - self.last_led_toggle >= self.led_toggle_interval:
            # Toggle LED rapidly for power consumption
            current_state = self.led_module.led_state
            self.led_module.set_led(not current_state)
            
            self.last_led_toggle = current_time
            self.test_cycle_count += 1
            
            # Add CPU load with some calculations
            for i in range(100):
                dummy = i * i * 0.1

    def _update_logging(self):
        """Update voltage logging - record readings at specified intervals."""
        if not self.logging_active:
            return
            
        current_time = time.monotonic()
        if current_time - self.last_log_time >= self.log_interval:
            voltage = self.get_voltage()
            if voltage is not None:
                # Create log entry
                log_entry = {
                    'time': current_time,
                    'voltage': voltage,
                    'load_test': self.load_test_active
                }
                
                # Add to memory buffer
                self.log_entries.append(log_entry)
                
                # Keep only recent entries
                if len(self.log_entries) > self.max_log_entries:
                    self.log_entries = self.log_entries[-self.max_log_entries:]
                
                self.last_log_time = current_time
                self.foundation.startup_print("Logged voltage: " + str(voltage) + "V")

    def get_log_summary(self):
        """
        Get summary of recent voltage log entries.
        
        :return: HTML formatted string of recent readings
        :rtype: str
        """
        if not self.log_entries:
            return "No voltage readings logged yet"
            
        summary = "<strong>Recent Voltage Readings:</strong><br>"
        for entry in self.log_entries[-10:]:  # Show last 10 entries
            load_status = " (Load Test)" if entry['load_test'] else ""
            summary += str(entry['voltage']) + "V" + load_status + "<br>"
            
        return summary

    def register_routes(self, server):
        """
        Register HTTP routes for battery monitor web interface.
        
        Provides REST endpoints for voltage monitoring and control.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        
        **Available Routes:**
        
        * ``POST /battery-voltage`` - Get current battery voltage
        * ``POST /battery-load-test`` - Start/stop load test
        * ``POST /battery-logging`` - Start/stop voltage logging
        """
        @server.route("/battery-voltage", methods=['POST'])
        def battery_voltage(request: Request):
            """Get current battery voltage reading."""
            try:
                if not self.voltage_available:
                    return Response(request, "Voltage monitoring not available", content_type="text/plain")

                voltage = self.get_voltage()
                if voltage is None:
                    return Response(request, "Error reading voltage", content_type="text/plain")

                status_text = "Battery Voltage: " + str(voltage) + "V<br>"
                if self.load_test_active:
                    status_text += "Load Test: Active (" + str(self.test_cycle_count) + " cycles)<br>"
                else:
                    status_text += "Load Test: Inactive<br>"
                    
                if self.logging_active:
                    status_text += "Logging: Active (" + str(len(self.log_entries)) + " readings)"
                else:
                    status_text += "Logging: Inactive"

                return Response(request, status_text, content_type="text/html")

            except Exception as e:
                error_msg = "Battery voltage error: " + str(e)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/battery-load-test", methods=['POST'])
        def battery_load_test(request: Request):
            """Start or stop load test."""
            try:
                if self.load_test_active:
                    self.stop_load_test()
                    return Response(request, "Load test stopped", content_type="text/plain")
                else:
                    self.start_load_test()
                    return Response(request, "Load test started", content_type="text/plain")

            except Exception as e:
                error_msg = "Load test error: " + str(e)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/battery-logging", methods=['POST'])
        def battery_logging(request: Request):
            """Start or stop voltage logging."""
            try:
                if self.logging_active:
                    self.stop_logging()
                    log_summary = self.get_log_summary()
                    return Response(request, "Logging stopped<br><br>" + log_summary, content_type="text/html")
                else:
                    self.start_logging()
                    return Response(request, "Voltage logging started", content_type="text/plain")

            except Exception as e:
                error_msg = "Logging error: " + str(e)
                return Response(request, error_msg, content_type="text/plain")

    def get_dashboard_html(self):
        """
        Generate HTML dashboard widget for battery monitor.
        
        Creates interactive web interface with voltage display and control buttons.
        Includes JavaScript for AJAX communication with the server.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
        return '''
        <div class="module">
            <h3>Battery Monitor</h3>
            <div class="control-group">
                <button id="battery-voltage-btn" onclick="getBatteryVoltage()">Get Voltage</button>
                <button id="battery-load-test-btn" onclick="toggleLoadTest()">Toggle Load Test</button>
                <button id="battery-logging-btn" onclick="toggleLogging()">Toggle Logging</button>
            </div>
            <p id="battery-voltage-display">Battery: Click button for voltage</p>
        </div>

        <script>
        function getBatteryVoltage() {
            const btn = document.getElementById('battery-voltage-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/battery-voltage', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'Get Voltage';
                    document.getElementById('battery-voltage-display').innerHTML = result;
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'Get Voltage';
                    document.getElementById('battery-voltage-display').textContent = 'Error: ' + error.message;
                });
        }

        function toggleLoadTest() {
            const btn = document.getElementById('battery-load-test-btn');
            btn.disabled = true;
            btn.textContent = 'Working...';

            fetch('/battery-load-test', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'Toggle Load Test';
                    document.getElementById('battery-voltage-display').textContent = result;
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'Toggle Load Test';
                    document.getElementById('battery-voltage-display').textContent = 'Error: ' + error.message;
                });
        }

        function toggleLogging() {
            const btn = document.getElementById('battery-logging-btn');
            btn.disabled = true;
            btn.textContent = 'Working...';

            fetch('/battery-logging', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'Toggle Logging';
                    document.getElementById('battery-voltage-display').innerHTML = result;
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'Toggle Logging';
                    document.getElementById('battery-voltage-display').textContent = 'Error: ' + error.message;
                });
        }
        </script>
        '''

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Handles load testing and voltage logging updates.
        
        .. note::
           This method is called periodically by the WicdPico foundation.
           Manages load test LED toggling and voltage data logging.
        """
        self._update_load_test()
        self._update_logging()

    def cleanup(self):
        """
        Cleanup method called during system shutdown.
        
        Stops any active load tests and cleans up resources.
        """
        if self.load_test_active:
            self.stop_load_test()
        if self.logging_active:
            self.stop_logging()

    @property
    def current_voltage(self):
        """
        Get current voltage reading (property access).
        
        :return: Current voltage in volts
        :rtype: float or None
        """
        return self.get_voltage()

    @property  
    def is_load_testing(self):
        """
        Check if load test is currently active.
        
        :return: True if load test running, False otherwise
        :rtype: bool
        """
        return self.load_test_active

    @property
    def is_logging(self):
        """
        Check if voltage logging is currently active.
        
        :return: True if logging active, False otherwise
        :rtype: bool  
        """
        return self.logging_active