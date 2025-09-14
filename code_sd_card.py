import supervisor
import time
import gc

supervisor.runtime.autoreload = False

def main():
    try:
        print("=== WICDPICO SD CARD MODULE DEMO ===")
        from foundation_core import WicdpicoFoundation
        foundation = WicdpicoFoundation()

        if foundation.initialize_network():
            from module_sd_card import SDCardModule
            sdcard = SDCardModule(foundation)
            foundation.register_module("sdcard", sdcard)
            sdcard.register_routes(foundation.server)
            foundation.start_server()
            print("✓ SD Card dashboard ready. Access via browser.")

            # Use the same pattern as your working code: only interact with files that already exist,
            # avoid creating/deleting files unless you know the SD card is writable.
            print("Listing files...")
            files = sdcard.list_directory(sdcard.mount_point)
            print("Files:", [f['name'] for f in files])

            # Pick an existing file for demonstration
            demo_file = None
            for f in files:
                if f['type'] == 'file':
                    demo_file = f['path']
                    break

            if demo_file:
                print(f"Reading file: {demo_file}")
                content = sdcard.read_file(demo_file)
                print("Content:", content)

                print(f"Saving file: {demo_file}")
                saved = sdcard.write_file(demo_file, "Updated content.", append=False)
                print("Save result:", saved)

                print(f"Reading updated file: {demo_file}")
                updated_content = sdcard.read_file(demo_file)
                print("Updated content:", updated_content)
            else:
                print("No file found to demonstrate read/write.")

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