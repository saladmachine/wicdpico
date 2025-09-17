# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
CPU Fan Module - PWM Fan Control and RPM Monitoring
===================================================

Provides PWM-based fan speed control and RPM monitoring for cooling management
in the WicdPico system following established architectural patterns.
"""

import time
import json
import board
import pwmio
import digitalio
import analogio
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class CPUFanModule(WicdpicoModule):
    """
    CPU Fan control module for WicdPico system.
    
    Provides PWM fan speed control (0-100%) and RPM monitoring through 
    web dashboard interface. Follows established patterns from DarkBox module.
    """
    
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "CPU Fan Control"
        
        # Fan control state
        self.fan_speed_percent = 50  # Default 50% speed
        self.current_rpm = 0
        self.fan_available = False
        self.pwm_pin = None
        self.tach_pin = None
        
        # RPM measurement state
        self.last_rpm_time = 0
        self.rpm_measurement_interval = 2.0  # seconds
        self.pulse_count = 0
        self.last_pulse_time = 0
        
        self._initialize_fan_hardware()
        
    def _initialize_fan_hardware(self):
        """Initialize PWM output for fan control and tachometer input for RPM sensing."""
        try:
            # Initialize PWM for fan control (GPIO 16)
            self.pwm_pin = pwmio.PWMOut(board.GP16, frequency=25000)
            self.foundation.startup_print("Fan PWM control initialized on GP16")
            
            # Initialize tachometer input for RPM sensing (GPIO 17)
            self.tach_pin = digitalio.DigitalInOut(board.GP17)
            self.tach_pin.direction = digitalio.Direction.INPUT
            self.tach_pin.pull = digitalio.Pull.UP
            self.foundation.startup_print("Fan tachometer initialized on GP17")
            
            # Set initial fan speed
            self.set_fan_speed(self.fan_speed_percent)
            self.fan_available = True
            
        except Exception as e:
            self.foundation.startup_print(f"Fan hardware initialization failed: {e}")
            self.fan_available = False
    
    def set_fan_speed(self, speed_percent):
        """
        Set fan speed as percentage (0-100%).
        
        :param speed_percent: Fan speed percentage (0-100)
        :type speed_percent: int or float
        :return: Success status and message
        :rtype: tuple
        """
        if not self.fan_available:
            return False, "Fan hardware not available"
            
        try:
            # Clamp speed to valid range
            speed_percent = max(0, min(100, speed_percent))
            
            # Convert percentage to PWM duty cycle (0-65535)
            duty_cycle = int((speed_percent / 100.0) * 65535)
            
            self.pwm_pin.duty_cycle = duty_cycle
            self.fan_speed_percent = speed_percent
            
            return True, f"Fan speed set to {speed_percent}%"
            
        except Exception as e:
            return False, f"Failed to set fan speed: {str(e)}"
    
    def get_fan_speed(self):
        """
        Get current fan speed percentage.
        
        :return: Current fan speed percentage
        :rtype: float
        """
        return self.fan_speed_percent
    
    def measure_rpm(self):
        """
        Measure fan RPM using tachometer signal.
        
        Simple pulse counting method over measurement interval.
        
        :return: Current RPM value
        :rtype: int
        """
        if not self.fan_available:
            return 0
            
        current_time = time.monotonic()
        
        # Reset measurement if interval has passed
        if current_time - self.last_rpm_time >= self.rpm_measurement_interval:
            # Calculate RPM from pulse count
            # Assuming 2 pulses per revolution (typical for PC fans)
            pulses_per_revolution = 2
            time_elapsed = current_time - self.last_rpm_time
            
            if time_elapsed > 0:
                # RPM = (pulses / pulses_per_rev) * (60 seconds / time_elapsed)
                self.current_rpm = int((self.pulse_count / pulses_per_revolution) * (60 / time_elapsed))
            
            # Reset for next measurement
            self.pulse_count = 0
            self.last_rpm_time = current_time
        
        return self.current_rpm
    
    def _count_tach_pulse(self):
        """Count tachometer pulses for RPM calculation."""
        if not self.fan_available:
            return
            
        current_time = time.monotonic()
        
        # Simple edge detection (falling edge)
        if not self.tach_pin.value and (current_time - self.last_pulse_time > 0.001):  # Debounce
            self.pulse_count += 1
            self.last_pulse_time = current_time
    
    def get_fan_status(self):
        """
        Get comprehensive fan status information.
        
        :return: Dictionary with fan status data
        :rtype: dict
        """
        return {
            "available": self.fan_available,
            "speed_percent": self.fan_speed_percent,
            "rpm": self.current_rpm,
            "status": "Running" if self.fan_speed_percent > 0 else "Stopped"
        }
    
    def register_routes(self, server):
        """Register HTTP routes for fan control web interface."""
        
        @server.route("/cpu-fan-speed", methods=['GET'])
        def get_fan_speed(request: Request):
            """Handle fan speed query requests."""
            try:
                speed = self.get_fan_speed()
                return Response(request, json.dumps({"speed_percent": speed}), content_type="application/json")
            except Exception as e:
                return Response(request, f"Error getting fan speed: {str(e)}", content_type="text/plain")
        
        @server.route("/cpu-fan-speed", methods=['POST'])
        def set_fan_speed(request: Request):
            """Handle fan speed control requests."""
            try:
                # Parse speed from request body or query parameter
                speed_percent = 50  # default
                
                # Try to get speed from request body (JSON or form data)
                if hasattr(request, 'body') and request.body:
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                        speed_percent = data.get('speed', 50)
                    except:
                        # Fallback to form data or default
                        pass
                
                success, message = self.set_fan_speed(speed_percent)
                
                if success:
                    return Response(request, message, content_type="text/plain")
                else:
                    return Response(request, f"Error: {message}", content_type="text/plain")
                    
            except Exception as e:
                return Response(request, f"Set fan speed error: {str(e)}", content_type="text/plain")
        
        @server.route("/cpu-fan-rpm", methods=['GET'])
        def get_fan_rpm(request: Request):
            """Handle RPM reading requests."""
            try:
                rpm = self.measure_rpm()
                return Response(request, json.dumps({"rpm": rpm}), content_type="application/json")
            except Exception as e:
                return Response(request, f"Error reading RPM: {str(e)}", content_type="text/plain")
        
        @server.route("/cpu-fan-status", methods=['GET'])
        def get_fan_status(request: Request):
            """Handle fan status requests."""
            try:
                status = self.get_fan_status()
                return Response(request, json.dumps(status), content_type="application/json")
            except Exception as e:
                return Response(request, f"Error getting fan status: {str(e)}", content_type="text/plain")
        
        self.foundation.startup_print("CPU Fan routes registered: /cpu-fan-speed, /cpu-fan-rpm, /cpu-fan-status")
    
    def get_dashboard_html(self):
        """
        Generate dashboard HTML widget for fan control.
        
        Follows the same styling and structure patterns as DarkBox module
        for consistency with the rest of the WicdPico dashboard.
        """
        # Get current status for display
        status = self.get_fan_status()
        speed_display = f"{status['speed_percent']:.0f}" if status['available'] else "---"
        rpm_display = f"{status['rpm']}" if status['available'] else "---"
        status_display = status['status'] if status['available'] else "Unavailable"
        
        return f'''
        <div class="module">
            <h3>CPU Fan Control</h3>
            <div style="font-size: 24px; font-weight: bold; text-align: center; padding: 20px; border: 2px solid #007bff; margin: 10px 0;">
                Speed: <span id="fan-speed-value">{speed_display}</span>% | RPM: <span id="fan-rpm-value">{rpm_display}</span>
            </div>
            <div style="display: flex; justify-content: space-around; text-align: center; margin-bottom: 20px;">
                <div class="sensor-reading">
                    <span style="font-weight: bold;">Status</span><br>
                    <span id="fan-status-value" style="font-size: 1.5em;">{status_display}</span>
                </div>
                <div class="sensor-reading">
                    <span style="font-weight: bold;">Power Level</span><br>
                    <span id="fan-power-level" style="font-size: 1.5em;">{"Normal" if status['speed_percent'] < 80 else "High"}</span>
                </div>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Speed Control</h4>
                <div style="margin: 10px 0;">
                    <input type="range" id="fan-speed-slider" min="0" max="100" value="{status['speed_percent']}" 
                           style="width: 100%; margin: 5px 0;" onchange="setFanSpeedSlider(this.value)">
                    <div style="display: flex; justify-content: space-between; font-size: 0.9em; color: #666;">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                    </div>
                </div>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Quick Controls</h4>
                <button id="fan-stop-btn" onclick="setFanSpeed(0)" style="background: #dc3545;">Stop Fan</button>
                <button id="fan-low-btn" onclick="setFanSpeed(25)" style="background: #28a745;">Low (25%)</button>
                <button id="fan-medium-btn" onclick="setFanSpeed(50)" style="background: #007bff;">Medium (50%)</button>
                <button id="fan-high-btn" onclick="setFanSpeed(75)" style="background: #fd7e14;">High (75%)</button>
                <button id="fan-max-btn" onclick="setFanSpeed(100)" style="background: #dc3545;">Max (100%)</button>
            </div>
            
            <div class="control-group">
                <h4 style="margin: 10px 0 5px 0; color: #666;">Monitoring</h4>
                <button id="fan-refresh-btn" onclick="refreshFanStatus()">Refresh Status</button>
                <button id="fan-rpm-btn" onclick="getRPM()">Read RPM</button>
            </div>
            <p id="fan-control-status">Ready for fan control</p>
        </div>

        <script>
        function setFanSpeed(speedPercent) {{
            const btn = event.target;
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Setting...';

            fetch('/cpu-fan-speed', {{
                method: 'POST',
                body: JSON.stringify({{ speed: speedPercent }}),
                headers: {{ 'Content-Type': 'application/json' }}
            }})
                .then(response => response.text())
                .then(result => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('fan-control-status').innerHTML = '<strong>Speed Set:</strong><br>' + result;
                    document.getElementById('fan-control-status').style.background = '#d4edda';
                    document.getElementById('fan-control-status').style.borderLeft = '4px solid #28a745';
                    
                    // Update slider and display
                    document.getElementById('fan-speed-slider').value = speedPercent;
                    document.getElementById('fan-speed-value').textContent = speedPercent;
                    
                    // Update power level indicator
                    const powerLevel = speedPercent < 80 ? 'Normal' : 'High';
                    document.getElementById('fan-power-level').textContent = powerLevel;
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('fan-control-status').innerHTML = '<strong>Control Error:</strong><br>' + error.message;
                    document.getElementById('fan-control-status').style.background = '#f8d7da';
                    document.getElementById('fan-control-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function setFanSpeedSlider(speedPercent) {{
            // Update display immediately for responsive feel
            document.getElementById('fan-speed-value').textContent = speedPercent;
            const powerLevel = speedPercent < 80 ? 'Normal' : 'High';
            document.getElementById('fan-power-level').textContent = powerLevel;
            
            // Set the actual fan speed
            setFanSpeed(speedPercent);
        }}
        
        function getRPM() {{
            const btn = document.getElementById('fan-rpm-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/cpu-fan-rpm', {{ method: 'GET' }})
                .then(response => response.json())
                .then(data => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('fan-rpm-value').textContent = data.rpm;
                    document.getElementById('fan-control-status').innerHTML = '<strong>RPM Reading:</strong><br>' + data.rpm + ' RPM';
                    document.getElementById('fan-control-status').style.background = '#d1ecf1';
                    document.getElementById('fan-control-status').style.borderLeft = '4px solid #17a2b8';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('fan-control-status').innerHTML = '<strong>RPM Error:</strong><br>' + error.message;
                    document.getElementById('fan-control-status').style.background = '#f8d7da';
                    document.getElementById('fan-control-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        function refreshFanStatus() {{
            const btn = document.getElementById('fan-refresh-btn');
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Refreshing...';

            fetch('/cpu-fan-status', {{ method: 'GET' }})
                .then(response => response.json())
                .then(status => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    
                    // Update all displays
                    document.getElementById('fan-speed-value').textContent = status.speed_percent;
                    document.getElementById('fan-rpm-value').textContent = status.rpm;
                    document.getElementById('fan-status-value').textContent = status.status;
                    document.getElementById('fan-speed-slider').value = status.speed_percent;
                    
                    const powerLevel = status.speed_percent < 80 ? 'Normal' : 'High';
                    document.getElementById('fan-power-level').textContent = powerLevel;
                    
                    document.getElementById('fan-control-status').innerHTML = '<strong>Status Updated:</strong><br>Speed: ' + status.speed_percent + '%, RPM: ' + status.rpm + ', Status: ' + status.status;
                    document.getElementById('fan-control-status').style.background = '#d4edda';
                    document.getElementById('fan-control-status').style.borderLeft = '4px solid #28a745';
                }})
                .catch(error => {{
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('fan-control-status').innerHTML = '<strong>Status Error:</strong><br>' + error.message;
                    document.getElementById('fan-control-status').style.background = '#f8d7da';
                    document.getElementById('fan-control-status').style.borderLeft = '4px solid #dc3545';
                }});
        }}
        
        // Auto-refresh RPM every 5 seconds when page is active
        setInterval(function() {{
            if (document.visibilityState === 'visible') {{
                getRPM();
            }}
        }}, 5000);
        </script>
        '''
    
    def update(self):
        """
        Called from main loop for periodic tasks.
        
        Handles tachometer pulse counting for RPM measurement.
        """
        if self.fan_available:
            self._count_tach_pulse()
    
    def cleanup(self):
        """Cleanup on shutdown."""
        if self.fan_available and self.pwm_pin:
            try:
                # Stop the fan on shutdown
                self.pwm_pin.duty_cycle = 0
                self.foundation.startup_print("CPU fan stopped on shutdown")
            except:
                pass