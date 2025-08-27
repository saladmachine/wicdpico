#!/bin/bash
set -e

# Find CIRCUITPY mount point automatically
CIRCUITPY_PATH=$(find /media -name "CIRCUITPY" -type d 2>/dev/null | head -n1)

if [ -z "$CIRCUITPY_PATH" ]; then
    echo "ERROR: CIRCUITPY drive not found. Is Pico W connected?"
    exit 1
fi

echo "Deploying wicdpico to $CIRCUITPY_PATH..."

# Copy library files
echo "Copying libraries..."
rsync -av lib/ "$CIRCUITPY_PATH/lib/"

# Copy all module files
echo "Copying modules..."
cp module_*.py "$CIRCUITPY_PATH/"

# Copy foundation files
echo "Copying foundation..."
cp foundation_*.py "$CIRCUITPY_PATH/"

# Copy configuration files
echo "Copying configuration..."
cp settings.toml "$CIRCUITPY_PATH/"

# Copy current code.py (if it exists and isn't a test)
if [ -f code.py ] && [ "$(basename code.py)" != "test_led_blinky.py" ]; then
    echo "Copying current code.py..."
    cp code.py "$CIRCUITPY_PATH/"
else
    echo "No custom code.py found, copying water level test..."
    cp code_water_level.py "$CIRCUITPY_PATH/code.py"
fi

echo "Deployment complete! Files copied to $CIRCUITPY_PATH"
echo "Reset Pico W to run the new code."
