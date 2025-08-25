# code_sd_card_test.py - SD Card Test with PicoBell Adalogger
"""
Test SD card functionality with proper SPI mounting on PicoBell Adalogger.
Generates 5x5 test data matrix and provides web interface for testing.
"""
import gc
import time
import wifi

import supervisor
supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO SD CARD TEST - PICOBELL ADALOGGER ===")
        
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()
        
        if foundation.initialize_network():
            server_ip = "192.168.4.1" if foundation.wifi_mode == "AP" else str(wifi.radio.ipv4_address)
            
            # Load SD Card Test module
            from module_sd_card_test import SDCardTestModule
            sd_test = SDCardTestModule(foundation)
            foundation.register_module("sd_test", sd_test)
            
            # Load LED control module for status
            from module_led_control import LEDControlModule
            led = LEDControlModule(foundation)
            foundation.register_module("led", led)
            
            # Fix foundation dashboard route
            from adafruit_httpserver import Response
            
            @foundation.server.route("/", methods=['GET'])
            def serve_dashboard(request):
                try:
                    dashboard_html = foundation.render_dashboard("WicdPico SD Card Test - PicoBell Adalogger")
                    return Response(request, dashboard_html, content_type="text/html")
                except Exception as e:
                    print("Dashboard error: " + str(e))
                    return Response(request, "<h1>Dashboard Error</h1><p>" + str(e) + "</p>", content_type="text/html")
            
            foundation.start_server()
            
            print("✓ Dashboard ready at: http://" + server_ip)
            print("✓ SD Card Test module loaded!")
            
            if sd_test.mounted:
                print("✓ SD card mounted successfully to /sd")
                storage_info = sd_test.get_sd_storage_info()
                if storage_info:
                    print("✓ Storage: " + str(storage_info['total_mb']) + " MB total, " + str(storage_info['free_mb']) + " MB free")
                print("✓ Test data generated: 5x5 sensor matrix")
            else:
                print("✗ SD card mounting failed")
            
            print("")
            print("Hardware Setup - PicoBell Adalogger:")
            print("- SPI SCK: GP18 (Pin 24)")
            print("- SPI MOSI: GP19 (Pin 25)")  
            print("- SPI MISO: GP16 (Pin 21)")
            print("- SPI CS: GP17 (Pin 22)")
            print("")
            print("Test Features:")
            print("- Proper SPI mounting to /sd directory")
            print("- 5x5 test data generation (temp + humidity)")
            print("- Automatic data updates every 30 seconds")
            print("- Web interface for file operations")
            print("- CSV download functionality")
            print("")
            print("Usage Instructions:")
            print("1. Connect to WiFi hotspot: PicoTest-Node00")
            print("2. Open browser to: http://" + server_ip)
            print("3. Click 'Get SD Status' to verify mounting")
            print("4. Click 'List Files' to see SD card contents")
            print("5. Click 'Download Test Data' to test file streaming")
            print("6. Monitor for automatic data updates every 30 seconds")
            
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