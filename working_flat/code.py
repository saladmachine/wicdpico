"""
Test application to verify LED Blinky module with foundation
"""
from foundation_core import PicowidFoundation
from led_blinky import LEDBlinkyModule

from adafruit_httpserver import Request, Response

def main():
    # Initialize foundation
    foundation = PicowidFoundation()
    foundation.startup_print("Starting LED Blinky test...")
    
    # Initialize network
    if not foundation.initialize_network():
        foundation.startup_print("Network initialization failed!")
        return
    
    @foundation.server.route("/", methods=['GET'])
    def handle_root(request: Request):
        return Response(
            request, 
            foundation.render_dashboard("Picowicd LED Test"), 
            content_type="text/html"
        )

    # Start server and run
    foundation.start_server()
    foundation.startup_print("LED Blinky test ready!")
    foundation.run_main_loop()

if __name__ == "__main__":
    main()
