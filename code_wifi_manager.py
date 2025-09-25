# code_wifi_manager.py
import gc
from foundation_core import WicdpicoFoundation
from module_wifi_manager import WifiManagerModule

def main():
    print("=== WICDPICO WIFI MANAGER TEST ===")
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        # Instantiate and register the module.
        # The foundation's register_module method now also handles route registration.
        wifi_manager = WifiManagerModule(foundation)
        foundation.register_module("wifi_manager", wifi_manager)

        # The foundation now creates the root dashboard route automatically.
        foundation.start_server()
        print("✓ WiFi Manager test dashboard ready. Access via browser.")
        
        # The foundation's main loop handles polling the server and modules.
        foundation.run_main_loop()

if __name__ == "__main__":
    main()