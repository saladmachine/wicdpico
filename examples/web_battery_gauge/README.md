# Web Battery Fuel Gauge Example

A practical demonstration of battery monitoring using the picowicd platform with Raspberry Pi Pico W, PicoWbell Adalogger (RTC + SD), and Pico Doubler (LiPo charging).

## Quick Start

### Hardware Required
- Raspberry Pi Pico W
- Adafruit PicoWbell Adalogger (RTC + SD card)
- Adafruit Pico Doubler with LiPo charging
- Small breadboard
- 2x 100kΩ resistors
- Jumper wires
- LiPo battery (any capacity)

### Basic Setup
1. Stack: Pico W → Adalogger → Doubler
2. Connect voltage divider on breadboard
3. Copy `code.py` to Pico W
4. Access web interface for real-time battery monitoring

## Features

- **Real-time battery voltage** via web dashboard
- **Charging status monitoring** from MCP73833 LEDs
- **Data logging** with RTC timestamps to SD card
- **Battery percentage calculation** with LiPo voltage curves
- **Field-ready design** for research applications

## Documentation

- [Hardware Setup Guide](docs/hardware_setup.md) - Detailed wiring instructions
- [Advanced Power Management](docs/advanced_power_management.md) - Ultra-low power designs
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Power Consumption

This example uses a simple voltage divider approach suitable for most applications:
- **Current draw**: ~21µA continuous
- **Battery life impact**: Negligible for >1000mAh batteries
- **Optimization**: See advanced documentation for ultra-low power scenarios

---

*This example demonstrates core picowicd platform capabilities while serving as a practical tool for field research battery monitoring.*