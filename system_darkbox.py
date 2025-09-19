# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
system_darkbox.py
=================

System-level integration for the DarkBox experiment.
This file combines device modules into a unified application according to
the WicdPico architecture. Here, we start with only the BH1750 light sensor.

- Imports and instantiates BH1750Module (light sensor)
- Registers its routes with the HTTP server
- Provides composite dashboard HTML

Add additional modules and orchestration logic in later steps.
"""

from module_bh1750 import BH1750Module

class SystemDarkBox:
    def __init__(self, foundation):
        self.foundation = foundation
        self.bh1750_module = BH1750Module(foundation)
        # Optionally: add self.bh1750_module to a list of modules for orchestration

    def register_routes(self, server):
        # Register BH1750 routes
        self.bh1750_module.register_routes(server)
        # Add system-level or composite routes here as needed

    def get_dashboard_html(self):
        # Combine dashboards from all modules (only BH1750 for now)
        return self.bh1750_module.get_dashboard_html()

    def update(self):
        # Call update on each module
        self.bh1750_module.update()

    def cleanup(self):
        self.bh1750_module.cleanup()

# Example usage (in your application entrypoint):
# foundation = WicdPicoFoundation(...)
# system = SystemDarkBox(foundation)
# system.register_routes(server)
# dashboard_html = system.get_dashboard_html()
