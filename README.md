# WicdPico: Modular CircuitPython Sensor Platform

**Transform your Raspberry Pi Pico 2 W into a versatile wireless sensor meter with web-based control.**

## Overview

WicdPico is a modular platform for building I2C sensor instruments that serve interactive web dashboards. Suitable for environmental monitoring, data logging, and laboratory instrumentation - all as simple as swapping or stacking modules.

## Key Features

✅ **Standalone Operation** - Creates its own WiFi hotspot (no network required)  
✅ **Web-Based Dashboard** - Control via phone, tablet, or laptop browser  
✅ **Modular Architecture** - Mix and match sensor/control modules  
✅ **Built-in Web IDE** - Edit code directly through web interface  
✅ **Data Logging** - Timestamped data to SD card  
✅ **RTC Time Sync** - Browser-based time synchronization for accurate timestamps  
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
- **`module_scd41.py`** - CO2, temperature, humidity sensor (SCD41)
- **`module_bh1750.py`** - Digital light sensor (BH1750)
- **`module_led_control.py`** - Onboard LED control and status
- **`module_rtc_control.py`** - Real-time clock (PCF8523) with browser time sync
- **`module_sd_card.py`** - SD card data logging
- **`module_sd_card_test.py`** - SD card testing utilities
- **`module_battery_monitor.py`** - Internal VSYS voltage monitoring with load testing
- **`module_water_level.py`** - Water level detection (FS-IR02B sensor)
- **`module_file_manager.py`** - Web-based file editor
- **`module_console_monitor.py`** - Web-based REPL console

### Development Workflow

**1. Individual Module Testing**
```bash
# Test temperature/humidity sensor
cp code_sht45.py code.py

# Test CO2 sensor
cp code_scd41.py code.py

# Test light sensor
cp code_bh1750.py code.py

# Test water level sensor
cp code_water_level.py code.py

# Test battery monitoring
cp code_battery_monitor.py code.py

# Test RTC time synchronization
cp code_rtc_time_sync_test.py code.py

# Test SD card with PicoBell Adalogger
cp code_sd_card_test.py code.py
```

**2. Multi-Module Combinations** 
```bash
# Create custom code.py with desired modules
# See existing code_*.py files for examples
# Modify module selections in code.py as needed
```

**3. Custom Module Development**
- Create `module_mynewsensor.py` inheriting from `WicdpicoModule`
- Implement sensor reading, web interface, and dashboard widget
- Register in your `code.py` configuration

## Creating a Custom Application and Module

You can create your own specialized sensor application by combining existing modules or developing your own. Here’s a step-by-step guide for a semi-skilled programmer to get started **without needing any external code or templates**:

---

### 1. Create a Custom Module

All modules inherit from `WicdpicoModule` (defined in `module_base.py`).  
A custom module typically implements:

- `register_routes(self, server)`: Registers any web API endpoints for your sensor/control logic.
- `get_dashboard_html(self)`: Returns the HTML (and optionally CSS/JS) for the dashboard widget.
- `update(self)`: Performs periodic tasks such as sensor readings.

**Minimal Example (`module_example.py`):**
```python
from module_base import WicdpicoModule

class ExampleModule(WicdpicoModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Example"
        self.path = "/example"
        self.counter = 0

    def register_routes(self, server):
        @server.route("/increment", methods=["POST"])
        def increment_handler(request):
            self.counter += 1
            return "Counter incremented!"

    def get_dashboard_html(self):
        return f"""
        <div class="module">
            <h3>Example Module</h3>
            <p>Counter: <span id='counter'>{self.counter}</span></p>
            <button onclick="fetch('/increment', {{method: 'POST'}}).then(_=>location.reload())">
                Increment
            </button>
        </div>
        """

    def update(self):
        # Called periodically by the system
        pass
```

---

### 2. Register Your Module in Your Application Entrypoint

The main entrypoint is typically `code.py` or a custom `code_*.py` file.  
You import your module, instantiate it, register it with the foundation, and then start the system.

**Minimal Example (`code.py`):**
```python
from foundation_core import WicdpicoFoundation
from module_example import ExampleModule

foundation = WicdpicoFoundation()
foundation.register_module("example", ExampleModule(foundation))

if foundation.initialize_network():
    foundation.start_server()
    foundation.run_main_loop()
```

---

### 3. Add Your Files

- Place your custom module file (`module_example.py`) in the root of the CIRCUITPY drive.
- Make sure your `code.py` imports it and registers it with the foundation as shown above.

---

### 4. View and Interact

- Boot your device, connect to its WiFi, and open the web dashboard in your browser.
- Your new module’s widget should appear and be interactive!

---

### 5. Tips

- See `module_base.py` for required and optional methods.
- Use the built-in web IDE (if enabled) to edit and experiment without ejecting the drive.
- Use the `startup_print()` method for debugging output that appears on both the serial console and web dashboard.
- You can add additional REST API endpoints to your module by defining them in `register_routes`.

---

**With these instructions, you do NOT need to reference any external code or templates. Everything you need to create a custom application and module is demonstrated above.**

## Example Applications

**🌡️ Environmental Monitor** - SHT45 + RTC + SD logging  
**🔧 Web-Based IDE** - Code editor + file manager + console  
**🔋 Battery Meter** - Internal VSYS voltage monitoring + load testing  
**💧 Water Level Monitor** - FS-IR02B sensor with refill event logging  
**⏰ RTC Time Sync** - Browser-based time synchronization for field use  
**💾 SD Card Test** - PicoBell Adalogger SPI mounting with file download validation  
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
├── code_*.py                   # Example configurations
└── claude_context.txt          # Development context and guidelines
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

MIT License

---

## Acknowledgments
Built with CircuitPython and adafruit_httpserver.

AI Assistance Note: This project, including aspects of its code (e.g., structure, debugging assistance, error handling enhancements) and the drafting of this README.md, was significantly assisted by AI tools (Anthropic Claude, GitHub Copilot, ChatGPT). All code and text should be reviewed for accuracy and safety before use in production.