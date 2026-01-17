import board
import busio
import digitalio
import adafruit_sdcard
import storage
import os

print("\n--- SD Card Diagnostic Tool ---")
print("This script attempts to mount the SD card and list files.")
print("Verifying Pinout:")
print(f"SCK:  {board.GP18}")
print(f"MOSI: {board.GP19}")
print(f"MISO: {board.GP16}")
print(f"CS:   {board.GP17}")
print("-------------------------------")

# 1. SPI Initialization
try:
    print("1. Initializing SPI bus...", end="")
    spi = busio.SPI(board.GP18, board.GP19, board.GP16)
    print(" OK")
except Exception as e:
    print(f" FAIL\nError: {e}")

# 2. CS Initialization
try:
    print("2. Initializing Chip Select (CS)...", end="")
    cs = digitalio.DigitalInOut(board.GP17)
    print(" OK")
except Exception as e:
    print(f" FAIL\nError: {e}")

# 3. SD Card Shakehand (Try Native sdcardio first)
print("3. Talking to SD Card...")

# Attempt 1: Native sdcardio (Faster, Robust)
try:
    import sdcardio
    print("   [Attempt 1] Using native 'sdcardio'...", end="")
    # sdcardio requires the Pin object (board.GP17), NOT a DigitalInOut
    sdcard = sdcardio.SDCard(spi, board.GP17)
    print(" OK")
    
    print("4. Mounting Filesystem...", end="")
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd_test")
    print(" OK")
    
    print("\nSUCCESS! SD Card is working via 'sdcardio'.")
    print("Files on card:")
    print(os.listdir("/sd_test"))
    
except ImportError:
    print(" SKIP (sdcardio not available)")
    # Fallthrough to adafruit_sdcard
except Exception as e:
    print(f" FAIL ({e})")

    # Attempt 2: Adafruit Library (Fallback)
    try:
        print("   [Attempt 2] Using 'adafruit_sdcard' library...", end="")
        sdcard = adafruit_sdcard.SDCard(spi, cs, baudrate=250000)
        print(" OK")
        
        print("4. Mounting Filesystem...", end="")
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd_test")
        print(" OK")
        print("\nSUCCESS! SD Card is working via 'adafruit_sdcard'.")
        print(os.listdir("/sd_test"))

    except Exception as e2:
        print(f"\nFAIL: Both methods failed.")
        if "no SD card" in str(e2):
             print("Error: 'no SD card' - Hardware wiring/power issue.")

except Exception as e:
    print(f"\nFAIL: Unexpected error: {e}")
finally:
    print("\nDiagnostic complete.")
