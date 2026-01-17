# code_rtc.py - RTC Module Test Harness
import gc
from foundation_core import WicdpicoFoundation
from module_rtc import RTCModule
import module_base 

def main():
    print("=== WICDPICO RTC MODULE TEST ===")
    
    foundation = WicdpicoFoundation()
    
    if foundation.initialize_network():
        # Instantiate and register the RTC module.
        rtc = RTCModule(foundation)
        foundation.register_module("rtc", rtc)
        
        # The foundation automatically handles the dashboard route.
        foundation.start_server()
        
        print("✓ RTC Test Dashboard ready. Access via browser.")
        if rtc.rtc_available:
            now = rtc.current_time
            if now and now.tm_year < 2025:
                print("⚠  RTC time appears to be unset. Please set it from the browser.")
            elif now:
                print("✓ RTC time is currently set.")
            else:
                 print("✗ Could not read from RTC.")
        
        # The foundation's main loop handles polling.
        foundation.run_main_loop()
            
    else:
        print("✗ Network initialization failed.")

if __name__ == "__main__":
    main()