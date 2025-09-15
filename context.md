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

*No current architectural violations. All dashboard routes are now correctly defined only in the main application file (e.g., `code.py`). All module routes are properly registered and not nested. Modules provide dashboard widgets via `get_dashboard_html()` as required.*

---

## Context Notes for WicdPico Project

### SD Card File Handling

- All CSV log files are stored **only on the SD card** (`/sd`), not on the root (`/`) directory.
- The root directory is read-only when CIRCUITPY is mounted over USB; this is why all logging and file management is done on the SD card.
- When listing files for download in the web dashboard, **only filenames from `/sd` are shown** (e.g., `darkbox_data.csv`), with no `sd/` prefix.
- When downloading, the backend always prepends `/sd/` to the filename received from the browser.
- **Because only the filename is sent to the browser and the backend always prepends `/sd/`, there is no need for a custom URL decoding fix for slashes (`%2F`).**
- This approach eliminates the need to handle URL-encoded slashes and avoids confusion about file location.

### Web Dashboard

- The "Files" card in the dashboard now only lists and downloads CSV files from the SD card.
- No console/log management buttons are present; the UI is streamlined for file management.
- All file operations (listing, downloading) are restricted to the SD card.

### Architecture Guidance

- Do not list or attempt to access files from the root directory.
- Do not use the `sd/` prefix in filenames sent to the browser.
- Always access files as `/sd/filename.csv` in backend code.
- **No custom URL decode function for slashes is needed.**

---

# filepath: /home/joepardue/wicdpico/architecture.md

### File Management

- **All log files are stored on the SD card** (`/sd`). The root directory is read-only and not used for logging.
- The backend lists only CSV files from `/sd` and sends just the filename (e.g., `darkbox_data.csv`) to the browser.
- When a file is requested for download, the backend constructs the path as `/sd/filename.csv`.
- **This design avoids issues with URL-encoded slashes and eliminates the need for any custom URL decoding fix for slashes.**
- File handling is now simple and robust.

### Best Practices

- Do not use the `sd/` prefix in filenames sent to the browser.
- Always prepend `/sd/` in backend code when accessing files.
- Avoid listing or accessing files from the root directory.
- **No custom URL decode function for slashes is needed.**

---