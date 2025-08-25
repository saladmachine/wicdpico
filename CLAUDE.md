# WicdPico Project Context

## Project Overview
WicdPico is a modular CircuitPython sensor platform for Raspberry Pi Pico 2 W that creates a standalone WiFi hotspot with web-based dashboards for sensor monitoring and control.

## Current Status
- **Platform**: Raspberry Pi Pico 2 W with CircuitPython
- **Architecture**: Modular system with web interface
- **Network**: WiFi hotspot mode (PicoTest-Node00)
- **Interface**: Web dashboard at http://192.168.4.1

## Recent Development (from git history)
- **Latest**: Added comprehensive sensor modules - SCD41 CO2 sensor and BH1750 light sensor
- **Previous**: Major refactor to clean modular sensor platform
- **Documentation**: Updated README.md with current features

## Core Architecture
- **foundation_core.py**: Core framework
- **module_base.py**: Base class for all modules
- **code.py**: Main application entry point
- **settings.toml**: Configuration file

## Available Sensor Modules
### Environmental Sensors
- **module_sht45.py**: Temperature/humidity sensor (SHT45)
- **module_scd41.py**: CO2, temperature, humidity sensor (SCD41) - *Recently added*
- **module_bh1750.py**: Digital light sensor (BH1750) - *Recently added*

### System Modules
- **module_led_control.py**: Onboard LED control and status
- **module_rtc_control.py**: Real-time clock (PCF8523)
- **module_sd_card.py**: SD card data logging
- **module_battery_monitor.py**: Battery voltage monitoring
- **module_file_manager.py**: Web-based file editor
- **module_console_monitor.py**: Web-based REPL console

## Hardware Configuration
- **I2C Bus**: GP4 (SDA), GP5 (SCL)
- **SD Card**: SPI interface
- **Power**: USB or battery via STEMMA connector

## Development Tools
- **deploy.sh**: Deployment script
- **test_automation.py**: Testing framework
- **Code templates**: Various configurations (code_sht45.py, code_scd41.py, code_bh1750.py)

## Testing Strategy
- Individual module testing with dedicated code_*.py files
- Template-based workflow for different sensor combinations
- Hardware-first design approach

## Key Features
- Standalone WiFi hotspot operation
- Web-based dashboard and control
- Modular sensor architecture
- Built-in web IDE for live coding
- Data logging to SD card
- Real-time sensor monitoring

## Development Notes
- Project uses CircuitPython constraints and optimizations
- Modules kept in root directory to avoid import issues
- Simple, reliable architecture prioritized over abstraction
- Hardware compatibility tested with Adafruit breakouts

## Git Status
- Current branch: main
- Repository status: clean
- Recent focus: Expanding sensor module ecosystem

---
*This file helps maintain project context across Claude Code sessions*