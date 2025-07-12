"""
PicowidFoundation - Robust base system for all picowicd applications
Extracted from production picowicd system
"""
import wifi
import socketpool
import ipaddress
import time
from adafruit_httpserver import Server, Request, Response
import gc
from foundation_templates import TemplateSystem

class Config:
    """Robust configuration with guaranteed defaults"""
    WIFI_SSID = "Picowicd"
    WIFI_PASSWORD = "simpletest"
    WIFI_AP_TIMEOUT_MINUTES = 10
    BLINK_INTERVAL = 0.25

class PicowicdFoundation:
    def __init__(self):
        self.config = Config()
        self.startup_log = []
        self.server = None
        self.modules = {}
        self.config_failed = False
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
            ssid = "Picowicd"
            password = "simpletest"

        try:
            self.startup_print(f"Attempting to start AP with SSID: {ssid}")
            wifi.radio.start_ap(ssid=ssid, password=password)
            self.startup_print("AP started successfully")
            return True, ssid, password
        except Exception as e:
            self.startup_print(f"AP start failed: {e}")
            try:
                wifi.radio.start_ap(ssid="Picowicd", password="simpletest")
                self.startup_print("AP started with defaults")
                return False, "Picowicd", "simpletest"
            except Exception as e2:
                self.startup_print(f"AP start failed completely: {e2}")
                return False, ssid, password

    def safe_set_ipv4_address(self):
        """Configure network with error handling"""
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
        """Robust config loading with settings.toml priority and config.py fallback"""
        # Cache os.getenv calls as recommended by CircuitPython docs
        import os

        try:
            self.startup_print("Loading user config...")

            # Try settings.toml first (modern approach)
            toml_ssid = os.getenv("WIFI_SSID")
            toml_password = os.getenv("WIFI_PASSWORD")
            toml_timeout = os.getenv("WIFI_AP_TIMEOUT_MINUTES")
            toml_blink = os.getenv("BLINK_INTERVAL")

            # If any setting found in TOML, use TOML approach
            if any([toml_ssid, toml_password, toml_timeout, toml_blink]):
                self.startup_print("Found settings.toml, using TOML configuration")

                # Apply TOML settings with individual fallbacks (preserve your pattern)
                if toml_ssid:
                    try:
                        self.config.WIFI_SSID = self.decode_html_entities(str(toml_ssid))
                    except:
                        self.config_failed = True

                if toml_password:
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
            self.startup_print("No settings.toml found, trying config.py")
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
            self.startup_print(f"Config import failed: {e}")
            self.config_failed = True

        if self.config_failed:
            self.config.BLINK_INTERVAL = 0.10  # Rapid blink error indicator

    def initialize_network(self):
        """Complete network initialization"""
        self.load_user_config()
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
        """Start web server"""
        self.server.start("192.168.4.1", port=80)
        self.startup_print("Foundation ready at http://192.168.4.1")

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
                    modules_html += f'<div class="module"><h3>DEBUG: Module {name}</h3>{module_html}</div>\n'
            except Exception as e:
                modules_html += f'<div class="module"><h3>{name}</h3><p>Error loading module: {e}</p></div>\n'

        # System info
        system_info = f"""
            <p><strong>WiFi SSID:</strong> {self.config.WIFI_SSID}</p>
            <p><strong>Network:</strong> http://192.168.4.1</p>
            <p><strong>Modules loaded:</strong> {len(self.modules)}</p>
            <p><strong>Config status:</strong> {'Failed' if self.config_failed else 'OK'}</p>
        """

        return self.templates.render_page(title, modules_html, system_info)