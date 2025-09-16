"""
Foundation Core - Robust Base System for WicdPico Applications
==============================================================

The foundation core provides the essential infrastructure for all wicdpico
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
    from foundation_core import WicdpicoFoundation
    
    # Initialize with automatic network detection
    foundation = WicdpicoFoundation()
    foundation.initialize_network()  # Auto-detects client/AP mode
    foundation.start_server()
    
    # Register modules
    
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
import config

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
    WIFI_SSID = "Wicdpico"
    WIFI_PASSWORD = "simpletest"
    WIFI_MODE = "AP"  # Default to AP mode
    WIFI_AP_TIMEOUT_MINUTES = 10
    BLINK_INTERVAL = 0.25

# AP timeout configuration
WIFI_AP_TIMEOUT_MINUTES = getattr(config, "WIFI_AP_TIMEOUT_MINUTES", 10)
WIFI_TIMEOUT_SECONDS = WIFI_AP_TIMEOUT_MINUTES * 60

global last_activity_time
last_activity_time = time.monotonic()
ap_is_off_and_logged = False
timeout_disabled = False  # Set to True to disable timeout

class WicdpicoFoundation:
    """
    Core foundation class providing network, web server, and module management.
    
    The WicdpicoFoundation serves as the central coordination point for all
    wicdpico functionality, managing network connectivity, HTTP services,
    and module integration.
    
    :param config_source: Optional configuration override
    :type config_source: dict or None
    
    .. code-block:: python
    
        # Create foundation instance
        foundation = WicdpicoFoundation()
        
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


    def get_module(self, name):
        """
        Get registered module by name.
        
        Retrieves a previously registered module from the system registry.
        Used by modules to access other modules for data sharing.
        
        :param name: Module name to retrieve
        :type name: str
        :return: Module instance or None if not found
        :rtype: WicdpicoModule or None
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
            ssid = "Wicdpico-Recovery"
            password = "emergency123"

        try:
            self.startup_print(f"Starting AP with SSID: {ssid}")
            wifi.radio.start_ap(ssid=ssid, password=password)
            self.startup_print("AP started successfully")
            return True, ssid, password
        except Exception as e:
            self.startup_print(f"AP start failed: {e}")
            try:
                wifi.radio.start_ap(ssid="Wicdpico-Recovery", password="emergency123")
                self.startup_print("AP started with emergency defaults")
                return False, "Wicdpico-Recovery", "emergency123"
            except Exception as e2:
                self.startup_print(f"AP start failed completely: {e2}")
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
                # Force AP mode for standalone sensor meter
                self.config.WIFI_MODE = "AP"

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
            self.config.WIFI_SSID = "Wicdpico-Recovery"
            self.config.WIFI_PASSWORD = "emergency123"
            self.config.BLINK_INTERVAL = 0.10  # Rapid blink error indicator

    def initialize_network(self):
        """
        Initialize standalone AP mode network for sensor meter.
        
        Creates WiFi hotspot for direct device access and sensor monitoring.
        
        :return: True if network initialization successful
        :rtype: bool
        
        .. code-block:: python
        
            foundation = WicdpicoFoundation()
            
            if foundation.initialize_network():
                print("AP mode ready at 192.168.4.1")
            else:
                print("Network initialization failed")
        """
        self.load_user_config()
        
        # Force AP mode for standalone sensor meter
        self.wifi_mode = "AP"
        self.startup_print("WiFi mode: AP (standalone sensor meter)")
        
        # AP mode - create own hotspot
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
        :type module: WicdpicoModule
        :raises ValueError: If module name already exists
        :raises TypeError: If module doesn't inherit from WicdpicoModule
        
        .. code-block:: python
        
            
            # Register multiple modules
            foundation.register_module("sensors", sensor_module)
            foundation.register_module("logging", log_module)
        """
        self.modules[name] = module
        module.register_routes(self.server)

    def start_server(self):
        """
        Start web server for AP mode standalone sensor meter.
        
        Initializes HTTP server on AP mode IP address (192.168.4.1).
        """
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

            check_wifi_timeout()  # <-- Add this line

            time.sleep(0.1)
            gc.collect()

    def render_dashboard(self, title="Wicdpico Dashboard"):
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


        # Collect HTML from all enabled modules
        for name, module in self.modules.items():
            try:
                module_html = module.get_dashboard_html()
                if module_html:
                    modules_html += f'<div class="module"><h3>Module: {name}</h3>{module_html}</div>\n'
            except Exception as e:
                modules_html += f'<div class="module"><h3>{name}</h3><p>Error loading module: {e}</p></div>\n'

        # System info for standalone sensor meter
        system_info = f"""
            <p><strong>Sensor Meter:</strong> Standalone AP Mode</p>
            <p><strong>WiFi Hotspot:</strong> {self.config.WIFI_SSID}</p>
            <p><strong>Access URL:</strong> http://192.168.4.1</p>
            <p><strong>Modules loaded:</strong> {len(self.modules)}</p>
            <p><strong>System status:</strong> {'Configuration Error' if self.config_failed else 'Ready'}</p>
        """

        html = self.templates.render_page(title, modules_html, system_info)

        html += """
<!-- Wi-Fi Hotspot Timeout Card -->
<div class="card" id="hotspot-timeout-card">
  <h3>Wi-Fi Hotspot Timeout</h3>
  <p id="hotspot-timeout-desc">
    By default, the Wi-Fi hotspot (AP) will shut down after a period of inactivity for security and power saving.
    You can disable this timeout to keep the AP open, or manually close it now.
  </p>
  <button id="hotspot-btn" onclick="toggleHotspotControl()">Loading...</button>
  <div id="hotspot-result"></div>
  </div>

<script>
function toggleHotspotControl() {
    const btn = document.getElementById('hotspot-btn');
    const resultDiv = document.getElementById('hotspot-result');
    if (btn.textContent === 'Close Hotspot') {
        if (confirm("Are you sure you want to close the Wi-Fi hotspot? A physical power cycle will be required to restart it.")) {
            fetch('/toggle-hotspot-control', { method: 'POST' })
                .then(() => {
                    resultDiv.textContent =
                        "Hotspot closed. Connection loss is normal. Power cycle to restore hotspot.";
                    document.querySelectorAll('button').forEach(b => b.disabled = true);
                })
                .catch(() => {
                    resultDiv.textContent =
                        "Hotspot is shutting down. Connection loss is normal. Power cycle to restore hotspot.";
                    document.querySelectorAll('button').forEach(b => b.disabled = true);
                });
        } else {
            resultDiv.textContent = 'Hotspot closure cancelled.';
        }
    } else {
        fetch('/toggle-hotspot-control', { method: 'POST' })
            .then(() => {
                btn.textContent = 'Close Hotspot';
                resultDiv.textContent =
                    'Automatic timeout disabled. Hotspot will remain open.';
            })
            .catch(error => {
                resultDiv.textContent = 'Error: ' + error.message;
            });
    }
}
</script>
"""

        return html

def shut_down_wifi_and_sleep():
    # Replace with your AP shutdown logic
    print("Initiating Wi-Fi AP shutdown due to inactivity...")
    try:
        import wifi
        if wifi.radio.enabled:
            wifi.radio.stop_ap()
            print("Wi-Fi AP shut down.")
        else:
            print("Wi-Fi AP already off.")
    except Exception as e:
        print(f"Error shutting down AP: {e}")

def check_wifi_timeout():
    global last_activity_time, ap_is_off_and_logged, timeout_disabled
    if timeout_disabled:
        return
    now = time.monotonic()
    if wifi.radio.enabled:
        elapsed = now - last_activity_time
        if elapsed > WIFI_TIMEOUT_SECONDS and not ap_is_off_and_logged:
            shut_down_wifi_and_sleep()
        elif not ap_is_off_and_logged:
            remaining = WIFI_TIMEOUT_SECONDS - elapsed
            print(f"AP active. Inactivity: {elapsed:.1f}s / Remaining: {remaining:.1f}s")
    else:
        if not ap_is_off_and_logged:
            print("AP is already off.")
            ap_is_off_and_logged = True
