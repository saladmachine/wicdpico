# system_darkbox.py

import time
import gc

from foundation_core import WicdpicoFoundation

def main():
    print("=== WICDPICO DARKBOX SYSTEM v1.0 ===")
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        # Import all necessary modules
        from module_scd41 import SCD41Module
        from module_bh1750 import BH1750Module
        from module_emc2101 import Emc2101Module
        from module_battery_monitor import BatteryMonitorModule
        from module_rtc import RTCModule
        from module_SD_manager import SDManagerModule
        from module_datalogger import DataloggerModule
        
        # 1. FOUNDATIONAL SERVICES (Must be first for dependency chain)
        
        # A. RTC: Provides time for all logging modules
        rtc = RTCModule(foundation)
        foundation.register_module("rtc", rtc)
        
        # B. SD Manager: Mounts the file system for all logging modules
        sd_manager = SDManagerModule(foundation)
        foundation.register_module("sd_manager", sd_manager)

        # 2. CORE SENSOR MODULES (Can be loaded in any order now)
        
        scd41 = SCD41Module(foundation)
        foundation.register_module("scd41", scd41)

        bh1750 = BH1750Module(foundation)
        foundation.register_module("bh1750", bh1750)

        # 3. PERIPHERAL & LOGGING MODULES (Rely on RTC/SD for full functionality)

        emc2101_module = Emc2101Module(foundation)
        foundation.register_module("emc2101", emc2101_module)

        battery_monitor = BatteryMonitorModule(foundation)
        foundation.register_module("battery", battery_monitor)
        
        datalogger = DataloggerModule(foundation)
        foundation.register_module("datalogger", datalogger)

        # Start the web server and dashboard route (via foundation)
        foundation.start_server()
        print("✓ Darkbox dashboard ready. Access via browser.")

        # Main loop: poll the server
        while True:
            foundation.poll()
            time.sleep(0.1)
            gc.collect()

if __name__ == "__main__":
    main()