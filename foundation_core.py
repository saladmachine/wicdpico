"""
PicowidFoundation - Robust base system for all picowicd applications
Updated with WiFi mode support for MQTT client connections
"""
import wifi
import socketpool
import ipaddress
import time
import os
from adafruit_httpserver import Server, Request, Response
import gc
from foundation_templates import TemplateSystem

class Config:
    """Robust configuration with guaranteed defaults"""
    WIFI_SSID = "Picowicd"
    WIFI_PASSWORD = "simpletest"
    WIFI_MODE = "AP"  # Default to AP mode
    WIFI_AP_TIMEOUT_MINUTES = 10
    BLINK_INTERVAL = 0.25

class PicowicdFoundation:
    def __init__(self):
        self.config = Config()
        self.startup_log = []
        self.server = None
        self.modules = {}
        self.config_failed = False
        self.wifi_mode = "AP"  # Track current mode
        self.templates = TemplateSystem()

    def startup_print(self, message):
        """Dual console/web logging for debugging"""
        print(message)
        self.startup_log.append(message)

    def decode_html_entities(self, text):
        """Clean web form input of HTML entities"""
        text = text.replace('&quot;', '"')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&#39;', "'")
        return text

    def validate_wifi_password(self, password):
        """Validate WPA2 requirements"""
        if not password:
            return False, "WiFi password cannot be empty"
        if len(password) < 8:
            return False, "WiFi password must be at least 8 characters"
        if len(password) > 64:
            return False, "WiFi password cannot exceed 64 characters"
        return True, ""

    def safe_start_access_point(self, ssid, password):
        """Robust AP startup with fallback"""
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
        """Robust client connection with timeout"""
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
        """Configure network with error handling - AP mode only"""
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
        """Robust config loading with settings.toml priority and robust defaults"""
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
        """Complete network initialization with mode support"""
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
        """Add module to system"""
        self.modules[name] = module
        module.register_routes(self.server)

    def start_server(self):
        """Start web server with appropriate IP"""
        if self.wifi_mode == "CLIENT":
            server_ip = str(wifi.radio.ipv4_address)
        else:
            server_ip = "192.168.4.1"
            
        self.server.start(server_ip, port=80)
        self.startup_print(f"Foundation ready at http://{server_ip}")

    def run_main_loop(self):
        """Main polling loop with module updates"""
        while True:
            self.server.poll()

            # Update all modules
            for module in self.modules.values():
                module.update()

            time.sleep(0.1)
            gc.collect()

    def render_dashboard(self, title="Picowicd Dashboard"):
        """Render complete dashboard with all modules"""
        modules_html = ""

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