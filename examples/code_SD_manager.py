# code.py - Main entry point for the SD Manager

import sys
import gc
import time
from foundation_core import WicdpicoFoundation
from module_SD_manager import SDManagerModule
from adafruit_httpserver import Response

def main():
    print("=== WICDPICO SD MANAGER SYSTEM ===")
    foundation = WicdpicoFoundation()
    
    if foundation.initialize_network():
        # The module now handles its own hardware initialization.
        sd_manager = SDManagerModule(foundation)
        
        sd_manager.register_routes(foundation.server)
        
        @foundation.server.route("/", methods=['GET'])
        def root_route_handler(request):
            """Serves the SD manager page directly."""
            return sd_manager.files_page(request)

        foundation.start_server()
        print("✓ Server started. Access the SD Manager at http://192.168.4.1")
        
        while True:
            foundation.poll()
            gc.collect()
            
if __name__ == "__main__":
    main()