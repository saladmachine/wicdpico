# WicdPico: Modular CircuitPython Sensor Platform

**Transform your Raspberry Pi Pico 2 W into a versatile wireless sensor meter with web-based control.**

## Overview

WicdPico is a modular platform for building I2C sensor instruments that serve interactive web dashboards. Perfect for environmental monitoring, data logging, and laboratory instrumentation - all accessible through any web browser.

## Key Features

✅ **Standalone Operation** - Creates its own WiFi hotspot (no network required)  
✅ **Web-Based Dashboard** - Control via phone, tablet, or laptop browser  
✅ **Modular Architecture** - Mix and match sensor/control modules  
✅ **Built-in Web IDE** - Edit code directly through web interface  
✅ **Data Logging** - Timestamped data to SD card  
✅ **I2C Sensor Support** - Temperature, humidity, CO2, light sensors  

## Quick Start

1. **Flash CircuitPython 9.0+** to your Pico 2 W
2. **Copy files** to CIRCUITPY drive:
   ```bash
   git clone https://github.com/saladmachine/wicdpico.git
   cp wicdpico/*.py /media/CIRCUITPY/
   cp wicdpico/settings.toml /media/CIRCUITPY/
   ```
3. **Connect to WiFi** hotspot "PicoTest-Node00" (password: testpass123)
4. **Open browser** to http://192.168.4.1
5. **View dashboard** with live sensor data and controls

## Modular System

### Available Modules
- **`module_sht45.py`** - Temperature/humidity sensor (SHT45)
- **`module_led_control.py`** - Onboard LED control and status
- **`module_rtc_control.py`** - Real-time clock (PCF8523)
- **`module_sd_card.py`** - SD card data logging
- **`module_battery_monitor.py`** - Battery voltage monitoring
- **`module_file_manager.py`** - Web-based file editor
- **`module_console_monitor.py`** - Web-based REPL console

### Development Workflow

**1. Individual Module Testing**
```bash
# Test single sensor
cp templates/code_sht45_only.py code.py

# Test web IDE  
cp templates/code_ide_complete.py code.py
```

**2. Multi-Module Combinations** 
```bash
# Data logging setup
cp templates/code_sht45_rtc_sd.py code.py

# Full production system
cp templates/code_production.py code.py
```

**3. Custom Module Development**
- Create `module_mynewsensor.py` inheriting from `WicdpicoModule`
- Implement sensor reading, web interface, and dashboard widget
- Register in your `code.py` configuration

## Example Applications

**🌡️ Environmental Monitor** - SHT45 + RTC + SD logging  
**🔧 Web-Based IDE** - Code editor + file manager + console  
**🔋 Battery Meter** - Voltage monitoring + status dashboard  
**📊 Multi-Sensor Dashboard** - Multiple I2C devices on one interface  

*Detailed examples and hardware setup guides coming soon in `/docs/examples/`*

## File Structure

```
wicdpico/
├── code.py                      # ← Main application (copy target)
├── foundation_core.py           # Core framework
├── module_base.py              # Module base class
├── settings.toml               # Configuration
├── module_*.py                 # All sensor/control modules
└── templates/                  # Code configurations (coming soon)
    ├── code_sht45_only.py     # Single sensor test
    ├── code_ide_complete.py   # Web IDE setup
    └── code_production.py     # All modules
```

## Hardware Compatibility

**Tested Hardware:**
- Raspberry Pi Pico 2 W
- Adafruit SHT45 temperature/humidity sensor  
- PCF8523 RTC breakout
- MicroSD card breakouts
- Various I2C sensors and devices

**Connections:**
- **I2C**: GP4 (SDA), GP5 (SCL)
- **SD Card**: SPI interface
- **Power**: USB or battery via STEMMA connector

## Contributing

This project follows a pragmatic approach optimized for CircuitPython constraints:

- **Modules in root directory** - Avoids CircuitPython import issues
- **Template-based testing** - Copy/paste workflow for different configurations  
- **Simple architecture** - Prioritizes reliability over abstraction
- **Hardware-first design** - Built for real sensor applications

## License

MIT License - Build amazing sensor instruments!

---

Acknowledgments
Built with CircuitPython and adafruit_httpserver.

AI Assistance Note: This project, including aspects of its code (e.g., structure, debugging assistance, error handling enhancements) and the drafting of this README.md, was significantly assisted by large language models, specifically Gemini by Google and Claude by Anthropic. This collaboration highlights the evolving landscape of modern open-source development, demonstrating how AI tools can empower makers to bring complex projects to fruition and achieve robust, production-ready implementations.
