# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT
#
# Architectural note (2025-09-16):
# - Removed the dashboard route definition (`@foundation.server.route("/", ...)`) and its handler (`serve_dashboard`)
#   from this module to comply with project architecture.md.
# - This module now only registers REST API endpoints and provides dashboard widget HTML via get_dashboard_html().
# - No other logic was changed.

"""
DarkBox Module - Simple Implementation
Combines CO2/temp/humidity monitoring (SCD41) with light detection (BH1750)
for dark box growth chamber applications following WicdPico simple patterns.
"""

import time
import json
import board
import busio
import storage
import adafruit_sdcard
import digitalio
import analogio
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
from foundation_core import shut_down_wifi_and_sleep


# AP timeout state variables (ensure these are shared with your AP logic)
timeout_disabled = False
ap_is_off_and_logged = False
last_activity_time = time.monotonic()

# Try to import SCD4x library
try:
    import adafruit_scd4x
    SCD4X_AVAILABLE = True
except ImportError:
    SCD4X_AVAILABLE = False

# Try to import BH1750 library
try:
    import adafruit_bh1750
    BH1750_AVAILABLE = True
except ImportError:
    BH1750_AVAILABLE = False

# Try to import RTC library for timestamps
try:
    from adafruit_pcf8523.pcf8523 import PCF8523
    RTC_AVAILABLE = True
except ImportError:
    RTC_AVAILABLE = False

class DarkBoxModule(WicdpicoModule):
    USB_THRESHOLD = 4.4
    BATTERY_THRESHOLD = 4.2

    """Simple DarkBox module combining SCD41 and BH1750 simple patterns."""
    
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "DarkBox Monitor"
        
        # Sensor state
        self.scd41_available = False
        self.last_co2 = None
        self.last_temp = None
        self.last_humidity = None
        self.scd41 = None
        
        self.bh1750_available = False
        self.last_lux = None
        self.bh1750 = None
        
        self.rtc_available = False
        self.rtc = None
        
        self.light_events = []
        self.current_event = None
        self.dark_count = 0
        self.last_light_check = 0
        
        self.sd_mounted = False
        
        self.vsys_adc = analogio.AnalogIn(board.A3)  # VSYS voltage monitor (ADC3/GP29)

        self.power_state = "UNKNOWN"

        self._initialize_sensors()
        self._initialize_sd_card()
        
        # Log initial power state after SD card is mounted
        voltage = self.get_voltage()
        if voltage > self.USB_THRESHOLD:
            self.power_state = "USB"
        elif voltage < self.BATTERY_THRESHOLD:
            self.power_state = "BATTERY"
        self._log_power_event_to_sd("startup", "UNKNOWN", self.power_state, voltage)
        
    def _initialize_sensors(self):
        """Initialize I2C and sensors."""
        try:
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.foundation.startup_print("I2C bus initialized (GP5=SCL, GP4=SDA)")

            if SCD4X_AVAILABLE:
                try:
                    self.scd41 = adafruit_scd4x.SCD4X(self.i2c)
                    self.scd41_available = True
                    self.foundation.startup_print("SCD41 initialized successfully")
                except Exception as e:
                    self.scd41_available = False
                    self.foundation.startup_print(f"SCD41 init failed: {e}")
            else:
                self.foundation.startup_print("SCD41 library not found.")
            
            if BH1750_AVAILABLE:
                try:
                    self.bh1750 = adafruit_bh1750.BH1750(self.i2c)
                    self.bh1750_available = True
                    self.foundation.startup_print("BH1750 initialized successfully")
                except Exception as e:
                    self.bh1750_available = False
                    self.foundation.startup_print(f"BH1750 init failed: {e}")
            else:
                self.foundation.startup_print("BH1750 library not found.")

            if RTC_AVAILABLE:
                try:
                    self.rtc = PCF8523(self.i2c)
                    self.rtc_available = True
                    self.foundation.startup_print("RTC initialized successfully")
                except Exception as e:
                    self.rtc_available = False
                    self.foundation.startup_print(f"RTC init failed: {e}")
            else:
                self.foundation.startup_print("RTC library not found.")
                
        except Exception as e:
            self.foundation.startup_print(f"Sensor initialization failed: {e}")

    def get_environment_reading(self):
        """Get CO2, temp, humidity readings from SCD41."""
        if not self.scd41_available:
            return {"success": False, "error": "SCD41 sensor not available"}
        
        try:
            self.scd41.measure_single_shot()
            time.sleep(5)
            
            co2_ppm = self.scd41.CO2
            temp_c = self.scd41.temperature
            humidity = self.scd41.relative_humidity

            if co2_ppm is None:
                return {"success": False, "error": "Sensor warming up"}
            
            self.last_co2 = co2_ppm
            self.last_temp = temp_c
            self.last_humidity = humidity
            
            return {"success": True, "co2": int(co2_ppm), "temp": temp_c, "humidity": humidity}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_light_reading(self):
        """Get light level reading from BH1750."""
        if not self.bh1750_available:
            return {"success": False, "error": "BH1750 sensor not available"}
        
        try:
            lux_value = self.bh1750.lux
            if lux_value is None:
                return {"success": False, "error": "Sensor warming up"}
            
            self.last_lux = lux_value
            return {"success": True, "lux": round(lux_value, 1)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_timestamp(self):
        """Get formatted timestamp string."""
        if self.rtc_available:
            dt = self.rtc.datetime
            return f"{dt.tm_year:04d}-{dt.tm_mon:02d}-{dt.tm_mday:02d} {dt.tm_hour:02d}:{dt.tm_min:02d}:{dt.tm_sec:02d}"
        else:
            return f"uptime_{time.monotonic():.1f}s"

    def _check_light_events(self):
        """KISS light event detection - called every loop."""
        current_time = time.monotonic()
        
        if current_time - self.last_light_check < 0.1:
            return
        self.last_light_check = current_time
        
        if not self.bh1750_available:
            return
            
        try:
            lux = self.bh1750.lux
            self.last_lux = lux
            
            if lux > 5:
                self.dark_count = 0
                if self.current_event is None:
                    timestamp = self._get_timestamp()
                    self.current_event = {'start_time': timestamp, 'start_mono': current_time, 'peak_lux': lux}
                    self.foundation.startup_print(f"Light event started: {lux} lux at {timestamp}")
                elif lux > self.current_event['peak_lux']:
                    self.current_event['peak_lux'] = lux
            else:
                if self.current_event is not None:
                    self.dark_count += 1
                    if self.dark_count >= 3:
                        timestamp = self._get_timestamp()
                        duration = current_time - self.current_event['start_mono']
                        event = (self.current_event['start_time'], timestamp, self.current_event['peak_lux'], duration)
                        self.light_events.append(event)
                        if len(self.light_events) > 100: self.light_events.pop(0)
                        self.foundation.startup_print(f"Light event ended: {duration:.1f}s duration, peak {self.current_event['peak_lux']:.1f} lux")
                        self._log_event_to_sd(event)
                        self.current_event = None
                        self.dark_count = 0
        except Exception:
            pass

    def _log_event_to_sd(self, event):
        """Log event to SD card - simple append."""
        try:
            with open("/sd/light_events.csv", "a") as f:
                f.write(f"{event[0]},{event[1]},{event[2]:.1f},{event[3]:.1f}\n")
        except:
            pass
    
    def log_sensor_data(self):
        """Log current sensor readings to CSV file with timestamp."""
        try:
            env_data = self.get_environment_reading()
            light_data = self.get_light_reading()
            timestamp = self._get_timestamp()
            
            try:
                with open("/sd/darkbox_data.csv", "r"): pass
            except:
                with open("/sd/darkbox_data.csv", "w") as f:
                    f.write("timestamp,co2_ppm,temp_c,humidity_percent,light_lux\n")
            
            with open("/sd/darkbox_data.csv", "a") as f:
                co2 = env_data.get('co2', '') if env_data.get('success') else ''
                temp = env_data.get('temp', '') if env_data.get('success') else ''
                humidity = env_data.get('humidity', '') if env_data.get('success') else ''
                lux = light_data.get('lux', '') if light_data.get('success') else ''
                f.write(f"{timestamp},{co2},{temp},{humidity},{lux}\n")
            
            return {"success": True, "message": f"Data logged at {timestamp}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def force_calibration(self, co2_ppm):
        """Calibrate SCD41 to known CO2 level."""
        if not self.scd41_available:
            return False, "SCD41 sensor not available"
        try:
            self.scd41.force_calibration(co2_ppm)
            return True, f"Calibrated to {co2_ppm} ppm"
        except Exception as e:
            return False, str(e)

    def get_voltage(self):
        # VSYS is divided internally, so multiply by 3 for Pico W
        return round((self.vsys_adc.value * 3.3 / 65536) * 3, 2)

    def register_routes(self, server):
        """Register HTTP routes for both sensors."""
        @server.route("/darkbox-environment", methods=['POST'])
        def environment_reading(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            reading = self.get_environment_reading()
            if reading['success']: reading['temp_f'] = reading['temp'] * 1.8 + 32
            return Response(request, json.dumps(reading), content_type="application/json")

        @server.route("/darkbox-light", methods=['POST'])
        def light_reading(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            reading = self.get_light_reading()
            return Response(request, json.dumps(reading), content_type="application/json")

        @server.route("/darkbox-calibration", methods=['POST'])
        def calibration(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            success, message = self.force_calibration(425)
            return Response(request, message, content_type="text/plain")

        @server.route("/darkbox-clear-events", methods=['POST'])
        def clear_events(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            count = len(self.light_events)
            self.light_events = []
            if self.current_event: self.current_event = None
            return Response(request, f"Cleared {count} light events", content_type="text/plain")
        
        @server.route("/calibration", methods=['GET'])
        def calibration_page(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            html_content = self.get_calibration_html()
            full_page = self.foundation.templates.render_page("CO2 Calibration", html_content)
            return Response(request, full_page, content_type="text/html")
            
        @server.route("/darkbox-log", methods=['POST'])
        def log_data(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            result = self.log_sensor_data()
            return Response(request, result.get('message', result.get('error')), content_type="text/plain")

        @server.route("/darkbox-read-log", methods=['GET'])
        def read_log(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            if not self.sd_mounted:
                return Response(request, "SD card not mounted.", content_type="text/plain")
            try:
                with open("/sd/darkbox_data.csv", "r") as f:
                    log_content = f.read()
                return Response(request, log_content, content_type="text/plain")
            except Exception as e:
                return Response(request, f"Error reading log: {e}", content_type="text/plain")

        @server.route("/darkbox-read-light-log", methods=['GET'])
        def read_light_log(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            if not self.sd_mounted:
                return Response(request, "SD card not mounted.", content_type="text/plain")
            try:
                with open("/sd/light_events.csv", "r") as f:
                    log_content = f.read()
                return Response(request, log_content, content_type="text/plain")
            except Exception as e:
                return Response(request, f"Error reading light log: {e}", content_type="text/plain")

        @server.route("/power-voltage", methods=['POST'])
        def power_voltage(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            voltage = self.get_voltage()
            return Response(request, str(voltage), content_type="text/plain")

        @server.route("/power-source", methods=['POST'])
        def power_source(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            return Response(request, self.power_state, content_type="text/plain")

        @server.route("/power-log", methods=['GET'])
        def power_log(request: Request):
            global last_activity_time
            last_activity_time = time.monotonic()
            if not self.sd_mounted:
                return Response(request, "SD card not mounted.", content_type="text/plain")
            try:
                with open("/sd/power_events.csv", "r") as f:
                    log_content = f.read()
                return Response(request, log_content, content_type="text/plain")
            except Exception as e:
                return Response(request, f"Error reading power log: {e}", content_type="text/plain")

        @server.route("/toggle-hotspot-control", methods=['POST'])
        def toggle_hotspot_control(request: Request):
            global timeout_disabled, ap_is_off_and_logged
            if not timeout_disabled:
                timeout_disabled = True
                return Response(request, "Automatic timeout disabled. Hotspot will remain open.", content_type="text/plain")
            else:
                # If already disabled, user wants to close the hotspot now
                shut_down_wifi_and_sleep()
                ap_is_off_and_logged = True
                return Response(request, "Hotspot closed. Power cycle required to restart.", content_type="text/plain")

        @server.route("/get-hotspot-status", methods=['GET'])
        def get_hotspot_status(request: Request):
            global timeout_disabled
            return Response(request, json.dumps({"timeout_disabled": timeout_disabled}), content_type="application/json")

    def _log_power_event_to_sd(self, event_type, prev_state, new_state, voltage):
        """Log power event to SD card."""
        if not self.sd_mounted:
            return
        timestamp = self._get_timestamp()
        try:
            with open("/sd/power_events.csv", "a") as f:
                f.write(f"{timestamp},{event_type},{prev_state},{new_state},{voltage:.2f}\n")
        except Exception as e:
            print(f"✗ Power event log error: {e}")

    def update(self):
        """Called from main loop."""
        self._check_light_events()
        self._check_power_state()

    def _check_power_state(self):
        voltage = self.get_voltage()
        prev_state = self.power_state
        if self.power_state != "USB" and voltage > self.USB_THRESHOLD:
            self.power_state = "USB"
            print("Switched to USB power")
            self._log_power_event_to_sd("transition", prev_state, self.power_state, voltage)
        elif self.power_state != "BATTERY" and voltage < self.BATTERY_THRESHOLD:
            self.power_state = "BATTERY"
            print("Switched to battery power")
            self._log_power_event_to_sd("transition", prev_state, self.power_state, voltage)
        # If voltage is between thresholds, hold previous state

    def cleanup(self):
        """Cleanup on shutdown."""
        pass

    def get_dashboard_html(self):
        """Dashboard with cards: environment, light, power, and Wi-Fi hotspot timeout."""
        co2_display = "---" if self.last_co2 is None else f"{self.last_co2}"
        temp_display = "---" if self.last_temp is None else f"{self.last_temp:.1f}"
        humidity_display = "---" if self.last_humidity is None else f"{self.last_humidity:.1f}"
        lux_display = "---" if self.last_lux is None else f"{self.last_lux:.1f}"
        
        power_card = f"""
        <div class="module" id="power-monitor">
            <h3>Power Monitoring</h3>
            <div>
                <button onclick="fetch('/power-voltage', {{method:'POST'}})
                    .then(r=>r.text())
                    .then(v=>document.getElementById('power-voltage').innerText = v + ' V')">
                    Get Voltage
                </button>
                <span id="power-voltage" style="margin-left:1em;">--</span>
                <button onclick="fetch('/power-source', {{method:'POST'}})
                    .then(r=>r.text())
                    .then(s=>document.getElementById('power-state').innerText = s)">
                    Get Power Source
                </button>
                <button onclick="viewPowerLog()">View Log</button>
                <div>Power Source: <span id="power-state">{self.power_state}</span></div>
            </div>
        </div>
        <script>
        function viewPowerLog() {{
            fetch('/power-log')
                .then(response => response.text())
                .then(log => {{
                    alert('Power Event Log:\\n' + log);
                }})
                .catch(error => {{
                    alert('Error reading power log: ' + error.message);
                }});
        }}
        </script>
        """

        # No outer card/wrapper here, just the inner cards
        return f'''
        <div class="module">
            <h3>Environment Sensor</h3>
            <div style="font-size: 24px; font-weight: bold; text-align: center; padding: 20px; border: 2px solid #007bff; margin: 10px 0;">
                CO2: <span id="co2-value">{co2_display}</span> ppm
            </div>
            <div style="display: flex; justify-content: space-around; text-align: center; margin-bottom: 20px;">
                <div class="sensor-reading">
                    <span style="font-weight: bold;">Temperature</span><br>
                    <span id="temp-value" style="font-size: 1.5em;">{temp_display}</span> C
                </div>
                <div class="sensor-reading">
                    <span style="font-weight: bold;">Humidity</span><br>
                    <span id="humidity-value" style="font-size: 1.5em;">{humidity_display}</span> %
                </div>
            </div>
            <div class="control-group">
                <button id="environment-btn" onclick="getEnvironmentReading()">Get Reading</button>
                <button onclick="window.location.href='/calibration'">Calibration</button>
                <button id="log-btn" onclick="logData()">Log to SD</button>
                <button id="read-log-btn" onclick="readLogFile()">Read Log File</button>
            </div>
            <p id="environment-status">Ready for measurements</p>
        </div>
        <div class="module">
            <h3>Light Status</h3>
            <div style="font-size: 24px; font-weight: bold; text-align: center; padding: 20px; border: 2px solid #28a745; margin: 10px 0;">
                Light: <span id="lux-value">{lux_display}</span> lux
            </div>
            <div class="control-group">
                <button id="light-btn" onclick="getLightReading()">Read Lux</button>
                <button id="read-light-log-btn" onclick="readLightLogFile()">Read Light Log</button>
                <button id="clear-events-btn" onclick="clearLightEvents()">Clear Light Events</button>
            </div>
            <p id="light-status">Ready for measurements</p>
        </div>
        {power_card}
        <div class="module" id="hotspot-timeout-card">
          <h3>Wi-Fi Hotspot Timeout</h3>
          <p id="hotspot-timeout-desc">
            By default, the Wi-Fi hotspot (AP) will shut down after a period of inactivity for security and power saving.
            You can disable this timeout to keep the AP open, or manually close it now.
          </p>
          <button id="hotspot-btn" onclick="toggleHotspotControl()">Loading...</button>
          <div id="hotspot-result"></div>
        </div>
        <script>
        function viewPowerLog() {{
            fetch('/power-log')
                .then(response => response.text())
                .then(log => {{
                    alert('Power Event Log:\\n' + log);
                }})
                .catch(error => {{
                    alert('Error reading power log: ' + error.message);
                }});
        }}

        // Wi-Fi Hotspot Timeout Card Logic (from picowide)
        function updateHotspotButton() {{
            fetch('/get-hotspot-status')
                .then(response => response.json())
                .then(status => {{
                    const btn = document.getElementById('hotspot-btn');
                    if (status.timeout_disabled) {{
                        btn.textContent = 'Close Hotspot';
                    }} else {{
                        btn.textContent = 'Keep Hotspot Open';
                    }}
                }})
                .catch(() => {{
                    document.getElementById('hotspot-btn').textContent = 'Unavailable';
                }});
        }}

        function toggleHotspotControl() {{
            const btn = document.getElementById('hotspot-btn');
            if (btn.textContent === 'Close Hotspot') {{
                // Show confirmation before closing
                if (confirm("Are you sure you want to close the Wi-Fi hotspot? A physical power cycle will be required to restart it.")) {{
                    fetch('/toggle-hotspot-control', {{ method: 'POST' }})
                        .then(response => response.text())
                        .then(result => {{
                            document.getElementById('hotspot-result').textContent = result;
                            btn.disabled = true;
                        }})
                        .catch(error => {{
                            document.getElementById('hotspot-result').textContent = 'Error: ' + error.message;
                        }});
                }}
            }} else {{
                fetch('/toggle-hotspot-control', {{ method: 'POST' }})
                    .then(response => response.text())
                    .then(result => {{
                        btn.textContent = 'Close Hotspot';
                        document.getElementById('hotspot-result').textContent = 'Automatic timeout disabled. Hotspot will remain open.';
                    }})
                    .catch(error => {{
                        document.getElementById('hotspot-result').textContent = 'Error: ' + error.message;
                    }});
            }}
        }}

        // Initialize button state on page load
        document.addEventListener('DOMContentLoaded', updateHotspotButton);

        function getEnvironmentReading() {{
            const btn = document.getElementById('environment-btn');
            const statusEl = document.getElementById('environment-status');
            btn.disabled = true;
            btn.textContent = 'Reading...';
            statusEl.textContent = 'Measuring... This takes about 5 seconds.';
            fetch('/darkbox-environment', {{ method: 'POST' }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        document.getElementById('co2-value').textContent = data.co2;
                        document.getElementById('temp-value').textContent = data.temp.toFixed(1);
                        document.getElementById('humidity-value').textContent = data.humidity.toFixed(1);
                        statusEl.textContent = 'Last reading successful.';
                    }} else {{
                        statusEl.textContent = 'Error: ' + data.error;
                    }}
                }}).finally(() => {{ btn.disabled = false; btn.textContent = 'Get Reading'; }});
        }}
        function getLightReading() {{
            const btn = document.getElementById('light-btn');
            const statusEl = document.getElementById('light-status');
            btn.disabled = true;
            btn.textContent = 'Reading...';
            statusEl.textContent = 'Reading light level...';
            fetch('/darkbox-light', {{ method: 'POST' }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        document.getElementById('lux-value').textContent = data.lux;
                        statusEl.textContent = 'Last reading successful.';
                    }} else {{
                        statusEl.textContent = 'Error: ' + data.error;
                    }}
                }}).finally(() => {{ btn.disabled = false; btn.textContent = 'Read Lux'; }});
        }}
        function logData() {{
            const btn = document.getElementById('log-btn');
            const statusEl = document.getElementById('environment-status');
            btn.disabled = true;
            btn.textContent = 'Logging...';
            statusEl.textContent = 'Logging data to SD card...';
            fetch('/darkbox-log', {{ method: 'POST' }})
                .then(response => response.text())
                .then(message => {{ statusEl.textContent = message; }})
                .catch(error => {{ statusEl.textContent = 'Log Error: ' + error.message; }})
                .finally(() => {{ btn.disabled = false; btn.textContent = 'Log to SD'; }});
        }}
        function readLogFile() {{
            const btn = document.getElementById('read-log-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';
            fetch('/darkbox-read-log')
                .then(response => response.text())
                .then(log => {{
                    alert('Log File Contents:\\n' + log);
                }})
                .catch(error => {{
                    alert('Error reading log: ' + error.message);
                }})
                .finally(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Read Log File';
                }});
        }}
        function clearLightEvents() {{
            const btn = document.getElementById('clear-events-btn');
            btn.disabled = true;
            btn.textContent = 'Clearing...';
            fetch('/darkbox-clear-events', {{ method: 'POST' }})
                .then(response => response.text())
                .then(message => {{
                    alert(message);
                }})
                .catch(error => {{
                    alert('Error clearing events: ' + error.message);
                }})
                .finally(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Clear Light Events';
                }});
        }}
        function readLightLogFile() {{
            const btn = document.getElementById('read-light-log-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';
            fetch('/darkbox-read-light-log')
                .then(response => response.text())
                .then(log => {{
                    alert('Light Log File Contents:\\n' + log);
                }})
                .catch(error => {{
                    alert('Error reading light log: ' + error.message);
                }})
                .finally(() => {{
                    btn.disabled = false;
                    btn.textContent = 'Read Light Log';
                }});
        }}
        function toggleHotspotControl() {{
            const btn = document.getElementById('hotspot-btn');
            const resultEl = document.getElementById('hotspot-result');
            btn.disabled = true;
            btn.textContent = 'Toggling...';
            fetch('/toggle-hotspot-control', {{ method: 'POST' }})
                .then(response => response.text())
                .then(message => {{
                    resultEl.textContent = message;
                    btn.textContent = 'Close Hotspot';
                }})
                .catch(error => {{
                    resultEl.textContent = 'Error: ' + error.message;
                    btn.textContent = 'Error';
                }})
                .finally(() => {{
                    btn.disabled = false;
                }});
        }}
        </script>
        '''

    def get_calibration_html(self):
        """Returns an HTML fragment for the calibration page content."""
        return '''
        <div class="module">
            <h3>CO2 Sensor Calibration</h3>
            <div class="status" style="background: #fff3cd; border-left: 4px solid #ffc107;">
                <strong>Instructions:</strong>
                <ol>
                    <li>Take the device outside, away from any CO2 sources (like vents or people).</li>
                    <li>Allow 5-10 minutes for the sensor to fully stabilize with the outdoor air.</li>
                    <li>Click the calibrate button below.</li>
                </ol>
            </div>
            <div class="control-group">
                <button onclick="calibrate()">Calibrate to 425ppm</button>
                <button onclick="window.location.href='/'" style="background: #6c757d;">Return to Dashboard</button>
            </div>
            <p id="calibration-status">Ready for calibration.</p>
        </div>
        <script>
        function calibrate() {
            if (confirm('This will calibrate the sensor to an assumed outdoor air level of 425ppm. Proceed?')) {
                const statusEl = document.getElementById('calibration-status');
                statusEl.textContent = 'Calibrating... Please wait.';
                fetch('/darkbox-calibration', {method: 'POST'})
                    .then(response => response.text())
                    .then(result => {
                        statusEl.textContent = 'Calibration Result: ' + result;
                        alert('Calibration Result: ' + result);
                    })
                    .catch(error => {
                        statusEl.textContent = 'Error: ' + error.message;
                        alert('Error: ' + error.message);
                    });
            }
        }
        </script>
        '''

    def _initialize_sd_card(self):
        """Initialize and mount SD card using PicoBell Adalogger SPI pins."""
        try:
            spi = busio.SPI(board.GP18, board.GP19, board.GP16)  # SCK, MOSI, MISO
            cs = digitalio.DigitalInOut(board.GP17)  # Chip Select as DigitalInOut
            self.sdcard = adafruit_sdcard.SDCard(spi, cs)
            self.vfs = storage.VfsFat(self.sdcard)
            storage.mount(self.vfs, "/sd")
            self.sd_mounted = True
            print("✓ SD card mounted successfully to /sd")
        except Exception as e:
            self.sd_mounted = False
            print(f"✗ SD card mounting failed: {e}")

    def get_sd_storage_info(self):
        """Return SD card storage info if mounted."""
        if not self.sd_mounted:
            return None
        try:
            import os
            statvfs = os.statvfs("/sd")
            total_mb = (statvfs[2] * statvfs[0]) / (1024 * 1024)
            free_mb = (statvfs[3] * statvfs[0]) / (1024 * 1024)
            return {"total_mb": int(total_mb), "free_mb": int(free_mb)}
        except Exception as e:
            print(f"✗ SD card info error: {e}")
            return None

    def log_to_sd(self, data):
        """Log data to SD card if mounted."""
        if not self.sd_mounted:
            print("✗ SD card not mounted, cannot log data.")
            return False
        try:
            with open("/sd/darkbox_log.csv", "a") as f:
                f.write(data + "\n")
            print("✓ Logged to SD card.")
            return True
        except Exception as e:
            print(f"✗ SD card write error: {e}")
            return False

    def get_html_template(self):
        # Refactored Files card: only List CSV Files and Download CSV buttons
        return """
        <h2>Files</h2>
        <button onclick="showCsvList()">List CSV Files</button>
        <div id="csv-list" style="margin-bottom: 20px; display:none;"></div>
        <button onclick="showDownloadCsvList()">Download CSV</button>
        <div id="download-csv-list" style="margin-bottom: 20px; display:none;"></div>
        <script>
        function fetchCsvFiles(callback) {
            fetch('/monitor/list_csv', { method: 'GET' })
                .then(response => response.text())
                .then(result => {
                    const files = result.split(',').map(f => f.trim()).filter(f => f !== "");
                    callback(files);
                });
        }
        function showCsvList() {
            fetchCsvFiles(function(files) {
                const csvListDiv = document.getElementById('csv-list');
                if (files.length === 0) {
                    csvListDiv.innerHTML = "<p>No CSV files found.</p>";
                } else {
                    let html = "<ul style='font-size:1.1em;'>";
                    files.forEach(function(fname) {
                        html += "<li>" + fname + "</li>";
                    });
                    html += "</ul>";
                    csvListDiv.innerHTML = html;
                }
                csvListDiv.style.display = 'block';
                document.getElementById('download-csv-list').style.display = 'none';
            });
        }
        function showDownloadCsvList() {
            fetchCsvFiles(function(files) {
                const downloadDiv = document.getElementById('download-csv-list');
                if (files.length === 0) {
                    downloadDiv.innerHTML = "<p>No CSV files found.</p>";
                } else {
                    let html = "<ul style='font-size:1.1em;'>";
                    files.forEach(function(fname) {
                        html += "<li><a href='/monitor/download?file=" + encodeURIComponent(fname) +
                                "' download style='text-decoration:none;'>" +
                                fname + " &#x1F4E5;</a></li>";
                    });
                    html += "</ul>";
                    downloadDiv.innerHTML = html;
                }
                downloadDiv.style.display = 'block';
                document.getElementById('csv-list').style.display = 'none';
            });
        }
        </script>
        """

    def update(self):
        """Called from main loop."""
        self._check_light_events()
        self._check_power_state()

    def cleanup(self):
        """Cleanup on shutdown."""
        pass

