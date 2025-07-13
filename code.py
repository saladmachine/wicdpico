#!/usr/bin/env python3
"""
Test SD Card Module - Step 1: Basic Hardware Detection
"""

import time
import gc

# Mock foundation class for testing (matching your RTC pattern)
class MockFoundation:
    def startup_print(self, message):
        print(f"[Foundation] {message}")

def main():
    print("=== Testing SD Card Module - Step 1 ===")
    
    try:
        # Create mock foundation
        foundation = MockFoundation()
        
        # Import and test SD card module
        from sd_card_module import SDCardModule
        
        print("1. Creating SD card module...")
        sd_module = SDCardModule(foundation)
        print(f"   Module name: {sd_module.name}")
        print(f"   Card available: {sd_module.card_available}")
        
        if sd_module.card_available:
            print("\n2. Testing SD card functionality...")
            
            # Test card status
            status = sd_module.get_card_status()
            print(f"   Available: {status['available']}")
            print(f"   Mount point: {status['mount_point']}")
            
            if status['card_info']:
                info = status['card_info']
                print(f"   Total space: {info['total_mb']} MB")
                print(f"   Free space: {info['free_mb']} MB")
                print(f"   Used space: {info['used_mb']} MB")
                print(f"   Usage: {info['usage_percent']}%")
            
            # Test storage info property
            storage_info = sd_module.storage_info
            if storage_info:
                print(f"   Storage info property working: {storage_info['total_mb']} MB total")
            
            print("\n3. Testing update method...")
            sd_module.update()
            
            print("\nSD card module test completed successfully!")
            
        else:
            print("SD card not available - check if SD card is inserted")
            print("This is normal if no SD card is present")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure sd_card_module.py and module_base.py are present")
    except Exception as e:
        print(f"Error during testing: {e}")
        import sys
        sys.print_exception(e)
    
    finally:
        # Clean up memory
        gc.collect()
        print(f"\nMemory free: {gc.mem_free()} bytes")

if __name__ == "__main__":
    main()