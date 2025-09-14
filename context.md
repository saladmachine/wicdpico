# WicdPico Collaborative Refactoring Workflow & AI Interaction Guidelines

!!!USE ONLY CIRCUITPYTHON AND NOT PYTHON!!!

# WicdPico Collaborative Refactoring Workflow & AI Interaction Guidelines

## Task Management & Chat Commands
- Use short, simple tasks.
- Use `@<filename>` to reference files.
- `/chat` ends the current chat, saves context, and starts a new chat.
- To refresh context, update `context.md`, then use `/clear` and tell the assistant to read `context.md`.

## Collaborative Refactoring Checklist

### Phase 1: Strategy & Prompt Engineering (Chat)
1. **Target Selection & Analysis**
   - Select a module to refactor and provide its code.
   - Identify all configurable values (I2C addresses, magic numbers, thresholds, etc.).
2. **settings.toml Structure Design**
   - Design a clear, consistent TOML table for each module.
   - Example:
     ```toml
     [module_bh1750]
     i2c_address = "0x23"
     measurement_mode = "high_res_2"
     ```
3. **Module & Foundation Modification Plan**
   - Modify the module’s `__init__` to accept a config dictionary.
   - Update main files (`code_*.py`) to load and pass config from `settings.toml`.
4. **Optimized CLI Prompt**
   - Once the plan is agreed, synthesize a single prompt for the Gemini CLI:
     - Modify the target module to accept config.
     - Update main file(s) to load and pass config.
     - Provide new settings.toml text.
   - Advise if `/clear` is needed before starting a new task.

### Phase 2: Execution & Validation (Terminal)
- Run the provided CLI command.
- Update `settings.toml` with the new config block.
- Test the application to confirm correct module initialization and behavior.

### Phase 3: Context Save (Persistent Memory)
- After successful refactoring and validation, update `context.md` with a concise summary.
- The assistant will prompt:  
  `"Now is a good time to update your context.md. Here is the summary to add:"`
- This creates a permanent record for future sessions.

## Codebase Interaction Principles

### Existing Code First
- **Always examine the codebase** (using Read, Grep, or Glob tools) before writing new code.
- **Never assume code structure**—verify patterns, class names, method signatures, and conventions.

### Real Features Only
- **Never create placeholder, mock, or demo code.**
- Only implement real, functional features.
- If interim non-functional steps are needed, ask for permission and explain why.

### Reuse Existing Code Mandate
- Before writing new code:
  1. Check if existing code already does the job.
  2. Look for existing patterns, functions, or modules.
  3. Use existing infrastructure and frameworks.
  4. Only write new code if existing code cannot be adapted or extended.
- If existing code does 80% of what's needed, extend or modify it.
- Prefer established patterns over new ones.
- When in doubt, ask: "Does something already exist that does this job?" If yes, use it.

---

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