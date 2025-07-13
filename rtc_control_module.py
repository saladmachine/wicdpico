# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`rtc_control_module`
====================================================

RTC (Real-Time Clock) control module for PicoWicd system.

Provides web interface and management for PCF8523 RTC hardware
on Raspberry Pi Pico with CircuitPython.

* Author(s): PicoWicd Development Team

Implementation Notes
--------------------

**Hardware:**

* Designed for use with Adafruit PicoBell Adalogger FeatherWing
* Uses PCF8523 RTC via I2C (GP4=SDA, GP5=SCL)
* Requires adafruit_pcf8523 library

**Software and Dependencies:**

* Adafruit CircuitPython firmware for Raspberry Pi Pico 2 W
* adafruit_pcf8523.pcf8523
* adafruit_httpserver
* PicoWicd foundation system

**Notes:**

* Battery backup provides timekeeping during power loss
* Web interface provides status checking and time management
* Automatic error handling for missing or failed hardware

"""

import time
import board
import busio
from module_base import PicowicdModule
from adafruit_httpserver import Request, Response
from adafruit_pcf8523.pcf8523 import PCF8523

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/picowicd/picowicd.git"


class RTCControlModule(PicowicdModule):
    """
    RTC Control Module for PicoWicd system.
    
    Provides web interface and management for PCF8523 RTC hardware.
    Handles time reading, battery status monitoring, and power loss detection.
    
    :param foundation: PicoWicd foundation instance for system integration
    :type foundation: PicoWicd
    
    **Quickstart: Importing and using the module**
    
    Here is an example of using the RTCControlModule:
    
    .. code-block:: python
    
        import busio
        import board
        from foundation_core import PicoWicd
        from rtc_control_module import RTCControlModule
        
        # Initialize foundation system
        foundation = PicoWicd()
        
        # Create RTC module
        rtc_module = RTCControlModule(foundation)
        
        # Register with web server
        rtc_module.register_routes(foundation.server)
        
        # Get current status
        if rtc_module.rtc_available:
            current_time = rtc_module.rtc.datetime
            print(f"Current time: {current_time}")
    """
    
    def __init__(self, foundation):
        """
        Initialize RTC Control Module.
        
        Sets up I2C communication and PCF8523 RTC hardware.
        Handles initialization errors gracefully.
        
        :param foundation: PicoWicd foundation instance
        :type foundation: PicoWicd
        """
        super().__init__(foundation)
        self.name = "RTC Control"

        try:
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.rtc = PCF8523(self.i2c)
            self.rtc_available = True
            self.foundation.startup_print("RTC PCF8523 initialized successfully.")
        except Exception as e:
            self.rtc_available = False
            self.foundation.startup_print(f"RTC initialization failed: {str(e)}. RTC will be unavailable.")

        self.days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        self.last_update_time = time.monotonic()
        self.update_interval = 10  # seconds

    def register_routes(self, server):
        """
        Register HTTP routes for RTC web interface.
        
        Provides REST endpoints for RTC status and control.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        
        **Available Routes:**
        
        * ``POST /rtc-status`` - Get current RTC status including time, battery, and power loss status
        """
        @server.route("/rtc-status", methods=['POST'])
        def rtc_status(request: Request):
            """
            Handle RTC status requests.
            
            Returns current time, battery status, and power loss detection.
            If battery is low or power was lost, automatically resets time to 2000/01/01.
            
            :param request: HTTP request object
            :type request: Request
            :return: HTTP response with RTC status
            :rtype: Response
            """
            try:
                if not self.rtc_available:
                    return Response(request, "RTC not available", content_type="text/plain")

                current_time = self.rtc.datetime
                battery_low = self.rtc.battery_low
                lost_power = self.rtc.lost_power

                if battery_low or lost_power:
                    self.foundation.startup_print("RTC: Battery low or power lost detected. Setting time to 2000/01/01 00:00:00.")
                    t = time.struct_time((2000, 1, 1, 0, 0, 0, 5, -1, -1))
                    self.rtc.datetime = t
                    current_time = self.rtc.datetime
                    battery_low = self.rtc.battery_low
                    lost_power = self.rtc.lost_power

                    status_prefix = "RTC Reset: "
                else:
                    status_prefix = "RTC Status: "

                formatted_time = f"{self.days[current_time.tm_wday]} {current_time.tm_mon}/{current_time.tm_mday}/{current_time.tm_year} {current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}"

                status_text = f"Time: {formatted_time}<br>"
                status_text += f"Battery Low: {'Yes' if battery_low else 'No'}<br>"
                status_text += f"Lost Power: {'Yes' if lost_power else 'No'}"

                self.foundation.startup_print(f"{status_prefix}{formatted_time}, Bat Low: {battery_low}, Lost Pwr: {lost_power}")

                return Response(request, status_text, content_type="text/html")

            except Exception as e:
                error_msg = f"Error reading/setting RTC: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

    def get_dashboard_html(self):
        """
        Generate HTML dashboard widget for RTC control.
        
        Creates interactive web interface with status display and control buttons.
        Includes JavaScript for AJAX communication with the server.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
        return '''
        <div class="module">
            <h3>RTC Control</h3>
            <div class="control-group">
                <button id="rtc-status-btn" onclick="getRTCStatus()">Get RTC Status</button>
            </div>
            <p id="rtc-display-status">RTC Status: Click button</p>
        </div>

        <script>
        // JavaScript for Get RTC Status
        function getRTCStatus() {
            const btn = document.getElementById('rtc-status-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/rtc-status', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'Get RTC Status';
                    document.getElementById('rtc-display-status').innerHTML = 'RTC Status: ' + result;
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'Get RTC Status';
                    document.getElementById('rtc-display-status').textContent = 'Error: ' + error.message;
                });
        }
        </script>
        '''

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Performs regular maintenance tasks. Currently disabled to prevent
        console spam but maintains compatibility with foundation system.
        
        .. note::
           This method is called periodically by the PicoWicd foundation.
           Override this method to add custom periodic tasks.
        """
        # FIX: Commented out the body of the update method to stop printing "Live RTC" updates.
        # The method itself remains to avoid AttributeError if foundation_core.py calls it.
        # This will prevent the "Live RTC..." messages from being printed.
        pass

    def cleanup(self):
        """
        Cleanup method called during system shutdown.
        
        Performs any necessary cleanup operations before module shutdown.
        Currently no cleanup is required for RTC hardware.
        """
        pass

    @property
    def current_time(self):
        """
        Get current time from RTC hardware.
        
        :return: Current time structure or None if RTC unavailable
        :rtype: time.struct_time or None
        
        .. code-block:: python
        
            # Get current time
            if rtc_module.rtc_available:
                current_time = rtc_module.current_time
                print(f"Hour: {current_time.tm_hour}")
        """
        if self.rtc_available:
            try:
                return self.rtc.datetime
            except Exception:
                return None
        return None

    @property
    def battery_status(self):
        """
        Get RTC battery status.
        
        :return: True if battery is OK, False if low, None if unavailable
        :rtype: bool or None
        """
        if self.rtc_available:
            try:
                return not self.rtc.battery_low
            except Exception:
                return None
        return None

    @property
    def power_lost(self):
        """
        Check if power was lost since last access.
        
        :return: True if power was lost, False if not, None if unavailable
        :rtype: bool or None
        """
        if self.rtc_available:
            try:
                return self.rtc.lost_power
            except Exception:
                return None
        return None