# system_wicdair.py
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
WicdAir System Entry Point
==========================
Orchestrates the WicdAir air quality monitor application.
Composes the Foundation with SCD30 and other modules.
"""

import time
import board
from foundation_core import WicdpicoFoundation, WicdHardwareConfig

# module_wifi_manager.py
from module_wifi_manager import WifiManagerModule
from module_scd30 import SCD30Module
from module_SD_manager import SDManagerModule
from module_rtc import RTCModule
from module_datalogger import DataloggerModule
from module_live_chart import LiveChartModule
from module_battery_monitor import BatteryMonitorModule

def main():
    print("--- WicdAir System Starting ---")
    
    # 1. Initialize Foundation (and shared hardware resources)
    # Using default hardware config (Pico 2 W standard)
    hw_config = WicdHardwareConfig() 
    foundation = WicdpicoFoundation(hw_config)
    
    # 2.Initialize Network
    # This loads settings.toml, starts AP, and sets up the server
    if not foundation.initialize_network():
        print("CRITICAL: Network initialization failed.")
        # We continue anyway to at least try to log data or show error on local display if one existed
    
    # 3. Instantiate Modules
    # Pass the foundation (which holds the shared I2C bus)
    
    # Wi-Fi Manager (Hotspot timeout control)
    wifi_manager = WifiManagerModule(foundation)
    
    # SCD30 (Primary CO2/Temp/Humidity Sensor)
    # The foundation initializes the I2C bus on foundation.i2c
    scd30 = SCD30Module(foundation.i2c)
    
    # SD Card Manager
    sd_manager = SDManagerModule(foundation)
    
    # RTC Clock (Heartbeat)
    rtc = RTCModule(foundation)
    
    # Data Logger (Logic)
    logger = DataloggerModule(foundation)
    
    # Live Chart (Zero-risk visualizer)
    live_chart = LiveChartModule()

    # Battery Monitor (Hardware verified)
    battery_monitor = BatteryMonitorModule(foundation)
    
    # 4. Register Modules with Foundation
    # The order here determines the order on the dashboard
    foundation.register_module("wifi_manager", wifi_manager)
    foundation.register_module("logger", logger) # Controls near top
    foundation.register_module("rtc", rtc) 
    foundation.register_module("scd30", scd30)
    foundation.register_module("sd_manager", sd_manager)
    foundation.register_module("live_chart", live_chart)
    foundation.register_module("battery", battery_monitor)
        
    # 5. Start Server
    foundation.start_server()
    
    # 6. Enter Main Loop
    print("--- WicdAir System Running ---")
    foundation.run_main_loop()

if __name__ == "__main__":
    main()
