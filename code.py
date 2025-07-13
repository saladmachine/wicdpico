#!/usr/bin/env python3
"""
Test your existing RTC module without the full foundation
"""

import time

# Mock foundation class for testing
class MockFoundation:
    def startup_print(self, message):
        print(f"[Foundation] {message}")

def main():
    print("=== Testing Your RTC Module ===")
    
    try:
        # Create mock foundation
        foundation = MockFoundation()
        
        # Import and test your module
        from rtc_control_module import RTCControlModule
        
        print("1. Creating RTC module...")
        rtc_module = RTCControlModule(foundation)
        print(f"   Module name: {rtc_module.name}")
        print(f"   RTC available: {rtc_module.rtc_available}")
        
        if rtc_module.rtc_available:
            print("\n2. Testing RTC functionality...")
            
            # Test direct RTC access
            current_time = rtc_module.rtc.datetime
            print(f"   Current time: {current_time}")
            
            # Test formatted display
            formatted_time = f"{rtc_module.days[current_time.tm_wday]} {current_time.tm_mon}/{current_time.tm_mday}/{current_time.tm_year} {current_time.tm_hour:02d}:{current_time.tm_min:02d}:{current_time.tm_sec:02d}"
            print(f"   Formatted: {formatted_time}")
            
            # Test status checks
            print(f"   Battery low: {rtc_module.rtc.battery_low}")
            print(f"   Lost power: {rtc_module.rtc.lost_power}")
            
            print("\n3. Testing update method...")
            rtc_module.update()
            
            print("\n✅ RTC module test completed successfully!")
            
        else:
            print("❌ RTC not available - check hardware connections")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure rtc_control_module.py and module_base.py are present")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()