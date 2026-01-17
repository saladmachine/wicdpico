# code_battery_monitor.py
import gc
from foundation_core import WicdpicoFoundation
from module_battery_monitor import BatteryMonitorModule
# This file is now required
import module_base 

def main():
    print("=== WICDPICO BATTERY MONITOR - POWER DETECTION ===")
    foundation = WicdpicoFoundation()

    if foundation.initialize_network():
        battery = BatteryMonitorModule(foundation)
        foundation.register_module("battery", battery)

        foundation.start_server()

        print("✓ Battery Monitor dashboard ready. Access via browser.")
        if battery.voltage_available:
            initial_voltage = battery.get_voltage()
            # New: Print the initial detected power state
            initial_state = battery.power_state
            if initial_voltage:
                print("✓ Initial voltage: {}V. Initial power source: {}".format(initial_voltage, initial_state))
        else:
            print("✗ Voltage monitoring unavailable")

        foundation.run_main_loop()

if __name__ == "__main__":
    main()