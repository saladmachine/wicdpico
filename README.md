# **Picowicd: Modular Instrument Control Platform**

## **Overview**

Picowicd (Pico wireless instrumentation and control dashboard) transforms your Raspberry Pi Pico W into a modular, web-based instrument control platform for controlled environment agriculture (CEA) and research applications. Built on the proven foundation of the picowicd wireless IDE, picowicd provides a class-based modular framework for building custom instrument control dashboards and I2C sensor platforms.

Whether you're monitoring greenhouse conditions, controlling irrigation systems, or developing new CEA instrumentation, picowicd's modular architecture allows you to rapidly prototype and deploy robust control systems that can be shared and reused across research projects.

## **Design Philosophy: "Lego Blocks for Embedded Interfaces"**

Picowicd is designed as a **modular dashboard system** where functional components can be "bolted in" to create custom embedded instruments. Rather than building monolithic applications, developers can:

- **Select pre-built functional modules** (LED control, file management, logging, sensors)
- **Configure each module** for specific needs
- **Assemble them** into a unified dashboard
- **Deploy as a complete** embedded instrument

This is **code-based assembly** requiring developer knowledge, but with standardized interfaces that make integration predictable and reliable.

## **Architecture**

### **Three-Layer Design**

**Foundation Layer (`foundation_core.py`)**
- **WiFi AP management** - Creates hotspot, handles network config
- **Web server framework** - Routes, templates, response handling  
- **Module registration system** - Central registry for all components
- **Shared services** - Logging, configuration, utilities

**Module Layer (Standardized Components)**
Each module follows the `PicowidModule` base class pattern:
- **Self-contained functionality** - LED control, file management, sensor monitoring
- **Standard interfaces** - Routes, dashboard integration, configuration
- **Configurable parameters** - Exposed at top of file for easy customization
- **Optional logging integration** - Can feed central log and/or display local output

**Template/UI Layer (`foundation_templates.py`)**
- **Responsive CSS framework** - Mobile-friendly, consistent styling
- **Page rendering system** - Unified layout with module content injection
- **Dashboard composition** - Automatic assembly of registered modules

### **Dual-Level Logging System**

**Local Logs**: Function-specific output displayed adjacent to controls
- Temperature readings next to sensor controls
- LED status next to LED buttons  
- File operations next to file manager

**Master Log**: Central system log showing all activity
- Foundation-level events (WiFi status, errors)
- Cross-module system events
- Debug output for troubleshooting

### **Configuration Philosophy**

**Hardcoded** (in module files):
- Buffer sizes, polling intervals, UI layout parameters
- Placed at top of file under imports for easy access
- Developer-level configuration requiring code changes

**User Configurable** (via `settings.toml`):
- Units (F/C), date formats, network credentials  
- Runtime behavior that end-users might change
- Validated with graceful fallbacks

## **Features**

### **Core Foundation**
* **Self-Hosted Web Server:** Runs directly on the Pico W, serving modular dashboards
* **Wi-Fi Hotspot (Access Point):** Creates a "Picowicd" Wi-Fi network for direct device connection
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
* **Phase 2**: Picowicd rebuild using modular architecture (In Progress)
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
   * `settings.toml` (configuration)
4. **Configure Settings** in `settings.toml` for your WiFi and application needs
5. **Power Cycle** to start the system

## **Usage**

### **Connecting to the System**

1. **Join WiFi Network:** Connect to "Picowicd" network (password: "simpletest")
2. **Open Dashboard:** Navigate to `http://192.168.4.1` in any web browser
3. **Access Modules:** Use the modular dashboard to control your instruments

### **Adding New Modules**

```python
from module_base import PicowidModule

class MySensorModule(PicowidModule):
    # === CONFIGURATION PARAMETERS ===
    SENSOR_POLL_INTERVAL = 1.0      # seconds
    TEMPERATURE_UNITS = "C"         # C or F
    LOG_SENSOR_EVENTS = True        # show in local log
    # === END CONFIGURATION ===
    
    def __init__(self, foundation):
        super().__init__(foundation)
        # Initialize your sensor hardware
        
    def register_routes(self, server):
        @server.route("/sensor_data", methods=['GET'])
        def get_sensor_data(request):
            # Handle sensor data requests
            pass
        
    def get_dashboard_html(self):
        # Return HTML for dashboard integration
        return '''
        <div class="module">
            <h3>My Sensor</h3>
            <p>Temperature: <span id="temp">--</span>°C</p>
            <button onclick="refreshSensor()">Refresh</button>
        </div>
        '''
        
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

### **Creating New Modules**

1. Inherit from `PicowidModule` base class
2. Define configuration parameters at top of file
3. Implement required methods: `register_routes()`, `get_dashboard_html()`
4. Add to main application via `foundation.register_module()`
5. Test in isolation, then in multi-module configuration

## **Configuration**

### **settings.toml Settings**

```toml
# Wi-Fi hotspot configuration
WIFI_SSID = "Picowicd"
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

## **Real-World Application Examples**

### **Multi-Function Environmental Monitor**
**Assembly**:
- **Sensor Module**: Displays current readings, controls sampling rate
- **Log Module**: Shows timestamped sensor data, scrollable history  
- **Storage Module**: Manages data files, export functionality
- **Config Module**: Set F/C units, date formats, thresholds

**User Experience**: 
- Set 1-minute logging interval
- Walk away for an hour  
- Return to scroll through timestamped log entries
- Future: Add graphing module for visualization

### **IoT Device Manager**
**Assembly**:
- **Device Control Module**: Turn outputs on/off
- **Network Module**: WiFi scanning, connection management
- **Monitoring Module**: Live system status, resource usage
- **Log Module**: Real-time event stream

## **Planned Module Types**
- **Sensor modules**: Temperature, humidity, pressure, motion
- **Communication modules**: MQTT, HTTP client, serial protocols  
- **Storage modules**: SD card, cloud sync, data export
- **Control modules**: PWM, servo, stepper motor control
- **Visualization modules**: Real-time graphs, gauges, charts

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

## **Success Metrics**

A successful Picowicd deployment should feel like:
- **Assembling electronic components** - predictable interfaces, known behavior
- **Professional embedded tools** - reliable, responsive, purpose-built
- **Modular synthesizers** - standardized connections enabling creative combinations

The architecture succeeds when developers can rapidly prototype embedded instruments by selecting and configuring modules rather than building from scratch.

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
* Foundation derived from picowicd wireless IDE
* Designed for CEA research and low-cost instrumentation
* Developed with AI assistance for rapid prototyping and robust implementation

---

**For Researchers:** This modular platform enables rapid development of custom instrumentation without starting from scratch. Share modules with colleagues to accelerate CEA research and reduce development costs across the community.

---

**AI Assistance Note:** This project, including aspects of its code (e.g., structure, debugging assistance, error handling enhancements) and the drafting of this `README.md`, was significantly assisted by large language models, specifically Gemini by Google and Claude by Anthropic. This collaboration highlights the evolving landscape of modern open-source development, demonstrating how AI tools can empower makers to bring complex projects to fruition and achieve robust, production-ready implementations.
