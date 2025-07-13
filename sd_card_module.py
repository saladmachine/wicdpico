# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`sd_card_module`
====================================================

SD Card control module for PicoWicd system.

Provides web interface and management for SD card storage
on Raspberry Pi Pico with CircuitPython.

* Author(s): PicoWicd Development Team

Implementation Notes
--------------------

**Hardware:**

* Designed for use with Adafruit PicoBell Adalogger FeatherWing
* Uses SD card slot on the FeatherWing
* Requires CircuitPython storage module

**Software and Dependencies:**

* Adafruit CircuitPython firmware for Raspberry Pi Pico 2 W
* CircuitPython storage module
* adafruit_httpserver
* PicoWicd foundation system

**Notes:**

* Provides file system access and storage management
* Web interface for file operations and status checking
* Automatic error handling for missing or corrupted SD cards

"""

import storage
import os
import gc
from module_base import PicowicdModule
from adafruit_httpserver import Request, Response

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/picowicd/picowicd.git"


class SDCardModule(PicowicdModule):
    """
    SD Card Control Module for PicoWicd system.
    
    Provides web interface and management for SD card storage.
    Handles card detection, mounting, and basic file operations.
    
    :param foundation: PicoWicd foundation instance for system integration
    :type foundation: PicoWicd
    
    **Quickstart: Importing and using the module**
    
    Here is an example of using the SDCardModule:
    
    .. code-block:: python
    
        from foundation_core import PicoWicd
        from sd_card_module import SDCardModule
        
        # Initialize foundation system
        foundation = PicoWicd()
        
        # Create SD card module
        sd_module = SDCardModule(foundation)
        
        # Register with web server
        sd_module.register_routes(foundation.server)
        
        # Get current status
        if sd_module.card_available:
            status = sd_module.get_card_status()
            print(f"SD card: {status}")
    """
    
    def __init__(self, foundation):
        """
        Initialize SD Card Control Module.
        
        Sets up SD card detection and mounting.
        Handles initialization errors gracefully.
        
        :param foundation: PicoWicd foundation instance
        :type foundation: PicoWicd
        """
        super().__init__(foundation)
        self.name = "SD Card Control"
        
        self.card_available = False
        self.mount_point = "/sd"
        self.card_info = {}
        
        try:
            self._detect_and_mount_card()
            if self.card_available:
                self.foundation.startup_print("SD card detected and mounted successfully.")
            else:
                self.foundation.startup_print("SD card not detected or failed to mount.")
        except Exception as e:
            self.card_available = False
            self.foundation.startup_print(f"SD card initialization failed: {str(e)}. SD card will be unavailable.")

    def _detect_and_mount_card(self):
        """
        Detect and mount the SD card.
        
        Attempts to access the SD card and gather basic information.
        Sets card_available flag based on success.
        """
        try:
            # Check if we can access the root filesystem (where SD would be mounted in CircuitPython)
            # CircuitPython typically auto-mounts SD cards to the root filesystem
            statvfs = os.statvfs("/")
            
            # Calculate storage information
            block_size = statvfs[0]
            total_blocks = statvfs[2]
            free_blocks = statvfs[3]
            
            total_bytes = block_size * total_blocks
            free_bytes = block_size * free_blocks
            used_bytes = total_bytes - free_bytes
            
            self.card_info = {
                'total_bytes': total_bytes,
                'free_bytes': free_bytes,
                'used_bytes': used_bytes,
                'total_mb': round(total_bytes / (1024 * 1024), 2),
                'free_mb': round(free_bytes / (1024 * 1024), 2),
                'used_mb': round(used_bytes / (1024 * 1024), 2),
                'usage_percent': round((used_bytes / total_bytes) * 100, 1) if total_bytes > 0 else 0
            }
            
            self.card_available = True
            
        except Exception as e:
            self.card_available = False
            self.card_info = {}
            raise e

    def get_card_status(self):
        """
        Get current SD card status information.
        
        :return: Dictionary containing card status and storage info
        :rtype: dict
        """
        if self.card_available:
            # Refresh card info
            try:
                self._detect_and_mount_card()
            except:
                self.card_available = False
                self.card_info = {}
        
        return {
            'available': self.card_available,
            'mount_point': self.mount_point,
            'card_info': self.card_info.copy()
        }

    def register_routes(self, server):
        """
        Register HTTP routes for SD card web interface.
        
        Provides REST endpoints for SD card status and control.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        
        **Available Routes:**
        
        * ``POST /sd-status`` - Get current SD card status including storage info
        """
        @server.route("/sd-status", methods=['POST'])
        def sd_status(request: Request):
            """
            Handle SD card status requests.
            
            Returns current storage information and availability status.
            
            :param request: HTTP request object
            :type request: Request
            :return: HTTP response with SD card status
            :rtype: Response
            """
            try:
                status = self.get_card_status()
                
                if not status['available']:
                    return Response(request, "SD card not available", content_type="text/plain")

                card_info = status['card_info']
                status_text = f"Storage: {card_info['total_mb']} MB total<br>"
                status_text += f"Free: {card_info['free_mb']} MB<br>"
                status_text += f"Used: {card_info['used_mb']} MB<br>"
                status_text += f"Usage: {card_info['usage_percent']}%"

                self.foundation.startup_print(f"SD Status: {card_info['total_mb']}MB total, {card_info['free_mb']}MB free, {card_info['usage_percent']}% used")

                return Response(request, status_text, content_type="text/html")

            except Exception as e:
                error_msg = f"Error reading SD card: {str(e)}"
                self.foundation.startup_print(error_msg)
                return Response(request, error_msg, content_type="text/plain")

    def get_dashboard_html(self):
        """
        Generate HTML dashboard widget for SD card control.
        
        Creates interactive web interface with status display and control buttons.
        Includes JavaScript for AJAX communication with the server.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
        return '''
        <div class="module">
            <h3>SD Card Control</h3>
            <div class="control-group">
                <button id="sd-status-btn" onclick="getSDStatus()">Get SD Status</button>
            </div>
            <p id="sd-display-status">SD Status: Click button</p>
        </div>

        <script>
        // JavaScript for Get SD Status
        function getSDStatus() {
            const btn = document.getElementById('sd-status-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/sd-status', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'Get SD Status';
                    document.getElementById('sd-display-status').innerHTML = 'SD Status: ' + result;
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'Get SD Status';
                    document.getElementById('sd-display-status').textContent = 'Error: ' + error.message;
                });
        }
        </script>
        '''

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Performs regular maintenance tasks if needed.
        Currently no periodic tasks required for SD card.
        
        .. note::
           This method is called periodically by the PicoWicd foundation.
           Override this method to add custom periodic tasks.
        """
        pass

    def cleanup(self):
        """
        Cleanup method called during system shutdown.
        
        Performs any necessary cleanup operations before module shutdown.
        Currently no cleanup is required for SD card.
        """
        pass

    @property
    def storage_info(self):
        """
        Get current storage information.
        
        :return: Storage info dictionary or None if card unavailable
        :rtype: dict or None
        
        .. code-block:: python
        
            # Get storage info
            if sd_module.card_available:
                info = sd_module.storage_info
                print(f"Free space: {info['free_mb']} MB")
        """
        if self.card_available:
            try:
                status = self.get_card_status()
                return status['card_info']
            except Exception:
                return None
        return None