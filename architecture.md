# WicdPico System Architecture

## Overview

WicdPico is a modular sensor and control platform for the Raspberry Pi Pico 2 W, built with CircuitPython.  
It provides a standalone WiFi hotspot and a web-based dashboard for real-time monitoring, control, and data logging.

---

## Core Components

### 1. Foundation Layer

- **File:** `foundation_core.py`
- **Class:** `WicdpicoFoundation`
- **Responsibilities:**
  - Manages network setup (AP/client modes)
  - Initializes and starts the HTTP server
  - Registers modules and integrates their web routes
  - Renders the main dashboard by collecting HTML fragments from modules
  - Handles configuration loading (from `settings.toml` or `config.py`)
  - Provides system status and error recovery

### 2. Module Layer

- **Files:** `module_*.py`
- **Base Class:** `WicdpicoModule` (from `module_base.py`)
- **Responsibilities:**
  - Encapsulate sensor/control logic (e.g., SCD41, BH1750, SD card, battery monitor)
  - Provide REST endpoints for sensor readings, control actions, and data logging
  - Supply dashboard widgets via `get_dashboard_html()` for integration into the main dashboard
  - Register their routes with the foundation's HTTP server

### 3. Application Layer

- **Files:** `code.py`, `code_darkbox.py`, etc.
- **Responsibilities:**
  - Entry point for the application
  - Instantiates the foundation and modules
  - Registers modules with the foundation
  - Starts the network and server
  - Serves the main dashboard route (`/`)
  - Runs the main polling loop

### 4. Configuration Layer

- **Files:** `settings.toml`, `config.py`
- **Responsibilities:**
  - Store user and system configuration (WiFi, module settings, etc.)
  - Provide configuration data to the foundation and modules

### 5. Templates & Utilities

- **File:** `foundation_templates.py`
- **Responsibilities:**
  - Renders HTML pages and dashboard layouts
  - Provides reusable UI components

---

## Architectural Principles

- **Modularity:** Each sensor/control module is self-contained and interacts with the foundation via a well-defined interface.
- **Separation of Concerns:** The foundation manages system-level tasks; modules handle device-specific logic; the main file orchestrates the application.
- **Web Integration:** All user interaction is via a web dashboard, assembled from module widgets.
- **Configuration Priority:** `settings.toml` is preferred, with fallback to `config.py` and robust defaults.
- **Extensibility:** New modules can be added easily by following the established base class and registration pattern.

---

## Architectural Violations (from open files)

1. **Dashboard Route in Module**
   - In `module_darkbox.py`, the dashboard route (`serve_dashboard`) is still present and **nested inside another route**.  
     **Violation:** The dashboard route should only be defined in the main application file (e.g., `code.py` or `code_darkbox.py`), not in any module.  
     **Fix:** Remove the dashboard route from `module_darkbox.py`.

2. **Route Nesting**
   - In `module_darkbox.py`, the dashboard route is nested inside the `read_light_log` route.  
     **Violation:** Routes should not be nested; each route should be defined at the top level within the `register_routes` method.

3. **Module HTML Integration**
   - All modules should provide dashboard widgets via `get_dashboard_html()`, not serve full dashboard pages.

---

## Summary

The WicdPico architecture is robust, modular, and extensible, supporting a wide range of sensor and control modules.  
To maintain architectural integrity, ensure that:
- The dashboard route is only served from the main application file.
- Modules only provide REST endpoints and dashboard widgets.
- Route definitions are not nested within each other.

**Adhering to these principles will keep the system maintainable and scalable.**