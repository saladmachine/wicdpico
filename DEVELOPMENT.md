# Picowicd Development Workflow

Quick reference for daily coding and testing with CircuitPython.

 push
```

## File Structure

### Repository Structure
```
picowicd/
├── lib/                    # Our custom CircuitPython libraries
│   ├── foundation_core.py  # Core foundation system
│   ├── foundation_templates.py # Responsive web templates
│   ├── module_base.py     # Base class for modules
│   └── led_blinky.py      # Example LED control module
├── tests/
│   └── test_led_blinky.py # Hardware test application
└── DEVELOPMENT.md         # This file
```

### CIRCUITPY Structure (after deployment)
```
CIRCUITPY/
├── code.py               # Main application (copied from tests/)
├── lib/
│   ├── adafruit_*        # Third-party libraries (don't commit)
│   ├── foundation_core.py    # Our files (deployed)
│   ├── foundation_templates.py
│   ├── module_base.py
│   └── led_blinky.py
└── config.py            # WiFi credentials
```

## Quick Commands

### Deploy Everything
```bash
# From picowicd directory
rsync -av lib/ /media/joepardue/CIRCUITPY/lib/ && cp tests/test_led_blinky.py /media/joepardue/CIRCUITPY/code.py
```

### Deploy Just Libraries (if test file unchanged)
```bash
rsync -av lib/ /media/joepardue/CIRCUITPY/lib/
```

### Check What's Different
```bash
# See what changed
rsync -av --dry-run lib/ /media/joepardue/CIRCUITPY/lib/
```

## Creating New Modules

### 1. Create Module File
```bash
# Create new module in lib/
touch lib/my_new_module.py
```

### 2. Follow Module Pattern
```python
from module_base import PicowidModule
from adafruit_httpserver import Request, Response

class MyNewModule(PicowidModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        # Initialize hardware/state
        
    def register_routes(self, server):
        @server.route("/my_endpoint", methods=['POST'])
        def handle_action(request: Request):
            return Response(request, "result")
    
    def get_dashboard_html(self):
        return '''<h3>My Module</h3><button onclick="myAction()">Click</button>'''
    
    def update(self):
        pass  # Called from main loop
```

### 3. Register in Test Application
```python
# In tests/test_*.py
new_module = MyNewModule(foundation)
foundation.register_module("my_module", new_module)
```

### 4. Deploy and Test
```bash
rsync -av lib/ /media/joepardue/CIRCUITPY/lib/
cp tests/test_my_module.py /media/joepardue/CIRCUITPY/code.py
```

## Troubleshooting

### Import Errors
- ✅ All custom files are in `/lib` directory
- ✅ Imports use direct names: `from foundation_core import PicowidFoundation`
- ✅ No subdirectory imports: avoid `from src.foundation import...`

### WiFi Issues
- Check `config.py` on CIRCUITPY has correct SSID/password
- Look for network name in WiFi settings
- Verify IP: http://192.168.4.1

### Web Interface Issues
- Check serial console for startup messages
- Verify all modules loaded (count should match registered modules)
- Try desktop browser first, then mobile

## Hardware Requirements

- Raspberry Pi Pico W with CircuitPython 8.x+
- USB connection for development
- WiFi capability for web interface

## Next Development Phases

**Phase 2: Rebuild Picowide Modules**
- File Manager Module
- Console Monitor Module  
- Power Management Module

**Phase 3: Instrument Control**
- I2C Interface Module
- Sensor modules (ColorPAR, etc.)
- Data logging and visualization
