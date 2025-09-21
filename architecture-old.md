# WicdPico System Architecture

## Overview

WicdPico is a modular sensor and control platform for the Raspberry Pi Pico 2 W, built with CircuitPython.  
It provides a standalone WiFi hotspot and a web-based dashboard for real-time monitoring, control, and data logging.

---

## Core Components

- **foundation_core.py**: Core system for WiFi/network, web server, module registration, and settings loading.
- **module_base.py**: Abstract base class defining the interface for all modules (sensor and system modules).
- **module_*.py**: Pluggable sensor, peripheral, and system modules (see below).
- **system_*.py**: System/application entrypoints—compose, orchestrate, and integrate multiple modules into a working application. (See below for details.)
- **code_*.py**: Legacy or test harness entrypoints. May still be used for single-module or experimental setups.
- **settings.toml**: Configuration file, preferred over legacy config.py.

---

## File & Naming Conventions

### Modules

- All hardware drivers, sensor logic, and system controls are implemented as `module_<name>.py`.
- Each module inherits from `WicdpicoModule` and is registered with the foundation in a system or code file.
- Common modules include:
  - `module_sht45.py`: SHT45 temperature/humidity sensor
  - `module_scd41.py`: SCD41 CO₂/temperature/humidity sensor
  - `module_bh1750.py`: BH1750 light sensor
  - `module_led_control.py`: Onboard LED control
  - `module_rtc_control.py`: PCF8523 RTC
  - `module_sd_card.py`: SD card storage
  - `module_battery_monitor.py`: Battery/VSYS monitoring
  - `module_monitor.py`: In-system monitor & console
  - (and others as needed for hardware or features)

### System Files

- **`system_<name>.py`**:  
  - Application/system entrypoints that compose and orchestrate multiple modules into a complete working device or research platform.
  - Responsible for:
    - Instantiating `WicdpicoFoundation`
    - Registering and configuring modules
    - Setting up all web routes, including the main dashboard
    - Managing the application main loop (polling server, calling `.update()` on modules, handling system-level events)
    - Loading configuration from `settings.toml`
  - Examples:
    - `system_darkbox.py`: Full DarkBox application integrating CO₂, light, RTC, SD, and other modules
    - `system_hydroponic.py`, etc.
  - The `system_*.py` convention formalizes the role of these files as multi-module, production-ready, application orchestrators.
  - For deployment, either copy `system_<name>.py` to `code.py` or configure the development workflow to launch the desired system file directly (if supported by the firmware).

### Application and Test Harnesses

- **`code_*.py`**:  
  - Legacy, experimental, or test entrypoints.
  - Typically used for single-module validation, development, or prototyping.
  - Follow the same structure as system files, but usually only instantiate and register one module.
  - Still supported for rapid development and hardware bring-up.

- **`code.py`**:  
  - The file actually executed on boot by CircuitPython.
  - In practice, this will be a copy of the desired `system_*.py` or `code_*.py` application.

### Example Structure

```
/CIRCUITPY/
├── foundation_core.py
├── foundation_templates.py
├── module_base.py
├── module_sht45.py
├── module_scd41.py
├── module_bh1750.py
├── module_led_control.py
├── module_rtc_control.py
├── module_sd_card.py
├── module_battery_monitor.py
├── module_monitor.py
├── system_darkbox.py
├── system_hydroponic.py
├── code_sht45.py
├── code_scd41.py
├── code_bh1750.py
├── code_darkbox.py
├── code_cpu_fan.py
├── code_monitor.py
├── settings.toml
└── code.py           # The active app (copy of one of system_*.py or code_*.py)
```

---

## System Initialization & Workflow

1. **Select Application/System**:  
   Copy the desired `system_*.py` or `code_*.py` to `code.py`.

2. **Startup**:  
   On boot, `code.py`:
   - Instantiates `WicdpicoFoundation`
   - Loads configuration from `settings.toml`
   - Initializes WiFi (AP or Client mode)
   - Registers modules and their HTTP/web routes
   - Starts the web server and enters the main loop

3. **Module Pattern**:  
   All modules:
   - Inherit from `WicdpicoModule`
   - Implement `register_routes(server)`, `get_dashboard_html()`, `update()`, and other lifecycle methods
   - Are registered with the foundation and exposed on the dashboard

4. **System File Pattern**:  
   - System files (`system_*.py`) define the device or application's top-level logic and integration.
   - They enable clear distinction between reusable modules and composed, production-grade systems.

5. **Dashboard**:  
   - The dashboard web route (usually `/`) is registered in the system or application file and renders all registered modules using the foundation's template and layout system.

6. **Main Loop**:  
   - The main loop polls the HTTP server and calls `.update()` on each module for periodic work.

---

## Configuration & Extensibility

- **settings.toml** is the canonical place for user and module config (network, sensor options, etc.)
- Each module may define its own config block/section in `settings.toml`.
- Legacy `config.py` is supported as fallback.
- New modules should be added as `module_<name>.py` and registered in a custom `system_*.py` or `code_*.py` application template.

---

## Hardware Patterns

- **I2C Bus**: GP4 (SDA), GP5 (SCL) for sensors (unless otherwise noted)
- **SD Card**: SPI interface, mounted at `/sd`
- **LED**: Onboard LED (GPIO25)
- **RTC**: PCF8523 via I2C
- **Power**: USB or battery (VSYS monitored by battery module)

---

## Best Practices

- Use `code_*.py` files for module development and testing.
- Use `system_*.py` for integrated, production-ready systems.
- Compose multi-module systems by copying and extending `system_*.py` templates.
- Keep modules in the root directory for reliable imports in CircuitPython.
- Register all module web routes and ensure each module supplies a dashboard HTML snippet or API.
- Prefer simple, direct hardware interaction and avoid unnecessary abstraction for reliability.

---

## Embedded & CircuitPython Coding Principles

- **Separation of Concerns**:  
  Modules encapsulate device-level or logical functionality; system files manage integration and orchestration.
- **Composability & Scalability**:  
  Systems are composed from well-defined, reusable modules.
- **Testability**:  
  Modules can be tested in isolation; systems can be tested at the integration level.
- **Clarity**:  
  The naming convention (`module_*.py`, `system_*.py`, `code_*.py`) communicates intent and structure.
- **Resource Awareness**:  
  Structure does not impact RAM/ROM or firmware constraints—it's a filename and workflow convention.
- **CircuitPython Alignment**:  
  `code.py` remains the executed entrypoint, with a workflow supporting templated, version-controlled applications.

## Web Dashboard Architecture: Cards and Buttons

The Darkbox dashboard UI is composed of modular "cards," each rendered as a `<div class="module">...</div>` block in HTML. Each card typically represents the output of a hardware or control module (such as the environmental sensors, CPU/fan status, or Wi-Fi management), and is generated by a `get_dashboard_html()` method in the relevant Python module. 

### Responsive Design

To achieve a modern, responsive layout:

- All cards use the `.module` CSS class, which ensures consistent padding, rounded corners, and drop shadow.
- The dashboard is wrapped in a `.dashboard-wrapper` container, which centers the content and sets a maximum width for readability on large screens, while also supporting edge-to-edge layout on mobile.
- CSS media queries ensure that padding and layout are adjusted for smaller screens.

### Buttons

- All action buttons in the dashboard use the `<button>` element and are styled globally via CSS to be **full width** (100% of their container) and stacked vertically.
- Vertical spacing between stacked buttons is enforced using `margin-bottom` on the `button` selector in CSS.
- This approach guarantees that, regardless of how the HTML is generated or what module produces the card, the buttons always present a clear and touch-friendly interface on all devices.

### Card Ordering and Grouping

- The HTML for each card is generated server-side (in CircuitPython), and cards are concatenated to form the dashboard.
- Special logic is used to extract and move the Wi-Fi Hotspot Timeout card to the top of the page, regardless of its position in the generated output.
- Related controls, such as CPU and Fan, can be combined into a single card for better grouping and user experience.

---

### Entry Point and Application Flexibility

The architecture uses a generic entry-point pattern, where each application or deployment provides its own `system_<application>.py` file (e.g., `system_darkbox.py`, `system_lightbox.py`, `system_hydroponics_chamber.py`). This file is copied or renamed to `code.py` on the CircuitPython device, as required by the runtime. The selected `system_*.py` file serves as the main application, importing and orchestrating the necessary modules and logic for that particular deployment, while reusing the library of hardware and feature modules provided by the codebase. This design allows the platform to support multiple applications and hardware configurations, simply by swapping or modifying the system file.
## CircuitPython Compatibility Statement

All server-side code for the dashboard is written in CircuitPython. **It is required that any Python code or module used in this project be first verified as available and compatible with CircuitPython.** Do not use features, modules, or libraries that are not supported by CircuitPython firmware.
---

### Module and System Composition Principle

- **Each module (`module_*.py`) must encapsulate a single hardware device or a single logical function.**
- **Modules should not combine multiple unrelated devices or sensors.**
- If a feature or application requires multiple devices (e.g., sensors and actuators), these should each be implemented as individual modules.
- **System files (`system_*.py`) are responsible for composing and orchestrating multiple modules to deliver the complete application logic and dashboard.**

*This ensures high modularity, reusability, and clarity. "Fat" modules that combine multiple sensors/devices (such as the deprecated `module_darkbox`) are discouraged and should be replaced with individual modules for each device.*

## License

MIT License

---

## See Also

- [README.md](./README.md)
- [CLAUDE.md](./CLAUDE.md)
- [context.md](./context.md)
