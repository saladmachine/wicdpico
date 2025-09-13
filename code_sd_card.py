import supervisor
import time
import gc

supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO SD CARD MODULE ===")
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()

        if foundation.initialize_network():
            from module_sd_card import SDCardModule
            sdcard = SDCardModule(foundation)
            foundation.register_module("sdcard", sdcard)

            # Register all module routes
            sdcard.register_routes(foundation.server)

            foundation.start_server()
            print("✓ SD Card dashboard ready. Access via browser.")

            while True:
                foundation.server.poll()
                sdcard.update()
                time.sleep(0.1)
                gc.collect()
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()