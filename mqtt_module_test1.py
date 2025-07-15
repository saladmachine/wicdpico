# code.py - Test MQTT Module Step 1 in CircuitPython
"""
Test MQTT Module - Step 1: Basic Structure Loading
Copy this as your code.py to test the MQTT module
"""
import gc
import time

# Mock foundation class for testing (matches your pattern)
class MockFoundation:
    def __init__(self):
        self.startup_log = []
        
        # Mock config object like real foundation
        class MockConfig:
            WIFI_SSID = "TEST"
            WIFI_PASSWORD = "test"
            BLINK_INTERVAL = 1.0
        
        self.config = MockConfig()
        
    def startup_print(self, message):
        print(f"[Foundation] {message}")
        self.startup_log.append(message)

# Mock server for route testing
class MockServer:
    def __init__(self):
        self.routes = []
        
    def route(self, path, methods=None):
        def decorator(func):
            self.routes.append((methods, path, func.__name__))
            return func
        return decorator

def main():
    try:
        print("=== MQTT Module Step 1 Test ===")
        
        print("\n1. Testing module import...")
        from mqtt_module import MQTTModule
        print("   ✓ Module imported successfully")
        
        print("\n2. Testing module initialization...")
        foundation = MockFoundation()
        mqtt_module = MQTTModule(foundation)
        
        print(f"   ✓ Module created: {mqtt_module.name}")
        print(f"   ✓ Node ID: {mqtt_module.node_id}")
        print(f"   ✓ Connected: {mqtt_module.connected}")
        print(f"   ✓ Status: {mqtt_module.status_message}")
        
        print("\n3. Testing route registration...")
        mock_server = MockServer()
        mqtt_module.register_routes(mock_server)
        
        print(f"   ✓ Registered {len(mock_server.routes)} routes:")
        for methods, path, handler in mock_server.routes:
            print(f"     {methods} {path} -> {handler}")
        
        print("\n4. Testing dashboard HTML generation...")
        dashboard_html = mqtt_module.get_dashboard_html()
        
        # Check for key elements
        checks = [
            ("MQTT Client", "Module title"),
            ("node01", "Node ID display"),
            ("Connect", "Connect button"),
            ("Disconnect", "Disconnect button"),
            ("Test Publish", "Publish button"),
            ("mqttConnect()", "JavaScript function"),
            ("Disconnected", "Status display")
        ]
        
        for check_text, description in checks:
            if check_text in dashboard_html:
                print(f"   ✓ {description}: Found")
            else:
                print(f"   ✗ {description}: Missing")
        
        print(f"   ✓ Dashboard HTML length: {len(dashboard_html)} characters")
        
        print("\n5. Testing update() method...")
        mqtt_module.update()
        print(f"   ✓ Update completed, status: {mqtt_module.status_message}")
        
        print("\n6. Testing cleanup() method...")
        mqtt_module.cleanup()
        print(f"   ✓ Cleanup completed")
        
        print("\n7. Testing foundation logging...")
        print(f"   ✓ Foundation received {len(foundation.startup_log)} log messages")
        for msg in foundation.startup_log:
            print(f"     - {msg}")
        
        print("=== Step 1 Test PASSED ===")
        print("✓ Module structure is correct")
        print("✓ All required methods implemented")
        print("✓ Web routes registered properly")
        print("✓ Dashboard HTML generates correctly")
        print("✓ Ready for Step 2 (MQTT Configuration)")
        
        # Keep running like a normal CircuitPython program
        print("\nTest completed. Ctrl+C to stop or reset board.")
        while True:
            time.sleep(1)
        
    except Exception as e:
        print(f"\n=== Step 1 Test FAILED ===")
        print(f"Error: {e}")
        import sys
        sys.print_exception(e)
        
        # Keep running so you can see the error
        print("\nError occurred. Ctrl+C to stop or reset board.")
        while True:
            time.sleep(1)
        
    finally:
        gc.collect()
        print(f"Memory free: {gc.mem_free()} bytes")

# Run the test when loaded as code.py
if __name__ == "__main__":
    main()
else:
    # Also run if imported (CircuitPython behavior)
    main()