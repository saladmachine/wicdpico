# Picowicd Architecture: Modular Dashboard System

## Vision Statement

Picowicd is designed as a **modular dashboard system** where functional components can be "bolted in" to create custom embedded instruments. Think of it as **Lego blocks for embedded web interfaces** - each module provides specific functionality that can be assembled into larger, purpose-built instruments.

## Core Philosophy: "Bolting In" Components

### The Assembly Metaphor
Rather than building monolithic applications, Picowicd enables developers to:
- Select pre-built functional modules (LED control, file management, logging, sensors)
- Configure each module for specific needs 
- Assemble them into a unified dashboard
- Deploy as a complete embedded instrument

**Not drag-and-drop** - this is code-based assembly requiring developer knowledge, but with standardized interfaces that make integration predictable.

## Architecture Layers

### Foundation Layer (`foundation_core.py`)
- **WiFi AP management** - Creates hotspot, handles network config
- **Web server framework** - Routes, templates, response handling  
- **Module registration system** - Central registry for all components
- **Shared services** - Logging, configuration, utilities

### Module Layer (Standardized Components)
Each module follows the `PicowidModule` base class pattern:
- **Self-contained functionality** - LED control, file management, sensor monitoring
- **Standard interfaces** - Routes, dashboard integration, configuration
- **Configurable parameters** - Exposed at top of file for easy customization
- **Optional logging integration** - Can feed central log and/or display local output

### Template/UI Layer (`foundation_templates.py`)
- **Responsive CSS framework** - Mobile-friendly, consistent styling
- **Page rendering system** - Unified layout with module content injection
- **Dashboard composition** - Automatic assembly of registered modules

## Logging Architecture: Dual-Level System

### The Coffee-Fueled Realization
During development, we discovered the need for **both local AND master logging**:

**Local Logs**: Function-specific output displayed adjacent to controls
- Temperature readings next to sensor controls
- LED status next to LED buttons  
- File operations next to file manager

**Master Log**: Central system log showing all activity
- Foundation-level events (WiFi status, errors)
- Cross-module system events
- Debug output for troubleshooting

### Implementation Pattern
```python
# Modules can choose their logging strategy:
self.foundation.log("System event")           # Goes to master log
self.local_log("Function-specific event")    # Shows in local context  
self.foundation.log_both("Critical event")   # Appears in both places
```

## Real-World Application Examples

### Multi-Function Environmental Monitor
**Scenario**: Temperature/humidity logging instrument with multiple functions

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

### IoT Device Manager
**Assembly**:
- **Device Control Module**: Turn outputs on/off
- **Network Module**: WiFi scanning, connection management
- **Monitoring Module**: Live system status, resource usage
- **Log Module**: Real-time event stream

## Configuration Philosophy

### Hardcoded vs Configurable
**Hardcoded** (in module files):
- Buffer sizes, polling intervals, UI layout parameters
- Placed at top of file under imports for easy access
- Developer-level configuration requiring code changes

**User Configurable** (via `config.py`):
- Units (F/C), date formats, network credentials  
- Runtime behavior that end-users might change
- Validated with graceful fallbacks

### Example Module Structure
```python
# LED Control Module
from foundation_core import PicowidFoundation

# === CONFIGURATION PARAMETERS ===
LED_BLINK_INTERVAL = 0.5        # seconds
MAX_BRIGHTNESS = 255            # 0-255
DEFAULT_PATTERN = "steady"      # steady, blink, pulse
LOG_LED_EVENTS = True          # show in local log
# === END CONFIGURATION ===

class LEDControlModule(PicowidModule):
    # Implementation follows...
```

## Future Evolution

### Planned Module Types
- **Sensor modules**: Temperature, humidity, pressure, motion
- **Communication modules**: MQTT, HTTP client, serial protocols  
- **Storage modules**: SD card, cloud sync, data export
- **Control modules**: PWM, servo, stepper motor control
- **Visualization modules**: Real-time graphs, gauges, charts

### Scalability Considerations
- **Memory constraints**: Modules must be lightweight for Pi Pico W
- **Performance**: Non-blocking operations, efficient polling
- **Reliability**: Graceful degradation, error isolation between modules

## Development Workflow

### Creating New Modules
1. Inherit from `PicowidModule` base class
2. Define configuration parameters at top of file
3. Implement required methods: `get_routes()`, `get_dashboard_html()`
4. Add to main application via `foundation.register_module()`
5. Test in isolation, then in multi-module configuration

### Integration Testing
- **Single module**: Verify basic functionality
- **Multi-module**: Test interaction, resource sharing
- **Full dashboard**: Complete instrument simulation

## Success Metrics

A successful Picowicd deployment should feel like:
- **Assembling electronic components** - predictable interfaces, known behavior
- **Professional embedded tools** - reliable, responsive, purpose-built
- **Modular synthesizers** - standardized connections enabling creative combinations

The architecture succeeds when developers can rapidly prototype embedded instruments by selecting and configuring modules rather than building from scratch.

---

*This architecture emerged from practical development experience and represents the philosophical foundation for all Picowicd development decisions.*