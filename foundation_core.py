"""
Foundation Core - Robust Base System for PicoWicd Applications
==============================================================

The foundation core provides the essential infrastructure for all picowicd
applications, including network management, web server functionality, and
module integration.

Hardware Requirements
--------------------
* Raspberry Pi Pico 2 W microcontroller
* CircuitPython 9.0+ firmware
* WiFi network access (client mode) or standalone operation (AP mode)

Software Dependencies  
--------------------
* adafruit_httpserver
* wifi (built-in CircuitPython)
* socketpool (built-in CircuitPython)
* ipaddress (built-in CircuitPython)

Key Features
-----------
* **Dual WiFi Modes**: Client mode for hub integration, AP mode for standalone
* **Robust Configuration**: Settings.toml priority with fallback to config.py
* **Modular Architecture**: Plugin system for sensor and control modules
* **Web Interface**: Built-in HTTP server with template system
* **Mode Switching**: Virtual buttons to switch between AP and Client modes
* **Error Recovery**: Graceful handling of network and configuration failures

Network Modes
-------------
**Client Mode**
    Connects to existing WiFi network (typically Pi5 WCS Hub)
    Ideal for multi-node sensor networks with centralized data collection
    
**Access Point Mode**
    Creates own WiFi hotspot for direct device access
    Perfect for standalone operation and initial configuration

.. code-block:: python

    # Basic foundation setup
    from foundation_core import PicowicdFoundation
    
    # Initialize with automatic network detection
    foundation = PicowicdFoundation()
    foundation.initialize_network()  # Auto-detects client/AP mode
    foundation.start_server()
    
    # Register modules
    from mqtt_module import MQTTModule
    mqtt = MQTTModule(foundation)
    foundation.register_module("mqtt", mqtt)
    
    # Start main application loop
    foundation.run_main_loop()

Configuration Priority
---------------------
1. **settings.toml** (preferred modern approach)
2. **config.py** (legacy fallback)
3. **Emergency defaults** (built-in safety values)

.. note::
   The foundation automatically detects the best available configuration
   source and applies robust defaults if configuration loading fails.
"""
import wifi
import socketpool
import ipaddress
import time
import os
import microcontroller
from adafruit_httpserver import Server, Request, Response
import gc
from foundation_templates import TemplateSystem

class Config:
    """
    Configuration container with guaranteed defaults.
    
    Provides robust default values for all system configuration
    parameters to ensure system stability even if user configuration fails.
    
    :ivar WIFI_SSID: Default WiFi network name
    :vartype WIFI_SSID: str
    :ivar WIFI_PASSWORD: Default WiFi password
    :vartype WIFI_PASSWORD: str
    :ivar WIFI_MODE: Network mode - "AP" or "CLIENT"
    :vartype WIFI_MODE: str
    """
    WIFI_SSID = "Picowicd"
    WIFI_PASSWORD = "simpletest"
    WIFI_MODE = "AP"  # Default to AP mode
    WIFI_AP_TIMEOUT_MINUTES = 10
    BLINK_INTERVAL = 0.25

class PicowicdFoundation:
    """
    Core foundation class providing network, web server, and module management.
    
    The PicowicdFoundation serves as the central coordination point for all
    picowicd functionality, managing network connectivity, HTTP services,
    and module integration.
    
    :param config_source: Optional configuration override
    :type config_source: dict or None
    
    .. code-block:: python
    
        # Create foundation instance
        foundation = PicowicdFoundation()
        
        # Initialize network (auto-detects mode)
        if foundation.initialize_network():
            print("Network ready")
        
        # Register custom modules
        foundation.register_module("sensors", sensor_module)
    """
    
    def __init__(self):
        """
        Initialize foundation system with default configuration.
        
        Sets up configuration container, logging system, and template engine.
        Does not initialize network - call initialize_network() separately.
        """
        self.config = Config()
        self.startup_log = []
        self.server = None
        self.modules = {}
        self.config_failed = False
        self.wifi_mode = "AP"  # Track current mode
        self.templates = TemplateSystem()

    def startup_print(self, message):
        """
        Dual console/web logging for debugging.
        
        Prints message to console and stores in startup log for
        web dashboard display and debugging purposes.
        
        :param message: Message to log
        :type message: str
        """
        print(message)
        self.startup_log.append(message)

    def decode_html_entities(self, text):
        """
        Clean web form input of HTML entities.
        
        Converts common HTML entities back to their character equivalents
        for safe processing of user input from web forms.
        
        :param text: Text containing HTML entities
        :type text: str
        :return: Text with entities decoded
        :rtype: str
        """
        text = text.replace('&quot;', '"')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&#39;', "'")
        return text

    def validate_wifi_password(self, password):
        """
        Validate WPA2 requirements for WiFi password.
        
        Ensures password meets minimum security requirements for
        WPA2 wireless networks.
        
        :param password: Password to validate
        :type password: str
        :return: Tuple of (is_valid, error_message)
        :rtype: tuple[bool, str]
        """
        if not password:
            return False, "WiFi password cannot be empty"
        if len(password) < 8:
            return False, "WiFi password must be at least 8 characters"
        if len(password) > 64:
            return False, "WiFi password cannot exceed 64 characters"
        return True, ""

    def write_settings_toml(self, new_mode):
        """
        Update settings.toml file with new WiFi mode.
        
        Safely updates the settings.toml file by preserving existing settings
        and only changing the WIFI_MODE parameter.
        
        :param new_mode: New WiFi mode ("AP" or "CLIENT")
        :type new_mode: str
        :return: Success status
        :rtype: bool
        """
        try:
            # Read current settings
            current_settings = {}
            
            # Try to read existing settings.toml
            try:
                current_settings = {
                    'WIFI_SSID': os.getenv("WIFI_SSID", "wicdhub"),
                    'WIFI_PASSWORD': os.getenv("WIFI_PASSWORD", "pudden789"),
                    'WIFI_MODE': new_mode,
                    'MQTT_BROKER': os.getenv("MQTT_BROKER", "192.168.99.1"),
                    'MQTT_PORT': os.getenv("MQTT_PORT", "1883"),
                    'MQTT_USERNAME': os.getenv("MQTT_USERNAME", "picowicd"),
                    'MQTT_PASSWORD': os.getenv("MQTT_PASSWORD", "picowicd123"),
                    'MQTT_NODE_ID': os.getenv("MQTT_NODE_ID", "node00"),
                    'MQTT_PUBLISH_INTERVAL': os.getenv("MQTT_PUBLISH_INTERVAL", "30"),
                    'MQTT_KEEPALIVE': os.getenv("MQTT_KEEPALIVE", "60"),
                    'MQTT_TOPIC_BASE': os.getenv("MQTT_TOPIC_BASE", "wcs"),
                    'BLINK_INTERVAL': os.getenv("BLINK_INTERVAL", "0.5")
                }
            except Exception as e:
                self.startup_print(f"Warning: Could not read current settings: {e}")
            
            # Write new settings.toml
            toml_content = '# CRITICAL SETTINGS FOR WCS HUB VALIDATION\n'
            toml_content += '# Connect picowicd to Pi5 WCS Hub for academic publication\n\n'
            
            if new_mode == "CLIENT":
                toml_content += '# WiFi Configuration - Pi5 WCS Hub Network\n'
                toml_content += f'WIFI_SSID = "{current_settings["WIFI_SSID"]}"\n'
                toml_content += f'WIFI_PASSWORD = "{current_settings["WIFI_PASSWORD"]}"\n'
                toml_content += 'WIFI_MODE = "CLIENT"\n\n'
            else:  # AP mode
                toml_content += '# WiFi Configuration - PicoW Access Point\n'
                toml_content += 'WIFI_SSID = "PicoTest-Node00"\n'
                toml_content += 'WIFI_PASSWORD = "testpass123"\n'
                toml_content += 'WIFI_MODE = "AP"\n\n'
            
            toml_content += '# MQTT Configuration - Pi5 Mosquitto Broker\n'
            toml_content += f'MQTT_BROKER = "{current_settings["MQTT_BROKER"]}"\n'
            toml_content += f'MQTT_PORT = "{current_settings["MQTT_PORT"]}"\n'
            toml_content += f'MQTT_USERNAME = "{current_settings["MQTT_USERNAME"]}"\n'
            toml_content += f'MQTT_PASSWORD = "{current_settings["MQTT_PASSWORD"]}"\n'
            toml_content += f'MQTT_NODE_ID = "{current_settings["MQTT_NODE_ID"]}"\n'
            toml_content += f'MQTT_PUBLISH_INTERVAL = "{current_settings["MQTT_PUBLISH_INTERVAL"]}"\n'
            toml_content += f'MQTT_KEEPALIVE = "{current_settings["MQTT_KEEPALIVE"]}"\n'
            toml_content += f'MQTT_TOPIC_BASE = "{current_settings["MQTT_TOPIC_BASE"]}"\n\n'
            
            toml_content += '# System Configuration\n'
            toml_content += f'BLINK_INTERVAL = "{current_settings["BLINK_INTERVAL"]}"\n'
            
            # Write to file
            with open("settings.toml", "w") as f:
                f.write(toml_content)
            
            self.startup_print(f"Settings updated: WIFI_MODE = {new_mode}")
            return True
            
        except Exception as e:
            self.startup_print(f"Failed to update settings.toml: {e}")
            return False

    def switch_wifi_mode(self, new_mode):
        """
        Switch WiFi mode and reboot system.
        
        Updates configuration file and performs system reboot to apply
        the new WiFi mode. This is necessary because WiFi mode changes
        require complete network reinitialization.
        
        :param new_mode: Target WiFi mode ("AP" or "CLIENT")
        :type new_mode: str
        :return: Success status (system will reboot if successful)
        :rtype: bool
        """
        if new_mode not in ["AP", "CLIENT"]:
            self.startup_print(f"Invalid WiFi mode: {new_mode}")
            return False
        
        if new_mode == self.wifi_mode:
            self.startup_print(f"Already in {new_mode} mode")
            return True
        
        self.startup_print(f"Switching from {self.wifi_mode} to {new_mode} mode...")
        
        # Update settings.toml
        if not self.write_settings_toml(new_mode):
            return False
        
        # Give time for any final operations
        time.sleep(1)
        
        # Reboot to apply new mode
        self.startup_print("Rebooting to apply new WiFi mode...")
        time.sleep(0.5)
        microcontroller.reset()
        
        return True  # Won't reach here due to reset

    def get_module(self, name):
        """
        Get registered module by name.
        
        Retrieves a previously registered module from the system registry.
        Used by modules to access other modules for data sharing.
        
        :param name: Module name to retrieve
        :type name: str
        :return: Module instance or None if not found
        :rtype: PicowicdModule or None
        """
        return self.modules.get(name)

    def safe_start_access_point(self, ssid, password):
        """
        Robust AP startup with fallback.
        
        Attempts to start WiFi access point with given credentials,
        falling back to emergency settings if validation or startup fails.
        
        :param ssid: Network name for access point
        :type ssid: str
        :param password: Network password
        :type password: str
        :return: Tuple of (success, actual_ssid, actual_password)
        :rtype: tuple[bool, str, str]
        """
        is_valid, error_msg = self.validate_wifi_password(password)
        if not is_valid:
            self.startup_print(f"Password validation failed: {error_msg}")
            self.startup_print("Falling back to default credentials")
            ssid = "Picowicd-Recovery"
            password = "emergency123"

        try:
            self.startup_print(f"Starting AP with SSID: {ssid}")
            wifi.radio.start_ap(ssid=ssid, password=password)
            self.startup_print("AP started successfully")
            return True, ssid, password
        except Exception as e:
            self.startup_print(f"AP start failed: {e}")
            try:
                wifi.radio.start_ap(ssid="Picowicd-Recovery", password="emergency123")
                self.startup_print("AP started with emergency defaults")
                return False, "Picowicd-Recovery", "emergency123"
            except Exception as e2:
                self.startup_print(f"AP start failed completely: {e2}")
                return False, ssid, password

    def safe_connect_client(self, ssid, password):
        """
        Robust client connection with timeout.
        
        Attempts to connect to existing WiFi network with comprehensive
        error handling and timeout protection.
        
        :param ssid: WiFi network name to connect to
        :type ssid: str
        :param password: WiFi network password
        :type password: str
        :return: Tuple of (success, ssid, password)
        :rtype: tuple[bool, str, str]
        """
        try:
            self.startup_print(f"Connecting to WiFi: {ssid}")
            wifi.radio.connect(ssid, password, timeout=30)
            
            if wifi.radio.connected:
                self.startup_print(f"Connected successfully: {wifi.radio.ipv4_address}")
                return True, ssid, password
            else:
                self.startup_print("Connection failed - no connection established")
                return False, ssid, password
                
        except Exception as e:
            self.startup_print(f"Client connection failed: {e}")
            return False, ssid, password

    def safe_set_ipv4_address(self):
        """
        Configure network with error handling - AP mode only.
        
        Sets up IPv4 addressing for access point mode with standard
        subnet configuration. Client mode handles IP automatically.
        
        :return: True if configuration successful
        :rtype: bool
        """
        if self.wifi_mode != "AP":
            return True  # Client mode handles IP automatically
            
        try:
            time.sleep(0.5)
            wifi.radio.set_ipv4_address_ap(
                ipv4=ipaddress.IPv4Address("192.168.4.1"),
                netmask=ipaddress.IPv4Address("255.255.255.0"),
                gateway=ipaddress.IPv4Address("192.168.4.1")
            )
            self.startup_print("IPv4 configured successfully")
            return True
        except Exception as e:
            self.startup_print(f"IPv4 config failed: {e}")
            return False

    def load_user_config(self):
        """
        Robust config loading with settings.toml priority and robust defaults.
        
        Loads user configuration from settings.toml (preferred) or config.py
        (fallback), with comprehensive error handling and emergency defaults.
        
        **Configuration Priority:**
        
        1. settings.toml (modern CircuitPython approach)
        2. config.py (legacy compatibility)
        3. Emergency defaults (built-in safety values)
        """
        try:
            self.startup_print("Loading user config...")

            # Try settings.toml first (modern approach)
            toml_mode = os.getenv("WIFI_MODE")
            toml_ssid = os.getenv("WIFI_SSID")
            toml_password = os.getenv("WIFI_PASSWORD")
            toml_timeout = os.getenv("WIFI_AP_TIMEOUT_MINUTES")
            toml_blink = os.getenv("BLINK_INTERVAL")

            # If core WiFi settings found in TOML, use TOML approach
            if toml_mode and toml_ssid and toml_password:
                self.startup_print("Found settings.toml, using TOML configuration")

                # Apply TOML settings with individual fallbacks
                try:
                    self.config.WIFI_MODE = str(toml_mode).upper()
                    if self.config.WIFI_MODE not in ["AP", "CLIENT"]:
                        self.config.WIFI_MODE = "AP"  # Safe default
                except:
                    self.config_failed = True

                try:
                    self.config.WIFI_SSID = self.decode_html_entities(str(toml_ssid))
                except:
                    self.config_failed = True

                try:
                    self.config.WIFI_PASSWORD = self.decode_html_entities(str(toml_password))
                except:
                    self.config_failed = True

                if toml_timeout:
                    try:
                        self.config.WIFI_AP_TIMEOUT_MINUTES = int(toml_timeout)
                    except:
                        self.config_failed = True

                if toml_blink:
                    try:
                        self.config.BLINK_INTERVAL = float(toml_blink)
                    except:
                        self.config_failed = True
                return

            # Fall back to config.py (existing working approach)
            self.startup_print("No complete settings.toml found, trying config.py")
            import config as user_config

            # Your existing config.py logic (unchanged)
            try:
                ssid = self.decode_html_entities(str(user_config.WIFI_SSID))
                self.config.WIFI_SSID = ssid
            except:
                self.config_failed = True

            try:
                password = self.decode_html_entities(str(user_config.WIFI_PASSWORD))
                self.config.WIFI_PASSWORD = password
            except:
                self.config_failed = True

            try:
                self.config.WIFI_AP_TIMEOUT_MINUTES = int(user_config.WIFI_AP_TIMEOUT_MINUTES)
            except:
                self.config_failed = True

            try:
                self.config.BLINK_INTERVAL = float(user_config.BLINK_INTERVAL)
            except:
                self.config_failed = True

        except Exception as e:
            self.startup_print(f"All config loading failed: {e}")
            self.config_failed = True

        # Apply robust defaults if config failed
        if self.config_failed:
            self.startup_print("Using robust emergency defaults")
            self.config.WIFI_MODE = "AP"
            self.config.WIFI_SSID = "Picowicd-Recovery"
            self.config.WIFI_PASSWORD = "emergency123"
            self.config.BLINK_INTERVAL = 0.10  # Rapid blink error indicator

    def initialize_network(self):
        """
        Initialize network connectivity with automatic mode detection.
        
        Attempts client mode connection first (for hub integration), then
        falls back to access point mode if client connection fails.
        Provides comprehensive error handling and recovery.
        
        :return: True if network initialization successful
        :rtype: bool
        :raises NetworkError: If both client and AP modes fail
        
        **Network Priority:**
        
        1. **Client Mode**: Connect to existing WiFi (Pi5 WCS Hub)
        2. **AP Fallback**: Create own hotspot if client fails
        3. **Emergency AP**: Use safe defaults if configuration invalid
        
        .. code-block:: python
        
            foundation = PicowicdFoundation()
            
            if foundation.initialize_network():
                print(f"Connected: {foundation.wifi_mode}")
                print(f"IP: {wifi.radio.ipv4_address}")
            else:
                print("Network initialization failed")
        """
        self.load_user_config()
        
        # Determine WiFi mode
        self.wifi_mode = self.config.WIFI_MODE
        self.startup_print(f"WiFi mode: {self.wifi_mode}")
        
        if self.wifi_mode == "CLIENT":
            # Client mode - connect to existing network (Pi5 hub)
            client_success, ssid, password = self.safe_connect_client(
                self.config.WIFI_SSID,
                self.config.WIFI_PASSWORD
            )
            self.config.WIFI_SSID = ssid
            self.config.WIFI_PASSWORD = password
            
            if client_success:
                # Create server using client IP
                pool = socketpool.SocketPool(wifi.radio)
                self.server = Server(pool, "/", debug=False)
                server_ip = str(wifi.radio.ipv4_address)
                self.startup_print(f"Client mode server IP: {server_ip}")
                return True
            else:
                self.startup_print("Client connection failed - falling back to AP mode")
                self.wifi_mode = "AP"  # Fallback to AP
        
        # AP mode - create own hotspot (original logic)
        ap_success, ssid, password = self.safe_start_access_point(
            self.config.WIFI_SSID,
            self.config.WIFI_PASSWORD
        )
        self.config.WIFI_SSID = ssid
        self.config.WIFI_PASSWORD = password

        ipv4_success = self.safe_set_ipv4_address()

        pool = socketpool.SocketPool(wifi.radio)
        self.server = Server(pool, "/", debug=False)

        return ap_success and ipv4_success

    def register_module(self, name, module):
        """
        Register a module with the foundation system.
        
        Adds the module to the system registry and automatically
        configures its web routes with the HTTP server.
        
        :param name: Unique identifier for the module
        :type name: str
        :param module: Module instance to register
        :type module: PicowicdModule
        :raises ValueError: If module name already exists
        :raises TypeError: If module doesn't inherit from PicowicdModule
        
        .. code-block:: python
        
            # Register MQTT module
            mqtt_module = MQTTModule(foundation)
            foundation.register_module("mqtt", mqtt_module)
            
            # Register multiple modules
            foundation.register_module("sensors", sensor_module)
            foundation.register_module("logging", log_module)
        """
        self.modules[name] = module
        module.register_routes(self.server)

    def start_server(self):
        """
        Start web server with appropriate IP and register mode switching routes.
        
        Initializes HTTP server on the correct IP address based on
        current network mode and adds mode switching functionality.
        """
        # Register mode switching route
        @self.server.route("/switch-mode", methods=['POST'])
        def switch_mode_route(request: Request):
            """Handle WiFi mode switching requests."""
            try:
                body = request.body.decode('utf-8') if request.body else ""
                
                target_mode = None
                if "mode=CLIENT" in body:
                    target_mode = "CLIENT"
                elif "mode=AP" in body:
                    target_mode = "AP"
                
                if not target_mode:
                    return Response(request, "No valid mode specified", content_type="text/plain")
                
                if target_mode == self.wifi_mode:
                    return Response(request, f"Already in {target_mode} mode", content_type="text/plain")
                
                # Initiate mode switch (this will reboot the system)
                success = self.switch_wifi_mode(target_mode)
                
                if success:
                    return Response(request, f"Switching to {target_mode} mode... (rebooting)", content_type="text/plain")
                else:
                    return Response(request, f"Failed to switch to {target_mode} mode", content_type="text/plain")
                    
            except Exception as e:
                return Response(request, f"Mode switch error: {str(e)}", content_type="text/plain")
        
        if self.wifi_mode == "CLIENT":
            server_ip = str(wifi.radio.ipv4_address)
        else:
            server_ip = "192.168.4.1"
            
        self.server.start(server_ip, port=80)
        self.startup_print(f"Foundation ready at http://{server_ip}")

    def run_main_loop(self):
        """
        Main polling loop with module updates.
        
        Continuously processes HTTP requests and updates all registered
        modules. Includes garbage collection for memory management.
        """
        while True:
            self.server.poll()

            # Update all modules
            for module in self.modules.values():
                module.update()

            time.sleep(0.1)
            gc.collect()

    def render_dashboard(self, title="Picowicd Dashboard"):
        """
        Render complete dashboard with all modules and mode switching controls.
        
        Generates HTML dashboard page by collecting content from all
        registered modules and combining with system information and
        mode switching controls.
        
        :param title: Page title for dashboard
        :type title: str
        :return: Complete HTML page
        :rtype: str
        """
        modules_html = ""

        # Add mode switching control widget
        if self.wifi_mode == "AP":
            mode_switch_html = '''
            <div class="module">
                <h3>WiFi Mode Control</h3>
                <div class="status" style="border-left: 4px solid #007bff;">
                    <strong>Current Mode:</strong> Access Point (AP)<br>
                    <strong>Function:</strong> Serving web dashboard and control interface<br>
                    <strong>Network:</strong> Creating hotspot for direct device access
                </div>
                
                <div class="control-group">
                    <button id="switch-client-btn" onclick="switchToClientMode()" style="background: #28a745;">
                        Switch to Node Mode
                    </button>
                    <p style="margin: 10px 0; font-size: 14px; color: #666;">
                        Switch to node mode to connect to Pi5 hub and send sensor data via MQTT
                    </p>
                </div>
                
                <div id="mode-switch-status" class="status" style="margin-top: 10px;">
                    Ready to switch modes
                </div>
            </div>

            <script>
            function switchToClientMode() {
                if (!confirm('Switch to Node Mode? This will connect to the Pi5 hub and stop the local web interface.')) {
                    return;
                }
                
                const btn = document.getElementById('switch-client-btn');
                const originalText = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Switching...';

                fetch('/switch-mode', { 
                    method: 'POST',
                    body: 'mode=CLIENT'
                })
                .then(response => response.text())
                .then(result => {
                    document.getElementById('mode-switch-status').innerHTML = '<strong>Status:</strong> ' + result;
                    document.getElementById('mode-switch-status').style.background = '#fff3cd';
                    document.getElementById('mode-switch-status').style.borderLeft = '4px solid #ffc107';
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('mode-switch-status').innerHTML = '<strong>Error:</strong> ' + error.message;
                    document.getElementById('mode-switch-status').style.background = '#f8d7da';
                    document.getElementById('mode-switch-status').style.borderLeft = '4px solid #dc3545';
                });
            }
            </script>
            '''
        else:  # CLIENT mode
            mode_switch_html = '''
            <div class="module">
                <h3>WiFi Mode Control</h3>
                <div class="status" style="border-left: 4px solid #28a745;">
                    <strong>Current Mode:</strong> Client/Node Mode<br>
                    <strong>Function:</strong> Sending sensor data to Pi5 hub via MQTT<br>
                    <strong>Network:</strong> Connected to Pi5 WCS Hub
                </div>
                
                <div class="control-group">
                    <button id="switch-ap-btn" onclick="switchToAPMode()" style="background: #007bff;">
                        Switch to AP Mode
                    </button>
                    <p style="margin: 10px 0; font-size: 14px; color: #666;">
                        Switch to AP mode to serve local web dashboard and configuration interface
                    </p>
                </div>
                
                <div id="mode-switch-status" class="status" style="margin-top: 10px;">
                    Ready to switch modes
                </div>
            </div>

            <script>
            function switchToAPMode() {
                if (!confirm('Switch to AP Mode? This will disconnect from the Pi5 hub and create a local hotspot.')) {
                    return;
                }
                
                const btn = document.getElementById('switch-ap-btn');
                const originalText = btn.textContent;
                btn.disabled = true;
                btn.textContent = 'Switching...';

                fetch('/switch-mode', { 
                    method: 'POST',
                    body: 'mode=AP'
                })
                .then(response => response.text())
                .then(result => {
                    document.getElementById('mode-switch-status').innerHTML = '<strong>Status:</strong> ' + result;
                    document.getElementById('mode-switch-status').style.background = '#fff3cd';
                    document.getElementById('mode-switch-status').style.borderLeft = '4px solid #ffc107';
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = originalText;
                    document.getElementById('mode-switch-status').innerHTML = '<strong>Error:</strong> ' + error.message;
                    document.getElementById('mode-switch-status').style.background = '#f8d7da';
                    document.getElementById('mode-switch-status').style.borderLeft = '4px solid #dc3545';
                });
            }
            </script>
            '''

        modules_html += mode_switch_html

        # Collect HTML from all enabled modules
        for name, module in self.modules.items():
            try:
                module_html = module.get_dashboard_html()
                if module_html:
                    modules_html += f'<div class="module"><h3>Module: {name}</h3>{module_html}</div>\n'
            except Exception as e:
                modules_html += f'<div class="module"><h3>{name}</h3><p>Error loading module: {e}</p></div>\n'

        # System info with mode status
        system_info = f"""
            <p><strong>WiFi Mode:</strong> {self.wifi_mode}</p>
            <p><strong>WiFi SSID:</strong> {self.config.WIFI_SSID}</p>
            <p><strong>Network:</strong> http://{wifi.radio.ipv4_address if self.wifi_mode == "CLIENT" else "192.168.4.1"}</p>
            <p><strong>Modules loaded:</strong> {len(self.modules)}</p>
            <p><strong>Config status:</strong> {'Failed' if self.config_failed else 'OK'}</p>
        """

        return self.templates.render_page(title, modules_html, system_info)