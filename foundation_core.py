# foundation_core.py (With Root Page Handler)
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
import board
import busio

class Config:
    """
    Configuration container with guaranteed defaults.
    """
    WIFI_SSID = "Wicdpico"
    WIFI_PASSWORD = "simpletest"
    WIFI_MODE = "AP"
    WIFI_AP_TIMEOUT_MINUTES = 10
    BLINK_INTERVAL = 0.25

# AP timeout configuration
WIFI_AP_TIMEOUT_MINUTES = getattr(config, "WIFI_AP_TIMEOUT_MINUTES", 10)
WIFI_TIMEOUT_SECONDS = WIFI_AP_TIMEOUT_MINUTES * 60

global last_activity_time
last_activity_time = time.monotonic()
ap_is_off_and_logged = False
timeout_disabled = False

class WicdpicoFoundation:
    """
    Core foundation class providing network, web server, and module management.
    """
    
    def __init__(self):
        """
        Initialize foundation system.
        """
        self.config = Config()
        self.startup_log = []
        self.server = None
        self.modules = {}
        self.config_failed = False
        self.wifi_mode = "AP"
        self.templates = TemplateSystem()
        self.server_ip = None
        
        # Create the single, shared I2C bus for all modules
        try:
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.startup_print("✓ I2C Bus initialized on GP5/GP4.")
        except Exception as e:
            self.i2c = None
            self.startup_print(f"✗ FAILED to initialize I2C bus: {e}")

    def startup_print(self, message):
        """
        Dual console/web logging for debugging.
        """
        print(message)
        self.startup_log.append(message)

    def decode_html_entities(self, text):
        """
        Clean web form input of HTML entities.
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
        """
        return self.modules.get(name)

    def safe_start_access_point(self, ssid, password):
        """
        Robust AP startup with fallback.
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
        """
        if self.wifi_mode != "AP":
            return True
            
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
        """
        try:
            self.startup_print("Loading user config...")
            toml_mode = os.getenv("WIFI_MODE")
            toml_ssid = os.getenv("WIFI_SSID")
            toml_password = os.getenv("WIFI_PASSWORD")
            toml_timeout = os.getenv("WIFI_AP_TIMEOUT_MINUTES")
            toml_blink = os.getenv("BLINK_INTERVAL")

            if toml_mode and toml_ssid and toml_password:
                self.startup_print("Found settings.toml, using TOML configuration")
                self.config.WIFI_MODE = "AP"
                self.config.WIFI_SSID = self.decode_html_entities(str(toml_ssid))
                self.config.WIFI_PASSWORD = self.decode_html_entities(str(toml_password))
                if toml_timeout: self.config.WIFI_AP_TIMEOUT_MINUTES = int(toml_timeout)
                if toml_blink: self.config.BLINK_INTERVAL = float(toml_blink)
                return

            self.startup_print("No complete settings.toml found, trying config.py")
            import config as user_config
            self.config.WIFI_SSID = self.decode_html_entities(str(user_config.WIFI_SSID))
            self.config.WIFI_PASSWORD = self.decode_html_entities(str(user_config.WIFI_PASSWORD))
            self.config.WIFI_AP_TIMEOUT_MINUTES = int(user_config.WIFI_AP_TIMEOUT_MINUTES)
            self.config.BLINK_INTERVAL = float(user_config.BLINK_INTERVAL)
        except Exception as e:
            self.startup_print(f"Config loading failed: {e}. Using emergency defaults.")
            self.config_failed = True
            self.config.WIFI_MODE = "AP"
            self.config.WIFI_SSID = "Wicdpico-Recovery"
            self.config.WIFI_PASSWORD = "emergency123"
            self.config.BLINK_INTERVAL = 0.10

    def initialize_network(self):
        """
        Initialize standalone AP mode network for sensor meter.
        """
        self.load_user_config()
        self.wifi_mode = "AP"
        self.startup_print("WiFi mode: AP (standalone sensor meter)")
        
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
        """
        self.modules[name] = module
        module.register_routes(self.server)

    def start_server(self):
        """
        Start web server and register the root dashboard route.
        """
        # --- ‼️ THIS IS THE NEW CODE ‼️ ---
        @self.server.route("/", methods=['GET'])
        def root_route(request: Request):
            """Serve the main dashboard page."""
            try:
                html_content = self.render_dashboard()
                return Response(request, html_content, content_type="text/html")
            except Exception as e:
                self.startup_print(f"Error rendering dashboard: {e}")
                return Response(request, "<h1>Error</h1><p>Could not render dashboard.</p>", content_type="text/html")
        # --- END OF NEW CODE ---

        self.server_ip = "192.168.4.1"
        self.server.start(self.server_ip, port=80)
        self.startup_print(f"Foundation ready at http://{self.server_ip}")

    def poll(self):
        """
        Performs a single poll cycle.
        """
        try:
            self.server.poll()
            for module in self.modules.values():
                module.update()
            check_wifi_timeout()
        except Exception as e:
            self.startup_print(f"Error in poll cycle: {e}")

    def run_main_loop(self):
        """
        Main polling loop with module updates.
        """
        while True:
            self.poll()
            time.sleep(0.1)
            gc.collect()

    def render_dashboard(self, title="Wicdpico Dashboard"):
        """
        Render complete dashboard with all modules.
        """
        modules_html = ""
        for name, module in self.modules.items():
            try:
                module_html = module.get_dashboard_html()
                if module_html:
                    modules_html += module_html
            except Exception as e:
                modules_html += f'<div class="module"><h3>{name}</h3><p>Error loading module: {e}</p></div>\n'

        system_info = f"""
            <p><strong>Sensor Meter:</strong> Standalone AP Mode</p>
            <p><strong>WiFi Hotspot:</strong> {self.config.WIFI_SSID}</p>
            <p><strong>Access URL:</strong> http://192.168.4.1</p>
            <p><strong>Modules loaded:</strong> {len(self.modules)}</p>
            <p><strong>System status:</strong> {'Configuration Error' if self.config_failed else 'Ready'}</p>
        """
        return self.templates.render_page(title, modules_html, system_info)

def shut_down_wifi_and_sleep():
    """Shuts down the Wi-Fi AP to save power after a timeout."""
    print("Initiating Wi-Fi AP shutdown due to inactivity...")
    try:
        if wifi.radio.enabled:
            wifi.radio.stop_ap()
            print("Wi-Fi AP shut down.")
        else:
            print("Wi-Fi AP already off.")
    except Exception as e:
        print(f"Error shutting down AP: {e}")

def check_wifi_timeout():
    """Checks if the AP has been inactive for too long and should be shut down."""
    global last_activity_time, ap_is_off_and_logged, timeout_disabled
    if timeout_disabled:
        return
    now = time.monotonic()
    if wifi.radio.enabled:
        elapsed = now - last_activity_time
        if elapsed > WIFI_TIMEOUT_SECONDS and not ap_is_off_and_logged:
            shut_down_wifi_and_sleep()
    else:
        if not ap_is_off_and_logged:
            ap_is_off_and_logged = True