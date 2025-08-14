#!/bin/bash
set -e

# Find CIRCUITPY mount point automatically
CIRCUITPY_PATH=$(find /media -name "CIRCUITPY" -type d 2>/dev/null | head -n1)

if [ -z "$CIRCUITPY_PATH" ]; then
    echo "ERROR: CIRCUITPY drive not found. Is Pico W connected?"
    exit 1
fi

echo "Deploying wicdpico to $CIRCUITPY_PATH..."
rsync -av lib/ "$CIRCUITPY_PATH/lib/"
cp tests/test_led_blinky.py "$CIRCUITPY_PATH/code.py"
echo "Deployment complete! Reset Pico W to run."
