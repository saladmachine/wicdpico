# code_water_level.py - FS-IR02B Water Level Sensor Test Version
"""
Test EPT Technology FS-IR02B Water Level Sensor with working dashboard
"""
import gc
import time
import wifi

import supervisor
supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO FS-IR02B WATER LEVEL SENSOR TEST ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        if foundation.initialize_network():
            server_ip = "192.168.4.1" if foundation.wifi_mode == "AP" else str(wifi.radio.ipv4_address)
            
            # Load modules FIRST
            from module_water_level import WaterLevelModule
            # Use GP6 for water level sensor signal (you can change this pin as needed)
            water_level = WaterLevelModule(foundation, gpio_pin="GP6")
            foundation.register_module("water_level", water_level)
            
            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # Fix foundation dashboard route
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    dashboard_html = foundation.render_dashboard("WicdPico FS-IR02B Water Level Sensor Test")
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print(f"Dashboard error: {e}")
                    return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")
            
            foundation.start_server()
            
            print(f"✓ Dashboard ready at: http://{server_ip}")
            print("✓ FS-IR02B water level sensor module loaded!")
            print(f"✓ Sensor configured on pin: {water_level.gpio_pin_name}")
            print("✓ Check dashboard for sensor status")
            print("")
            print("Hardware Setup:")
            print("- VCC: Connect to 3V3 (Pin 36)")
            print("- GND: Connect to GND (Pin 38)")
            print(f"- Signal: Connect to {water_level.gpio_pin_name}")
            print("")
            print("Sensor Features:")
            print("- Water presence detection")
            print("- Automatic refill event logging")
            print("- Real-time monitoring")
            print("- Web-based control interface")
            
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
        print(f"✗ Error: {e}")
        import sys
        sys.print_exception(e)

if __name__ == "__main__":
    main()
else:
    main()