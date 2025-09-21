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

---

## License

MIT License

---

## See Also

- [README.md](./README.md)
- [CLAUDE.md](./CLAUDE.md)
- [context.md](./context.md)