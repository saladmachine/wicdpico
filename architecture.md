# DarkBox System Architecture

## Overview

The DarkBox system is a modular, open-source instrumentation and control platform for research in acetate-based plant growth under strictly controlled environmental conditions. It is built on the WicdPico foundation, with all core logic written in CircuitPython and designed for reproducibility, reliability, and adaptability.

---

### Repository Structure
```
darkbox/
├── wicdpico/                    # Git submodule to WicdPico platform
├── darkbox_modules/             # DarkBox-specific modules
│   ├── module_hydroponic.py     # Solution management (Phase 2)
│   ├── module_darkness.py       # Light monitoring and safety
│   └── module_chamber.py        # Environmental control
├── phase1/                      # Petri dish system configuration
│   └── code_phase1.py           # Phase 1 main application
├── phase2/                      # Hydroponic system configuration  
│   └── code_phase2.py           # Phase 2 main application
├── lib/                         # Symlinks to WicdPico modules
├── docs/                        # Research documentation
└── scripts/                     # Development and deployment tools
```

## Safety & Validation

### Pre-Research Testing
- **System integrity**: Complete darkness verification using light sensors
- **Environmental stability**: Temperature, humidity, CO2 control validation  
- **Solution management**: Pumping, level sensing, bubbler operation (Phase 2)
- **Data logging**: Continuous monitoring and backup systems
- **Remote monitoring**: VCP accessibility for experiment oversight

### Research Protection
- **No light contamination**: Multiple redundant darkness monitoring
- **Stable environment**: Automated control with manual override capability
- **Data backup**: Multiple logging systems to prevent data loss
- **Remote access**: Monitor experiments without physical chamber access

## Development Workflow

### VSCode Integration
- **Code templates**: `phase1/code_phase1.py` → `code.py` deployment
- **Automated sync**: Save triggers copy to both local git and CIRCUITPY drive
- **Serial monitoring**: Real-time system feedback during development
- **Module management**: Automatic copying of dependencies to Pico

### Dependency Management
- **WicdPico sync**: Controlled updates via Git submodule versioning
- **One-way dependency**: DarkBox uses WicdPico, no reverse dependencies
- **Version control**: Lock to specific WicdPico commits for stability

## Academic Context

### Publication Target
- **Journal**: HardwareX - open source scientific hardware
- **Timeline**: Support publication within 6 months
- **Focus**: Reproducible low-cost research instrumentation
- **Audience**: Academic researchers requiring specialized controlled environments

### Research Value
- **Novel growth method**: Darkbox system supports study of acetate metabolism instead of photosynthesis
- **Cost-effective platform**: Academic-grade instrumentation at maker prices
- **Reproducible design**: Open source hardware enabling research replication
- **Modular architecture**: Adaptable to other controlled environment applications

## License

MIT License

---

## Dependencies

This project depends on the WicdPico platform:
- **Repository**: https://github.com/saladmachine/wicdpico
- **Integration**: Git submodule for controlled dependency management
- **Documentation**: See WicdPico README for core platform capabilities

Built with CircuitPython and the Adafruit ecosystem for academic research applications.

AI Assistance Note: This project, including aspects of its code (e.g., structure, debugging assistance, error handling enhancements) and the drafting of this README.md, was significantly assisted by large language models, specifically Gemini by Google and Claude by Anthropic. This collaboration highlights the evolving landscape of modern open-source development, demonstrating how AI tools can empower makers to bring complex projects to fruition and achieve robust, production-ready implementations.

---

# Persistent Application State and Configuration

## Motivation

To ensure device and experimental continuity after power loss or system reboot, all DarkBox and compatible WicdPico applications must persist configuration and runtime state to non-volatile storage. This enables restoration of the last known state and consistent application behavior across sessions.

## Standard Mechanism: SD Card JSON Config

**All modules and applications must:**
- Store persistent configuration and state in a dedicated JSON file on the SD card.
- Use application-specific filenames, e.g. `darkbox.json`, `cpu_fan.json`, stored in `/sd/settings/` or another clearly documented location.
- Load the JSON file at startup to reestablish the previous state.
- Save to the JSON file whenever persistent values change, using atomic file writes for reliability.

### File Layout Example

```
/sd/settings/
    darkbox.json
    cpu_fan.json
    hydroponic.json
```

### Example JSON Content

```json
{
  "ap_timeout_minutes": 10,
  "fan_speed": 80,
  "fan_enabled": true
}
```

### Implementation Guidelines

- **Atomic Write:** Always write to a temporary file (e.g. `cpu_fan.json.tmp`) then rename to the final file to prevent corruption.
- **Error Handling:** Gracefully handle missing, unreadable, or corrupted files; fall back to defaults and log any issues.
- **Human-Readable:** Keep files simple and editable by researchers.
- **Minimal Writes:** Only save when state changes to minimize SD card wear.
- **Consistent Pattern:** All modules use the same load/save pattern for maintainability.

### Startup and Runtime Workflow

1. **At Startup:**
   - Attempt to load the JSON config from SD card.
   - If missing/corrupt, initialize state from defaults and (optionally) create the config file.

2. **During Operation:**
   - When a persistent property changes (e.g., a user updates a setting via the web interface), write the new state to the JSON config using atomic write.

3. **At Shutdown:** 
   - No special action required; state is always current after each change.

### Example Usage Pattern

```python
import json
import os

CONFIG_PATH = "/sd/settings/cpu_fan.json"

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        # Log error, return defaults
        return {"fan_speed": 80, "fan_enabled": True}

def save_config(config):
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(config, f)
    os.rename(tmp_path, CONFIG_PATH)
```

## Migration Plan

- **New code:** All new modules/applications must follow this pattern.
- **Retrofit:** Older code using Pico flash or hardcoded config will be updated to use SD card JSON config as time allows.

## Rationale

- **Reliability:** SD card file system is robust and power-failure tolerant.
- **Transparency:** Researchers can inspect and edit config files externally if needed.
- **Consistency:** Standardized mechanism improves maintainability and onboarding.

## See Also

- [WicdPico Documentation](https://github.com/saladmachine/wicdpico)
- [Module Implementation Examples](/darkbox_modules/)
- [Phase 1/2 Main Application Code](/phase1/code_phase1.py, /phase2/code_phase2.py)
