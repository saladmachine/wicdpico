"""
Test application to verify LED Blinky module with foundation
"""
from src.foundation.core import PicowidFoundation
from src.modules.led_blinky import LEDBlinkyModule
from adafruit_httpserver import Request, Response

def main():
    # Initialize foundation
    foundation = PicowidFoundation()
    foundation.startup_print("Starting LED Blinky test...")
    
    # Initialize network
    if not foundation.initialize_network():
        foundation.startup_print("Network initialization failed!")
        return
    
    # Create and register LED module
    led_module = LEDBlinkyModule(foundation)
    foundation.register_module("led_blinky", led_module)
    
    # Add a simple home page route
    @foundation.server.route("/", methods=['GET'])
    def handle_root(request: Request):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Picowicd LED Test</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .module {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; }}
                button {{ padding: 10px 15px; margin: 5px; }}
            </style>
        </head>
        <body>
            <h1>Picowicd Foundation Test</h1>
            <p>Testing LED Blinky module integration</p>
            
            <div class="module">
                {led_module.get_dashboard_html()}
            </div>
            
            <div class="status">
                <h3>System Status</h3>
                <p>WiFi SSID: {foundation.config.WIFI_SSID}</p>
                <p>Network: http://192.168.4.1</p>
                <p>Modules loaded: {len(foundation.modules)}</p>
            </div>
        </body>
        </html>
        """
        return Response(request, html, content_type="text/html")
    
    # Start server and run
    foundation.start_server()
    foundation.startup_print("LED Blinky test ready!")
    foundation.run_main_loop()

if __name__ == "__main__":
    main()