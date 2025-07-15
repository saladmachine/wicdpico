# **WicdPico: Wireless Instrumentation Control Platform**

## **Overview**

WicdPico (wireless instrumentation and control device - Pico) transforms your Raspberry Pi Pico W into a versatile wireless control platform that adapts to your instrumentation needs. Whether you need a standalone handheld instrument or a networked sensor node, wicdpico provides the modular foundation to build professional-grade control systems.

## **Dual Deployment Modes**

WicdPico operates in two distinct modes using the same hardware and codebase:

### **WicdMeter Mode: Standalone Wireless Instrument**
Configure as a self-contained wireless meter:
- **Creates its own WiFi hotspot** - no existing network required
- **Serves web-based control panel** - access from any phone, tablet, or laptop
- **Perfect for field instruments** - handheld meters, portable monitors, remote controls
- **Zero infrastructure dependency** - works anywhere with power

*Example: A handheld environmental meter that creates "MeterWiFi" hotspot. Connect your phone, navigate to 192.168.4.1, and control/monitor the instrument through a responsive web interface.*

### **WicdNode Mode: Networked Sensor Node**  
Configure as a node in larger instrumentation networks:
- **Connects to existing WiFi** - joins your lab or facility network
- **MQTT communication** - publishes data to central hub systems
- **Scalable architecture** - deploy 5, 10, or 50+ nodes
- **Centralized monitoring** - all nodes report to unified dashboard

*Example: Precision agriculture research with 20 wicdnodes throughout a greenhouse, all reporting to a Raspberry Pi hub running Home Assistant for data logging and analysis.*

## **Why This Dual Approach Matters**

**Same hardware, same code - different configuration.** Most embedded platforms lock you into one deployment pattern. WicdPico adapts between wicdmeter and wicdnode modes based on your needs:

**Research Labs:** Start with standalone prototypes, scale to networked systems  
**Field Work:** No WiFi? No problem - each device is self-sufficient  
**Education:** Students build instruments that work anywhere  
**Commercial:** Single codebase supports both handheld products and IoT deployments

For example, in precision agriculture research, wicdpico democratizes instrumentation by delivering order-of-magnitude cost reductions compared to commercial CEA systems while maintaining research-quality data collection and control capabilities. This open-source platform enables sub-$50 sensor nodes versus $500+ commercial alternatives, making professional-grade environmental monitoring accessible to resource-constrained research institutions.

Built on proven modular architecture, wicdpico provides a class-based framework for building custom instrument control dashboards and sensor platforms that work equally well as standalone devices or networked systems.

Whether you're monitoring greenhouse conditions, controlling irrigation systems, or developing new CEA instrumentation, wicdpico's modular architecture allows you to rapidly prototype and deploy robust control systems that can be shared and reused across research projects.

## **Design Philosophy: "Lego Blocks for Embedded Interfaces"**

WicdPico is designed as a **modular dashboard system** where functional components can be "bolted in" to create custom embedded instruments. Rather than building monolithic applications, developers can:

- **Select pre-built functional modules** (LED control, file management, logging, sensors)
- **Configure each module** for specific needs
- **Assemble them** into a unified dashboard
- **Deploy as a complete** embedded instrument

This is **code-based assembly** requiring developer knowledge, but with standardized interfaces that make integration predictable and reliable.

## **Documentation**

* **Complete API Documentation:** https://wicdpico.readthedocs.io
* **Installation Guide:** Detailed setup instructions with troubleshooting
* **Module Development:** Professional Sphinx docstrings and integration examples
* **Research Applications:** Academic use cases and validation data

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
* **Wi-Fi Hotspot (Access Point):** Creates a "WicdNode" Wi-Fi network for direct device connection
* **Robust Configuration System:**
    * Crash resistant - falls back to working defaults
    * HTML entity decoding fixes corruption from web sources
    * Individual attribute validation with graceful fallback
    * Self-healing: can connect to default credentials to fix issues
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
* **Phase 2**: Picowicd rebuild using modular architecture (Complete)
* **Phase 3**: Instrument control tools for CEA applications (In Progress)

## **Getting Started**

### **Hardware Requirements**

* Raspberry Pi Pico 2 W
* Micro USB cable (for initial setup)
* External power source for field deployment
* I2C sensors/actuators as needed for your application

### **Software Requirements**

* **CircuitPython:** Version 9.0+ with `adafruit_httpserver` library
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

1. **Join WiFi Network:** Connect to "WicdNode" network (password: "simpletest" SSID and PW are configurble in settings.toml)
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

Modules feature academic-quality docstrings with comprehensive API documentation, usage examples, and integration patterns following professional Sphinx documentation standards.

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
WIFI_SSID = "WicdNode"
WIFI_PASSWORD = "simpletest"

# System timeout (minutes)
WIFI_AP_TIMEOUT_MINUTES = 10

# LED blink interval (seconds)
BLINK_INTERVAL = 0.25
```

### **Error Recovery**

WicdNode features robust error handling:
* **Missing config:** Uses safe defaults
* **Corrupted settings:** Individual fallback per setting
* **Network issues:** Automatic retry with default credentials
* **Module errors:** Graceful degradation reduces system failure

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

* **Memory:** 520KB of SRAM
* **Storage:** 4MB on-board flash storage
* **Network:** 802.11n WiFi (2.4GHz)
* **Power:** 3.3V operation, 5V tolerant inputs
* **I2C Support:** Multiple sensor/actuator connections
* **Web Interface:** Responsive design for mobile/desktop

## **Research Validation**

**Hardware Validated:**
* Multi-node sensor networks (5-10+ nodes tested)
* Pi5 WCS Hub integration with Home Assistant + Mosquitto MQTT
* Reliable wireless communication protocols

**Cost Analysis:**
* Sub-$50 sensor nodes vs $500+ commercial alternatives
* Complete system deployment under $300 vs $5000+ traditional systems
* Open-source design enables reproducible research across institutions

**Academic Applications:**
* Precision agriculture research platforms
* Controlled environment agriculture (CEA) monitoring
* Laboratory automation for plant science research
* Educational instrumentation for agricultural engineering programs

## **Success Metrics**

A successful wicdnode deployment should feel like:
- **Assembling electronic components** - predictable interfaces, known behavior
- **Professional embedded tools** - reliable, responsive, purpose-built
- **Modular synthesizers** - standardized connections enabling creative combinations

**For Academic Research:**
- **Reproducible Designs:** Complete documentation enables replication across labs
- **Publication Ready:** Professional documentation supports academic publication
- **Cost Effective:** Enables instrumentation access for resource-constrained institutions

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

---

**For Researchers:** This modular platform enables rapid development of custom instrumentation without starting from scratch. Share modules with colleagues to accelerate CEA research and reduce development costs across the community.

---

**AI Assistance Note:** This project, including aspects of its code (e.g., structure, debugging assistance, error handling enhancements) and the drafting of this `README.md`, was significantly assisted by large language models, specifically Gemini by Google and Claude by Anthropic. This collaboration highlights the evolving landscape of modern open-source development, demonstrating how AI tools can empower makers to bring complex projects to fruition and achieve robust, production-ready implementations.
