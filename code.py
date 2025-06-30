"""
Test application to verify LED Control module with foundation
"""
from foundation_core import PicowidFoundation
from led_control import LEDControlModule
from file_manager import FileManagerModule
from adafruit_httpserver import Request, Response

def main():
    # Initialize foundation
    foundation = PicowidFoundation()
    foundation.startup_print("Starting LED Control test...")

    # Initialize network
    if not foundation.initialize_network():
        foundation.startup_print("Network initialization failed!")
        return

    # Create and register LED module
    led_module = LEDControlModule(foundation)
    foundation.register_module("led_control", led_module)

    # Create and register File Manager module
    file_manager_module = FileManagerModule(foundation)
    foundation.register_module("file_manager", file_manager_module)

    @foundation.server.route("/", methods=['GET'])
    def handle_root(request: Request):
        return Response(
            request,
            foundation.render_dashboard("Picowicd LED Test"),
            content_type="text/html"
        )

    # Start server and run
    foundation.start_server()
    foundation.startup_print("LED Control test ready!")
    foundation.run_main_loop()

if __name__ == "__main__":
    main()