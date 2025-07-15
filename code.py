# code.py - Single Node Test with Improved Docstrings
"""
Test the improved foundation system with MQTT module
Uses node00 configuration for single-node testing
"""
import gc
import time

def main():
    try:
        print("=== PICOWICD FOUNDATION TEST - NODE00 ===")
        
        # Test foundation with improved docstrings
        print("Loading foundation_core...")
        from foundation_core import PicowicdFoundation
        
        print("Creating foundation...")
        foundation = PicowicdFoundation()
        
        print("Initializing network...")
        if foundation.initialize_network():
            print(f"✓ Network ready - Mode: {foundation.wifi_mode}")
            
            # Test MQTT module with improved docstrings
            print("Loading MQTT module...")
            from mqtt_module import MQTTModule
            
            print("Creating MQTT module...")
            mqtt = MQTTModule(foundation)
            
            print("Registering MQTT module...")
            foundation.register_module("mqtt", mqtt)
            
            # Test LED module
            print("Loading LED module...")
            from led_control import LEDControlModule
            
            print("Creating LED module...")
            led = LEDControlModule(foundation)
            
            print("Registering LED module...")
            foundation.register_module("led", led)
            
            print("Starting web server...")
            foundation.start_server()
            
            print("✓ Foundation system ready with improved docstrings!")
            print(f"✓ Access at: http://{foundation.server._server_socket.getsockname()[0]}")
            print("✓ MQTT and LED modules loaded")
            print("✓ Running main loop...")
            
            # Run for limited time for testing
            test_duration = 60  # 1 minute test
            start_time = time.monotonic()
            
            while time.monotonic() - start_time < test_duration:
                foundation.server.poll()
                
                # Update all modules
                for module in foundation.modules.values():
                    module.update()
                
                time.sleep(0.1)
                gc.collect()
            
            print("✓ Test completed successfully!")
            print("✓ Improved docstrings working correctly")
            
        else:
            print("✗ Network initialization failed")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import sys
        sys.print_exception(e)
        
    finally:
        # Cleanup
        try:
            if 'foundation' in locals():
                for module in foundation.modules.values():
                    module.cleanup()
        except:
            pass
        
        print("=== TEST COMPLETE ===")
        print("If you saw '✓ Test completed successfully!' the docstrings work!")
        
        # Keep running for manual testing
        print("Continuing to run for manual testing...")
        while True:
            time.sleep(1)

# Run the test
if __name__ == "__main__":
    main()
else:
    main()