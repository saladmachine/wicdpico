WicdPico System Architecture
This file should be read by collaborating AI before working on the repo.
Overview
WicdPico is a modular sensor and control platform for the Raspberry Pi Pico 2 W, built with CircuitPython. It provides a standalone WiFi hotspot and a web-based dashboard for real-time monitoring, control, and data logging.

CircuitPython Compatibility Statement
All server-side code for the dashboard is written in CircuitPython. It is required that any Python code or module used in this project be first verified as available and compatible with CircuitPython. Do not use features, modules, or libraries that are not supported by CircuitPython firmware.
f strings are incompatible with circuitpython. Never use f strings.

Core Components
foundation_core.py: Core system for WiFi/network, web server, module registration, and settings loading.

module_base.py: Abstract base class defining the interface for all modules (sensor and system modules).

module_*.py: Pluggable sensor, peripheral, and system modules.

system_*.py: System/application entrypoints that compose and orchestrate multiple modules.

code_*.py: Test harness and example entrypoints for single-module validation.

settings.toml: Configuration file for all system and module settings.

File & Naming Conventions
Modules
All hardware drivers, sensor logic, and system controls are implemented as module_<name>.py.

Each module inherits from WicdpicoModule and is registered with the foundation in a system or code file.

System Files
system_<name>.py:

Application/system entrypoints that compose and orchestrate multiple modules into a complete working device.

They are responsible for instantiating WicdpicoFoundation, registering modules, setting up web routes, and managing the application main loop.

For deployment, the desired system_<name>.py file (e.g., system_darkbox.py) is copied or renamed to code.py, which is the file executed by CircuitPython on boot. This design allows the platform to support multiple applications by simply swapping the system file.

Test Harnesses and Examples
code_*.py:

These files are used exclusively for single-module validation, development, or as simple usage examples. They are not intended for final deployment.

They follow the same basic structure as system files but are stripped down to focus on a single piece of hardware.

code.py
The file actually executed on boot by CircuitPython. In practice, this will be a copy of the desired system_*.py application file.

Module and System Composition Principle
Each module (module_*.py) must encapsulate a single hardware device or a single logical function. Modules should not combine multiple unrelated devices.

System files (system_*.py) are responsible for composing and orchestrating multiple modules to deliver the complete application logic and dashboard.

This ensures high modularity, reusability, and clarity. "Fat" modules that combine multiple sensors are discouraged and should be replaced with individual modules for each device.
System Initialization & Workflow
Select Application: Copy the desired system_*.py to code.py.

Startup: On boot, code.py instantiates WicdpicoFoundation, loads configuration, initializes WiFi, registers modules, starts the web server, and enters the main loop.

Main Loop: The main loop polls the HTTP server and calls .update() on each registered module for periodic tasks.

Shared Resource Management
To prevent hardware resource conflicts, all shared communication buses (I2C, SPI) MUST be instantiated a single time within the WicdpicoFoundation class. The application (system_*.py) will then pass the shared bus object to each module that requires it during its initialization.

Example in system_darkbox.py:

Python

1. Foundation creates the one and only one I2C bus
foundation = WicdpicoFoundation()
i2c_bus = foundation.get_i2c_bus() # Or it could be a public property

2. Pass the shared bus to each module's constructor
sht45_module = module_sht45.SHT45Module(i2c_bus)
scd41_module = module_scd41.SCD41Module(i2c_bus)

3. Register the modules
foundation.register_module(sht45_module)
foundation.register_module(scd41_module)
This pattern ensures that all modules coordinate access to the I2C bus through a single, shared instance.

Configuration & Dependency Management
Configuration
settings.toml is the canonical place for user and module config (network, sensor options, etc.). Each module may define its own config block/section in settings.toml.

Dependency Management
All third-party CircuitPython libraries (e.g., from the Adafruit bundle) must be placed in the /lib directory on the CIRCUITPY drive. This project uses circup for managing and updating these dependencies. A requirements.txt file should be maintained at the root of the project to simplify setup using circup install -r requirements.txt.

Embedded & CircuitPython Coding Principles
Separation of Concerns: Modules encapsulate device-level functionality; system files manage integration and orchestration.

Composability: Systems are composed from well-defined, reusable modules.

Testability: Modules can be tested in isolation using code_*.py test harnesses.

Resilience & Graceful Failure: Each hardware module is responsible for its own error handling (e.g., using try...except). If a device fails, the module should return a default value (e.g., None) and update its UI to show an error, ensuring that the failure of one sensor does not crash the entire system.

Clarity: The naming convention (module_*.py, system_*.py) communicates intent and structure.

Web Dashboard Architecture: Cards and Buttons
The dashboard UI is composed of modular "cards," each rendered as a <div class="module">...</div> block. Each card represents a module and is generated by a get_dashboard_html() method in that module's Python code.

Responsive Design
The dashboard uses a .dashboard-wrapper container and CSS media queries to ensure a responsive layout that works well on both desktop and mobile screens.

Buttons
All action buttons use the <button> element and are styled globally via CSS to be full width (100%) and stacked vertically for a clear, touch-friendly interface on all devices.

Best Practices
Use code_*.py files for module development and testing.

Use system_*.py for integrated, production-ready systems.

Keep modules in the root directory for reliable imports in CircuitPython.

Prefer simple, direct hardware interaction and avoid unnecessary abstraction for reliability.

License
MIT License
