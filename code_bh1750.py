# code_bh1750.py - BH1750 Light Sensor Test Version
"""
Test BH1750 Digital Light Sensor with working dashboard
"""
import gc
import time
import wifi

import supervisor
supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO BH1750 LIGHT SENSOR TEST ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        if foundation.initialize_network():
            server_ip = "192.168.4.1" if foundation.wifi_mode == "AP" else str(wifi.radio.ipv4_address)
            
            # Load modules FIRST
            from module_bh1750 import BH1750Module
            bh1750 = BH1750Module(foundation)
            foundation.register_module("bh1750", bh1750)
            
            
            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # Fix foundation dashboard route
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    dashboard_html = foundation.render_dashboard("WicdPico BH1750 Light Sensor Test")
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print(f"Dashboard error: {e}")
                    return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")
            
            foundation.start_server()
            
            print(f"✓ Dashboard ready at: http://{server_ip}")
            print("✓ BH1750 light sensor module loaded!")
            print("✓ Check dashboard for sensor status")
            
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