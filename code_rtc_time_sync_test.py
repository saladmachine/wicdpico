# code_rtc_time_sync_test.py - RTC Time Synchronization Test
"""
Test RTC time synchronization with browser time setting functionality
"""
import gc
import time
import wifi

import supervisor
supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO RTC TIME SYNCHRONIZATION TEST ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        if foundation.initialize_network():
            server_ip = "192.168.4.1" if foundation.wifi_mode == "AP" else str(wifi.radio.ipv4_address)
            
            # Load RTC module
            from module_rtc_control import RTCControlModule
            rtc = RTCControlModule(foundation)
            foundation.register_module("rtc", rtc)
            
            # Load LED control module for status
            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # Fix foundation dashboard route
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    dashboard_html = foundation.render_dashboard("WicdPico RTC Time Sync Test")
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print("Dashboard error: " + str(e))
                    return Response(request, "<h1>Dashboard Error</h1><p>" + str(e) + "</p>", content_type="text/html")
            
            foundation.start_server()
            
            print("✓ Dashboard ready at: http://" + server_ip)
            print("✓ RTC time synchronization module loaded!")
            if rtc.rtc_available:
                current_time = rtc.current_time
                if current_time:
                    print("✓ RTC current time: " + str(current_time.tm_year) + "/" + str(current_time.tm_mon) + "/" + str(current_time.tm_mday) + " " + str(current_time.tm_hour) + ":" + str(current_time.tm_min) + ":" + str(current_time.tm_sec))
                    if current_time.tm_year < 2020:
                        print("⚠  RTC time needs to be set (showing " + str(current_time.tm_year) + ")")
                else:
                    print("⚠  Could not read RTC time")
            else:
                print("✗ RTC not available")
            
            print("")
            print("Usage Instructions:")
            print("1. Connect to WiFi hotspot: PicoTest-Node00")
            print("2. Open browser to: http://" + server_ip)
            print("3. Click 'Get RTC Status' to see current time")
            print("4. Click 'Set Time from Browser' to sync RTC with your device's clock")
            print("5. Verify time is now correct with 'Get RTC Status'")
            print("")
            
            # Main loop
            while True:
                foundation.server.poll()
                for module in foundation.modules.values():
                    module.update()
                time.sleep(0.1)
                gc.collect()
                
        else:
            print("✗ Network failed")
            
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print("✗ Error: " + str(e))
        import sys
        sys.print_exception(e)

if __name__ == "__main__":
    main()
else:
    main()