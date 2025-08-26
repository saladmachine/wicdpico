# code_battery_monitor.py - Battery Monitor Test with Internal VSYS
"""
Test Battery Monitor with internal VSYS voltage monitoring.
Provides load testing and voltage logging capabilities.
"""
import gc
import time
import wifi

import supervisor
supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO BATTERY MONITOR - INTERNAL VSYS ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        if foundation.initialize_network():
            server_ip = "192.168.4.1" if foundation.wifi_mode == "AP" else str(wifi.radio.ipv4_address)
            
            # Load Battery Monitor module
            from module_battery_monitor import BatteryMonitorModule
            battery = BatteryMonitorModule(foundation)
            foundation.register_module("battery", battery)
            
            # Load LED control module for load testing
            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # Connect LED module to battery monitor for load testing
            battery.led_module = led
            
            # Fix foundation dashboard route
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    dashboard_html = foundation.render_dashboard("WicdPico Battery Monitor Test")
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print("Dashboard error: " + str(e))
                    return Response(request, "<h1>Dashboard Error</h1><p>" + str(e) + "</p>", content_type="text/html")
            
            foundation.start_server()
            
            print("✓ Dashboard ready at: http://" + server_ip)
            print("✓ Battery monitor using internal VSYS monitoring")
            
            if battery.voltage_available:
                initial_voltage = battery.get_voltage()
                if initial_voltage:
                    print("✓ Initial voltage reading: " + str(initial_voltage) + "V")
            else:
                print("✗ Voltage monitoring unavailable")
            
            print("")
            print("Hardware Setup:")
            print("- Uses internal VOLTAGE_MONITOR pin")
            print("- No external ADC required")
            print("- Battery connects to VSYS rail")
            print("")
            print("Test Features:")
            print("- Real-time voltage monitoring")
            print("- High-power load testing (LED + CPU load)")
            print("- Voltage logging with web display")
            print("- Web-based control interface")
            print("")
            print("Usage Instructions:")
            print("1. Connect to WiFi hotspot: PicoTest-Node00")
            print("2. Open browser to: http://" + server_ip)
            print("3. Click 'Get Voltage' for current battery reading")
            print("4. Click 'Toggle Load Test' to start/stop power consumption test")
            print("5. Click 'Toggle Logging' to start/stop voltage data collection")
            print("6. Load test uses rapid LED blinking + CPU activity")
            
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