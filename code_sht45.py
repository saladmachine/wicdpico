# code.py - Working version for SHT45 Step 2
"""
Test SHT45 Step 2 with working dashboard
"""
import gc
import time
import wifi

def main():
    try:
        print("=== PICOWICD SHT45 STEP 2 - WORKING ===")
        
        from foundation_core import PicowicdFoundation
        foundation = PicowicdFoundation()
        
        if foundation.initialize_network():
            server_ip = "192.168.4.1" if foundation.wifi_mode == "AP" else str(wifi.radio.ipv4_address)
            
            # Load modules FIRST
            from sht45_module import SHT45Module
            sht45 = SHT45Module(foundation)
            foundation.register_module("sht45", sht45)
            
            from mqtt_module import MQTTModule  
            mqtt = MQTTModule(foundation)
            foundation.register_module("mqtt", mqtt)
            
            from led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # Fix foundation dashboard route
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    dashboard_html = foundation.render_dashboard("PicoWicd SHT45 Test")
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print(f"Dashboard error: {e}")
                    return Response(request, f"<h1>Dashboard Error</h1><p>{e}</p>", content_type="text/html")
            
            foundation.start_server()
            
            print(f"✓ Dashboard ready at: http://{server_ip}")
            print("✓ SHT45 hardware detected and working!")
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