# module_scd41.py (Fix: All 'Run' buttons work, no server errors, all actions robust)
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import time
import adafruit_scd4x
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response

class SCD41Module(WicdpicoModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "SCD41 CO2 Sensor"
        self.foundation = foundation
        self.i2c = self.foundation.i2c
        self.scd41 = None
        self.sensor_available = False
        self.last_reading_time = 0
        self.last_co2 = None
        self.last_temp = None
        self.last_humidity = None
        self.sensor_serial = "N/A"
        self.status_message = "Initializing..."
        self.last_error = None
        self._initialize_sensor()
        self.foundation.startup_print("SCD41 module created. Status: '{}'".format(self.status_message))

    def _initialize_sensor(self):
        if not self.i2c:
            self.status_message = "Error: I2C Not Available"
            self.last_error = "Foundation failed to provide I2C bus."
            self.sensor_available = False
            return
        try:
            self.scd41 = adafruit_scd4x.SCD4X(self.i2c)
            serial_num = self.scd41.serial_number
            self.sensor_serial = "{:04X}-{:04X}-{:04X}".format(serial_num[0], serial_num[1], serial_num[2])
            self.sensor_available = True
            self.status_message = "Ready (Single-Shot Mode)"
        except Exception as e:
            self.sensor_available = False
            self.last_error = "SCD41 initialization failed: {}".format(e)
            self.status_message = "Error: Not Found"

    def get_sensor_reading(self):
        if not self.sensor_available:
            return {"success": False, "error": "Sensor not available"}
        try:
            self.scd41.measure_single_shot()
            time.sleep(5)
            co2_ppm = self.scd41.CO2
            temp_c = round(self.scd41.temperature, 1)
            humidity = round(self.scd41.relative_humidity, 1)
            self.last_co2 = int(co2_ppm)
            self.last_temp = temp_c
            self.last_humidity = humidity
            self.last_reading_time = time.monotonic()
            return { "success": True, "co2": self.last_co2, "temperature": temp_c, "humidity": humidity }
        except Exception as e:
            self.last_error = "Reading failed: {}".format(e)
            return {"success": False, "error": self.last_error}

    def set_altitude(self, altitude):
        if not self.sensor_available:
            return False, "Sensor not available"
        try:
            self.scd41.altitude = altitude
            return True, "Altitude set to {}m".format(altitude)
        except Exception as e:
            return False, str(e)

    def _get_all_properties(self):
        props = {}
        if not self.sensor_available:
            return props
        try:
            props["CO2"] = self.scd41.CO2
        except Exception:
            props["CO2"] = None
        try:
            props["temperature"] = self.scd41.temperature
        except Exception:
            props["temperature"] = None
        try:
            props["relative_humidity"] = self.scd41.relative_humidity
        except Exception:
            props["relative_humidity"] = None
        try:
            props["serial_number"] = "-".join(["{:04X}".format(x) for x in self.scd41.serial_number])
        except Exception:
            props["serial_number"] = "N/A"
        try:
            props["altitude"] = self.scd41.altitude
        except Exception:
            props["altitude"] = None
        try:
            props["ambient_pressure"] = self.scd41.ambient_pressure
        except Exception:
            props["ambient_pressure"] = None
        try:
            props["temperature_offset"] = self.scd41.temperature_offset
        except Exception:
            props["temperature_offset"] = None
        try:
            props["self_calibration_enabled"] = self.scd41.self_calibration_enabled
        except Exception:
            props["self_calibration_enabled"] = None
        try:
            props["target_co2"] = self.scd41.target_co2
        except Exception:
            props["target_co2"] = None
        return props

    def _set_property(self, prop, value):
        try:
            if prop == "altitude":
                self.scd41.altitude = int(value)
                return True, "Altitude set"
            elif prop == "ambient_pressure":
                self.scd41.ambient_pressure = int(value)
                return True, "Ambient pressure set"
            elif prop == "temperature_offset":
                self.scd41.temperature_offset = float(value)
                return True, "Temperature offset set"
            elif prop == "self_calibration_enabled":
                self.scd41.self_calibration_enabled = bool(int(value))
                return True, "Self calibration set"
            elif prop == "target_co2":
                self.scd41.target_co2 = int(value)
                return True, "Target CO2 set"
            else:
                return False, "Unknown property"
        except Exception as e:
            return False, str(e)

    def _call_action(self, action, value=None):
        try:
            # Only require value for actions that truly need it
            if action == "measure_single_shot":
                self.scd41.measure_single_shot()
                time.sleep(5)
                return True, "Single-shot measurement complete"
            elif action == "start_periodic_measurement":
                self.scd41.start_periodic_measurement()
                return True, "Started periodic measurement"
            elif action == "start_low_periodic_measurement":
                self.scd41.start_low_periodic_measurement()
                return True, "Started low periodic measurement"
            elif action == "stop_periodic_measurement":
                self.scd41.stop_periodic_measurement()
                return True, "Stopped periodic measurement"
            elif action == "factory_reset":
                self.scd41.factory_reset()
                return True, "Factory reset complete"
            elif action == "reinit":
                self.scd41.reinit()
                return True, "Sensor re-initialized"
            elif action == "self_test":
                result = self.scd41.self_test()
                return True, "Self test result: {}".format(result)
            elif action == "persist_settings":
                self.scd41.persist_settings()
                return True, "Settings persisted"
            elif action == "force_calibration":
                if value is None or value == "":
                    return False, "No CO2 ppm provided"
                self.scd41.force_calibration(int(value))
                return True, "Forced calibration done"
            elif action == "set_ambient_pressure":
                if value is None or value == "":
                    return False, "No pressure value"
                self.scd41.set_ambient_pressure(int(value))
                return True, "Ambient pressure set"
            else:
                return False, "Unknown action"
        except Exception as e:
            return False, str(e)

    def register_routes(self, server):
        @server.route("/scd41/read", methods=['POST'])
        def read_route(request: Request):
            result_dict = self.get_sensor_reading()
            if result_dict.get("success"):
                response_text = "CO2: {} ppm, Temp: {}°C, RH: {}%".format(
                    result_dict['co2'], result_dict['temperature'], result_dict['humidity']
                )
                return Response(request, response_text, content_type="text/plain")
            else:
                error_msg = result_dict.get('error', 'Unknown error')
                return Response(request, "Failed: {}".format(error_msg), content_type="text/plain")
        self.foundation.startup_print("SCD41 route '/scd41/read' registered.")

        @server.route("/scd41/details", methods=['GET', 'POST'])
        def details_route(request: Request):
            msg = ""
            try:
                if request.method == "POST":
                    form = request.form
                    if "set_property" in form:
                        prop = form.get("property")
                        value = form.get("value")
                        ok, msg = self._set_property(prop, value)
                        if ok:
                            msg = "Set {} to {}".format(prop, value)
                        else:
                            msg = "Failed to set {}: {}".format(prop, msg)
                    elif "call_action" in form:
                        action = form.get("action")
                        # Only pass value if present and non-empty
                        value = form.get("value") if ("value" in form and form.get("value") != "") else None
                        ok, msg = self._call_action(action, value)
                        if ok:
                            msg = "Action '{}' succeeded: {}".format(action, msg)
                        else:
                            msg = "Failed to run action '{}': {}".format(action, msg)
            except Exception as e:
                msg = "Internal error: {}".format(e)
            html = self.get_details_html(message=msg)
            return Response(request, html, content_type="text/html")
        self.foundation.startup_print("SCD41 route '/scd41/details' registered.")

    def get_dashboard_html(self):
        status_color = "#28a745" if self.sensor_available else "#dc3545"
        error_html = "<br><span class=\"error-text\"><strong>Error:</strong> {}</span>".format(self.last_error) if self.last_error else ""
        if self.last_co2 is not None:
            age = time.monotonic() - self.last_reading_time
            last_reading_text = "<strong>{} ppm</strong>, {}°C, {}% RH ({}s ago)".format(
                self.last_co2, self.last_temp, self.last_humidity, int(age)
            )
        else:
            last_reading_text = "No readings yet"
        return """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
    margin: 0;
    padding: 0;
    background: #f3f3f4;
}}
.module {{
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 18px 20px;
    margin: 10px auto;
    max-width: 420px;
    background: #fcfcfd;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}}
.status {{
    border-left: 6px solid {status_color};
    padding-left: 12px;
    margin-bottom: 10px;
}}
.error-text {{
    color: #dc3545;
}}
.full-btn {{
    margin-top: 12px;
    width: 100%;
    padding: 12px;
    font-size: 1.05em;
    border-radius: 4px;
    background-color: #007bff;
    color: #fff;
    border: none;
}}
.full-btn:active {{
    background-color: #0056b3;
}}
@media (max-width: 520px) {{
    .module {{
        padding: 12px 3vw;
        max-width: 98vw;
    }}
    .full-btn {{
        font-size: 1.05em;
    }}
}}
</style>
</head>
<body>
<div class="module">
    <h2>{name}</h2>
    <div class="status">
        <strong>Status:</strong> <span style="color: {status_color};">{status_message}</span><br>
        <strong>Last Reading:</strong> <span id="scd41-last-reading">{last_reading_text}</span>
        {error_html}
    </div>
    <p><small>Serial: {sensor_serial}</small></p>
    <button class="full-btn" id="scd41-read-btn" onclick="getSCD41Reading()">Get Fresh Reading (takes 5s)</button>
    <button class="full-btn" id="scd41-details-btn" onclick="window.location='/scd41/details'">Details</button>
</div>
<script>
function getSCD41Reading() {{
    var statusSpan = document.getElementById('scd41-last-reading');
    var button = document.getElementById('scd41-read-btn');
    statusSpan.innerHTML = '<strong>Reading... (Please wait 5 seconds)</strong>';
    button.disabled = true;
    fetch('/scd41/read', {{ method: 'POST' }})
        .then(function(response) {{ return response.text(); }})
        .then(function(result) {{
            statusSpan.innerHTML = '<strong>' + result + '</strong> (just now)';
        }})
        .catch(function(error) {{
            statusSpan.textContent = 'Error: ' + error.message;
        }})
        .finally(function() {{
            button.disabled = false;
        }});
}}
</script>
</body>
</html>
""".format(
            status_color=status_color,
            name=self.name,
            status_message=self.status_message,
            last_reading_text=last_reading_text,
            error_html=error_html,
            sensor_serial=self.sensor_serial
        )

    def get_details_html(self, message=""):
        props = self._get_all_properties()
        readonly_props = [
            ("CO2", "CO2 concentration [ppm]"),
            ("temperature", "Temperature [°C]"),
            ("relative_humidity", "Relative Humidity [%]"),
            ("serial_number", "Sensor Serial Number")
        ]
        settable_props = [
            ("altitude", "Altitude [m]"),
            ("ambient_pressure", "Ambient Pressure [hPa]"),
            ("temperature_offset", "Temperature Offset [°C]"),
            ("self_calibration_enabled", "Self-Calibration (0=off, 1=on)"),
            ("target_co2", "Target CO2 for calibration [ppm]")
        ]
        actions = [
            ("measure_single_shot", "Take Single-Shot Measurement"),
            ("start_periodic_measurement", "Start Periodic Measurement"),
            ("start_low_periodic_measurement", "Start Low-Power Periodic Measurement"),
            ("stop_periodic_measurement", "Stop Periodic Measurement"),
            ("factory_reset", "Factory Reset"),
            ("reinit", "Soft Reset (Reinitialize)"),
            ("self_test", "Self Test"),
            ("persist_settings", "Save Settings to EEPROM"),
            ("force_calibration", "Force Calibration (input target CO2 below)"),
            ("set_ambient_pressure", "Set Ambient Pressure (input hPa below)")
        ]
        html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
    margin: 0;
    padding: 0;
    background: #f3f3f4;
}}
.module {{
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 18px 20px;
    margin: 10px auto;
    max-width: 420px;
    background: #fcfcfd;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}}
.section-title {{
    font-size: 1.13em;
    font-weight: bold;
    margin: 16px 0 8px 0;
    color: #156;
}}
.row-label {{
    font-weight: bold;
    margin-bottom: 2px;
    color: #222;
}}
.row-desc {{
    font-size: 0.97em;
    color: #666;
    margin-bottom: 2px;
}}
.row-value {{
    font-size: 1.09em;
    color: #228;
}}
.full-btn, .row-form input[type="submit"] {{
    margin-top: 12px;
    width: 100%;
    padding: 12px;
    font-size: 1.05em;
    border-radius: 4px;
    background-color: #007bff;
    color: #fff;
    border: none;
}}
.full-btn:active, .row-form input[type="submit"]:active {{
    background-color: #0056b3;
}}
.row-form input[type="text"], .row-form input[type="number"] {{
    width: 100%;
    padding: 12px;
    margin-bottom: 4px;
    border-radius: 4px;
    border: 1px solid #ccc;
    font-size: 1em;
}}
.row-form {{
    margin-bottom: 0;
}}
.msgbox {{
    margin-bottom: 12px;
    color: #155724;
    background: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 4px;
    padding: 6px 10px;
}}
@media (max-width: 520px) {{
    .module {{
        padding: 12px 3vw;
        max-width: 98vw;
    }}
    .full-btn, .row-form input[type="submit"] {{
        font-size: 1.05em;
    }}
}}
</style>
</head>
<body>
<div class="module">
    <h2>{name} — Details</h2>
    <a href="/"><button class="full-btn">Return to Dashboard</button></a>
    {msg_html}
    <div class="section-title">Read-Only Properties</div>
""".format(name=self.name, msg_html='<div class="msgbox">{}</div>'.format(message) if message else "")

        for key, desc in readonly_props:
            val = props.get(key, "N/A")
            html += """
    <div style="margin-bottom:12px;">
        <div class="row-label">{key}</div>
        <div class="row-desc">{desc}</div>
        <div class="row-value">{val}</div>
    </div>
""".format(key=key, desc=desc, val=val)

        html += '<div class="section-title">Settable Properties</div>'
        for key, desc in settable_props:
            val = props.get(key, "N/A")
            html += """
    <div style="margin-bottom:12px;">
        <div class="row-label">{key}</div>
        <div class="row-desc">{desc}</div>
        <div class="row-value">Current: {val}</div>
        <form class="row-form" method="POST" action="/scd41/details">
            <input type="hidden" name="set_property" value="1"/>
            <input type="hidden" name="property" value="{key}"/>
            <input type="text" name="value" placeholder="New value"/>
            <input type="submit" value="Set"/>
        </form>
    </div>
""".format(key=key, desc=desc, val=val)

        html += '<div class="section-title">Actions</div>'
        for action, desc in actions:
            if action in ("force_calibration", "set_ambient_pressure"):
                html += """
    <div style="margin-bottom:12px;">
        <div class="row-label">{action}</div>
        <div class="row-desc">{desc}</div>
        <form class="row-form" method="POST" action="/scd41/details">
            <input type="hidden" name="call_action" value="1"/>
            <input type="hidden" name="action" value="{action}"/>
            <input type="text" name="value" placeholder="Value"/>
            <input type="submit" value="Run"/>
        </form>
    </div>
""".format(action=action, desc=desc)
            else:
                html += """
    <div style="margin-bottom:12px;">
        <div class="row-label">{action}</div>
        <div class="row-desc">{desc}</div>
        <form class="row-form" method="POST" action="/scd41/details">
            <input type="hidden" name="call_action" value="1"/>
            <input type="hidden" name="action" value="{action}"/>
            <input type="submit" value="Run"/>
        </form>
    </div>
""".format(action=action, desc=desc)

        html += """
    <a href="/"><button class="full-btn">Return to Dashboard</button></a>
</div>
</body>
</html>
"""
        return html

    def update(self):
        pass