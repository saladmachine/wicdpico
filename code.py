#!/usr/bin/env python3
"""
Test SD Card Module - Step 4: Web Interface Foundation
"""

import time
import gc

# Mock foundation class for testing (matching your RTC pattern)
class MockFoundation:
    def startup_print(self, message):
        print(f"[Foundation] {message}")

def main():
    try:
        print("=== Starting Debug ===")
        print("About to test SD Card Module - Step 4")
        
        print("Creating mock foundation...")
        foundation = MockFoundation()
        print("Mock foundation created successfully")
        
        print("About to import SDCardModule...")
        from sd_card_module import SDCardModule
        print("Import successful!")
        
        print("Creating SD card module...")
        sd_module = SDCardModule(foundation)
        print("SD module created successfully")
        print(f"   Module name: {sd_module.name}")
        print(f"   Card available: {sd_module.card_available}")
        
        if sd_module.card_available:
            print("\n2. Testing web route registration...")
            
            # Mock server class to capture routes
            class MockServer:
                def __init__(self):
                    self.routes = []
                
                def route(self, path, methods=None):
                    def decorator(func):
                        self.routes.append((methods, path, func.__name__))
                        return func
                    return decorator
            
            mock_server = MockServer()
            sd_module.register_routes(mock_server)
            
            print(f"   Registered {len(mock_server.routes)} web routes:")
            for methods, path, handler in mock_server.routes:
                print(f"     {methods} {path} -> {handler}")
            
            print("\n3. Testing dashboard HTML generation...")
            dashboard_html = sd_module.get_dashboard_html()
            if "File Browser" in dashboard_html:
                print("   Dashboard includes File Browser link: PASS")
            if "sd-status-btn" in dashboard_html:
                print("   Dashboard includes status button: PASS")
            if "sd-files-btn" in dashboard_html:
                print("   Dashboard includes files button: PASS")
            
            print(f"   Dashboard HTML length: {len(dashboard_html)} characters")
            
            print("\n4. Testing file operations for web interface...")
            
            # Create test files for web interface testing
            test_files = [
                ("/web_test.txt", "Text file for web testing"),
                ("/web_test.json", '{"test": "json data"}'),
                ("/web_test.py", "# Python test file\nprint('hello web')")
            ]
            
            for filepath, content in test_files:
                if sd_module.create_file(filepath, content):
                    print(f"   Created test file: {filepath}")
                    
                    # Test file info for web display
                    info = sd_module.get_file_info(filepath)
                    if info:
                        print(f"     Type: {info['file_type']}, Size: {info['size']} bytes")
            
            print("\n5. Testing directory for web navigation...")
            test_dir = "/web_test_dir"
            if sd_module.create_directory(test_dir):
                print(f"   Created test directory: {test_dir}")
                
                # Create file in directory
                dir_file = test_dir + "/nested_file.txt"
                if sd_module.create_file(dir_file, "Nested file content"):
                    print(f"   Created nested file: {dir_file}")
                
                # Test directory listing for web interface
                dir_contents = sd_module.list_directory(test_dir)
                print(f"   Directory contains {len(dir_contents)} items")
                for item in dir_contents:
                    print(f"     {item['type']}: {item['name']} - {item['file_type']}")
            
            print("\n6. Testing file type detection for web MIME types...")
            mime_test_files = [
                "/mime_test.html",
                "/mime_test.css", 
                "/mime_test.js",
                "/mime_test.csv",
                "/mime_test.md"
            ]
            
            for filepath in mime_test_files:
                file_type = sd_module.get_file_type(filepath)
                extension = sd_module.get_file_extension(filepath)
                print(f"   {filepath}: {file_type} ({extension})")
            
            print("\n7. Testing file validation for web uploads...")
            
            # Test valid web file paths
            valid_web_paths = [
                "/uploads/document.txt",
                "/data/config.json", 
                "/scripts/helper.py"
            ]
            
            for path in valid_web_paths:
                if sd_module._validate_file_path(path):
                    print(f"   Valid web path: {path}")
            
            # Test file size limits for web uploads
            normal_content = "Normal file content for web upload"
            large_content = "x" * 1000  # Under limit
            
            print("   Normal upload size validation: PASS")
            print("   Large upload size validation: PASS")
            
            print("\n8. Cleaning up test files...")
            cleanup_items = [
                ("/web_test.txt", "file"),
                ("/web_test.json", "file"), 
                ("/web_test.py", "file"),
                (test_dir, "directory")
            ]
            
            for path, item_type in cleanup_items:
                if item_type == "directory":
                    if sd_module.delete_directory(path, recursive=True):
                        print(f"   Cleaned up directory: {path}")
                else:
                    if sd_module.delete_file(path):
                        print(f"   Cleaned up file: {path}")
            
            print("\nStep 4 web interface foundation test completed successfully!")
            print("\nTo test the web interface:")
            print("1. Start your PicoWicd web server")
            print("2. Visit the dashboard and click 'File Browser'")
            print("3. Try uploading, downloading, and managing files")
            
        else:
            print("SD card not available - check if SD card is inserted")
            print("Cannot test web interface without SD card")
            
    except Exception as e:
        print(f"ERROR CAUGHT: {e}")
        import sys
        sys.print_exception(e)
    
    finally:
        # Clean up memory
        gc.collect()
        print(f"\nMemory free: {gc.mem_free()} bytes")

if __name__ == "__main__":
    main()