# **Picowicd: Modular Instrument Control Platform**

## **Overview**

Picowicd transforms your Raspberry Pi Pico W into a modular, web-based instrument control platform for controlled environment agriculture (CEA) and research applications. Built on the proven foundation of the picowide wireless IDE, picowicd provides a class-based modular framework for building custom instrument control dashboards and I2C sensor platforms.

Whether you're monitoring greenhouse conditions, controlling irrigation systems, or developing new CEA instrumentation, picowicd's modular architecture allows you to rapidly prototype and deploy robust control systems that can be shared and reused across research projects.

## **Architecture**

**Modular Design**: Built on a robust foundation system that allows easy addition of sensor modules, control interfaces, and monitoring tools. Each module is self-contained and reusable across different CEA instrumentation projects.

* **Foundation**: Robust core system providing WiFi, web server, and module management
* **Modules**: Standardized components for specific functionality (sensors, actuators, monitoring)
* **Widgets**: Dashboard UI components (buttons, sliders, gauges) that integrate seamlessly

## **Features**

### **Core Foundation**
* **Self-Hosted Web Server:** Runs directly on the Pico W, serving modular dashboards
* **Wi-Fi Hotspot (Access Point):** Creates a "Picowide" Wi-Fi network for direct device connection
* **Robust Configuration System:**
    * Never crashes - always falls back to working defaults
    * HTML entity decoding fixes corruption from web sources
    * Individual attribute validation with graceful fallback
    * Self-healing: can always connect to default credentials to fix issues
* **Plugin Architecture:** Easy registration and management of functional modules
* **Template System:** Centralized UI rendering for consistent dashboard appearance

### **Standard Modules**
* **LED Control Module:** Toggle and blinky modes for system status indication
* **File Manager Module:** Edit configuration files and code directly on the device
* **Console Monitor Module:** Real-time system output monitoring
* **Template Framework:** For rapid development of new sensor/control modules

### **Power Management**
* **Intelligent Timeout:** Automatic 10-minute hotspot shutdown to preserve battery
* **Standalone Battery Operation:** Fully functional when powered externally
* **Real-time Status:** Dashboard shows system health and module status

## **Development Phases**

* **Phase 1**: Foundation verification (Complete)
* **Phase 2**: Picowide rebuild using modular architecture (In Progress)
* **Phase 3**: Instrument control tools for CEA applications (Planned)

## **Getting Started**

### **Hardware Requirements**

* Raspberry Pi Pico W
* Micro USB cable (for initial setup)
* External power source for field deployment
* I2C sensors/actuators as needed for your application

### **Software Requirements**

* **CircuitPython:** Version 8.x or 9.x with `adafruit_httpserver` library
* **Standard Libraries:** `digitalio`, `board`, `time`, `wifi`, `socketpool`

### **Installation**

1. **Flash CircuitPython** onto your Raspberry Pi Pico W
2. **Install Required Libraries** in the `lib` folder:
   * `adafruit_httpserver`
   * Any sensor-specific libraries for your modules
3. **Copy Picowicd Files** to the CIRCUITPY drive:
   * `code.py` (main application)
   * `foundation_core.py` (core system)
   * `module_base.py` (base class for modules)
   * Module files (`led_control.py`, `file_manager.py`, etc.)
   * `foundation_templates.py` (UI templates)
   * `config.py` (configuration)
4. **Configure Settings** in `config.py` for your WiFi and application needs
5. **Power Cycle** to start the system

## **Usage**

### **Connecting to the System**

1. **Join WiFi Network:** Connect to "Picowide" network (password: "simpletest")
2. **Open Dashboard:** Navigate to `http://192.168.4.1` in any web browser
3. **Access Modules:** Use the modular dashboard to control your instruments

### **Adding New Modules**

```python
from module_base import PicowidModule

class MySensorModule(PicowidModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        # Initialize your sensor hardware
        
    def register_routes(self, server):
        # Add web endpoints for your sensor
        pass
        
    def get_dashboard_html(self):
        # Return HTML for dashboard integration
        return "<div>My Sensor Controls</div>"
        
    def update(self):
        # Called from main loop for real-time updates
        pass
```

Register your module in `code.py`:
```python
my_sensor = MySensorModule(foundation)
foundation.register_module("my_sensor", my_sensor)
```

## **Module Development**

### **Standard Module Interface**

All modules extend `PicowidModule` and implement:
* `register_routes(server)` - Add web endpoints
* `get_dashboard_html()` - Return dashboard UI
* `update()` - Real-time processing in main loop
* `cleanup()` - Shutdown procedures (optional)

### **Foundation Services**

Modules have access to foundation services:
* `self.foundation.startup_print()` - Logging
* `self.foundation.config` - Configuration access
* `self.foundation.server` - Web server for custom routes
* `self.foundation.templates` - UI template system

## **Configuration**

### **config.py Settings**

```python
# Wi-Fi hotspot configuration
WIFI_SSID = "Picowide"
WIFI_PASSWORD = "simpletest"

# System timeout (minutes)
WIFI_AP_TIMEOUT_MINUTES = 10

# LED blink interval (seconds)
BLINK_INTERVAL = 0.25
```

### **Error Recovery**

Picowicd features robust error handling:
* **Missing config:** Uses safe defaults
* **Corrupted settings:** Individual fallback per setting
* **Network issues:** Automatic retry with default credentials
* **Module errors:** Graceful degradation without system failure

## **Applications**

### **CEA Research**
* Environmental monitoring (temperature, humidity, CO2)
* Irrigation control systems
* Lighting control and scheduling
* Data logging and analysis

### **General Instrumentation**
* Sensor data collection
* Actuator control interfaces
* Real-time monitoring dashboards
* Remote configuration tools

## **Technical Specifications**

* **Memory Requirements:** 264KB RAM minimum
* **Storage:** 2MB flash storage
* **Network:** 802.11n WiFi (2.4GHz)
* **Power:** 3.3V operation, 5V tolerant inputs
* **I2C Support:** Multiple sensor/actuator connections
* **Web Interface:** Responsive design for mobile/desktop

## **Contributing**

Contributions welcome! The modular architecture makes it easy to:
* Add new sensor modules
* Enhance the foundation system
* Improve dashboard templates
* Expand instrumentation capabilities

## **License**

MIT License - see LICENSE file for details.

## **Acknowledgments**

* Built on CircuitPython and Adafruit libraries
* Foundation derived from picowide wireless IDE
* Designed for CEA research and low-cost instrumentation
* Developed with AI assistance for rapid prototyping and robust implementation

---

**For Researchers:** This modular platform enables rapid development of custom instrumentation without starting from scratch. Share modules with colleagues to accelerate CEA research and reduce development costs across the community.