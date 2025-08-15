# code_scd41.py - SCD41 CO2 Sensor Test Version
"""
Test SCD41 CO2, Temperature, and Humidity Sensor with working dashboard
"""
import gc
import time
import wifi

import supervisor
supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO SCD41 CO2 SENSOR TEST ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        if foundation.initialize_network():
            server_ip = "192.168.4.1" if foundation.wifi_mode == "AP" else str(wifi.radio.ipv4_address)
            
            # Load modules FIRST
            from module_scd41 import SCD41Module
            scd41 = SCD41Module(foundation)
            foundation.register_module("scd41", scd41)
            
            
            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # Fix foundation dashboard route
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    dashboard_html = foundation.render_dashboard("WicdPico SCD41 CO2 Sensor Test")
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print(f"Dashboard error: {e}")
                    return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")
            
            foundation.start_server()
            
            print(f"✓ Dashboard ready at: http://{server_ip}")
            print("✓ SCD41 CO2 sensor module loaded!")
            print("✓ Check dashboard for sensor status")
            print("✓ CO2 measurements may take a few seconds to stabilize")
            
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