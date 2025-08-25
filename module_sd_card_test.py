# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
SD Card Test Module for PicoBell Adalogger
==========================================

Test implementation of SD card functionality with proper SPI mounting
for Adafruit PicoBell Adalogger FeatherWing on Raspberry Pi Pico 2 W.

* Author(s): WicdPico Development Team

Implementation Notes
--------------------

**Hardware:**
* Adafruit PicoBell Adalogger FeatherWing
* SPI Pins: MOSI=GP19, MISO=GP16, SCK=GP18, CS=GP17
* Requires sdcardio library (CircuitPython 6.0+)

**Features:**
* Proper SPI mounting to /sd directory
* Test data generation (5x5 sensor data matrix)
* Web interface for file operations
* Download functionality with proper streaming
* File listing and management

"""

import board
import busio
import sdcardio
import storage
import os
import time
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response, FileResponse

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/wicdpico/wicdpico.git"


class SDCardTestModule(WicdpicoModule):
    """
    SD Card Test Module for WicdPico system.
    
    Provides proper SD card mounting and test data generation for
    validating SD card functionality on PicoBell Adalogger.
    """
    
    def __init__(self, foundation):
        """
        Initialize SD Card Test Module.
        
        Sets up SPI communication and mounts SD card to /sd directory.
        Creates test data for validation purposes.
        """
        super().__init__(foundation)
        self.name = "SD Card Test"
        
        self.sd_mounted = False
        self.mount_point = "/sd"
        self.test_data_file = "/sd/test_data.csv"
        
        # Test data configuration
        self.test_data_rows = 5
        self.test_data_cols = 5
        self.last_data_update = 0
        self.data_update_interval = 30  # seconds
        
        try:
            self._mount_sd_card()
            if self.sd_mounted:
                self.foundation.startup_print("SD card mounted successfully to /sd")
                self._create_sd_directory()
                self._generate_test_data()
            else:
                self.foundation.startup_print("SD card mounting failed")
        except Exception as e:
            self.sd_mounted = False
            self.foundation.startup_print("SD card initialization error: " + str(e))

    def _mount_sd_card(self):
        """
        Mount SD card using proper SPI configuration for PicoBell Adalogger.
        
        Pin configuration:
        - MOSI: GP19
        - MISO: GP16  
        - SCK: GP18
        - CS: GP17
        """
        try:
            # Create SPI interface with PicoBell Adalogger pins
            spi = busio.SPI(board.GP18, board.GP19, board.GP16)  # SCK, MOSI, MISO
            
            # Create SD card object with chip select pin
            sdcard = sdcardio.SDCard(spi, board.GP17)  # CS pin
            
            # Create filesystem and mount
            vfs = storage.VfsFat(sdcard)
            storage.mount(vfs, self.mount_point)
            
            self.sd_mounted = True
            self.foundation.startup_print("SD SPI mounted: SCK=GP18, MOSI=GP19, MISO=GP16, CS=GP17")
            
        except Exception as e:
            self.sd_mounted = False
            raise Exception("SD mount failed: " + str(e))

    def _create_sd_directory(self):
        """Create required directories on SD card if they don't exist."""
        try:
            # Create /sd directory on CIRCUITPY if it doesn't exist
            # (Required for CircuitPython 9+)
            if not self._path_exists("/sd"):
                os.mkdir("/sd")
            
            # Create data directory on SD card
            data_dir = "/sd/data"
            if not self._path_exists(data_dir):
                os.mkdir(data_dir)
                self.foundation.startup_print("Created /sd/data directory")
                
        except Exception as e:
            self.foundation.startup_print("Directory creation error: " + str(e))

    def _path_exists(self, path):
        """Check if path exists."""
        try:
            os.stat(path)
            return True
        except OSError:
            return False

    def _generate_test_data(self):
        """
        Generate 5x5 test data matrix mimicking real sensor logging.
        
        Creates CSV file with timestamp, temp1-5, humidity1-5 columns.
        """
        if not self.sd_mounted:
            return
            
        try:
            # Generate header
            header = "timestamp"
            for i in range(self.test_data_cols):
                header += ",temp" + str(i+1) + ",humidity" + str(i+1)
            header += "\n"
            
            # Generate 5 rows of test data
            current_time = time.monotonic()
            data_content = header
            
            for row in range(self.test_data_rows):
                # Simulate timestamp (5 minute intervals)
                timestamp = "2025-01-25 10:" + "{:02d}".format(row * 5) + ":00"
                line = timestamp
                
                # Generate temperature and humidity data for 5 sensors
                for col in range(self.test_data_cols):
                    temp = 20.0 + (row * 0.5) + (col * 0.2)  # Gradually increasing temp
                    humidity = 50.0 + (row * 1.0) + (col * 0.5)  # Gradually increasing humidity
                    line += "," + str(round(temp, 1)) + "," + str(round(humidity, 1))
                
                line += "\n"
                data_content += line
            
            # Write test data to SD card
            with open(self.test_data_file, "w") as f:
                f.write(data_content)
                f.flush()
            
            self.foundation.startup_print("Generated test data: " + str(self.test_data_rows) + "x" + str(self.test_data_cols*2) + " data points")
            
        except Exception as e:
            self.foundation.startup_print("Test data generation failed: " + str(e))

    def _update_test_data(self):
        """
        Periodically append new test data to simulate ongoing logging.
        """
        if not self.sd_mounted:
            return
            
        current_time = time.monotonic()
        if current_time - self.last_data_update < self.data_update_interval:
            return
            
        try:
            # Generate new data row
            row_count = self._get_csv_row_count()
            timestamp = "2025-01-25 10:" + "{:02d}".format((row_count * 5) % 60) + ":00"
            line = timestamp
            
            # Generate new sensor data
            for col in range(self.test_data_cols):
                temp = 20.0 + (row_count * 0.3) + (col * 0.1)
                humidity = 50.0 + (row_count * 0.7) + (col * 0.3)
                line += "," + str(round(temp, 1)) + "," + str(round(humidity, 1))
            
            line += "\n"
            
            # Append to file
            with open(self.test_data_file, "a") as f:
                f.write(line)
                f.flush()
            
            self.last_data_update = current_time
            self.foundation.startup_print("Appended test data row: " + str(row_count + 1))
            
        except Exception as e:
            self.foundation.startup_print("Test data update failed: " + str(e))

    def _get_csv_row_count(self):
        """Count number of data rows in CSV file (excluding header)."""
        try:
            with open(self.test_data_file, "r") as f:
                lines = f.readlines()
                return len(lines) - 1  # Subtract 1 for header
        except:
            return 0

    def list_sd_files(self, path="/sd"):
        """
        List files and directories on SD card.
        
        Returns list of dictionaries with file information.
        """
        if not self.sd_mounted:
            return []
        
        try:
            items = []
            for item in os.listdir(path):
                item_path = path.rstrip('/') + '/' + item if path != '/sd' else '/sd/' + item
                try:
                    stat_result = os.stat(item_path)
                    is_dir = (stat_result[0] & 0x4000) != 0
                    
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': 'directory' if is_dir else 'file',
                        'size': stat_result[6] if not is_dir else 0,
                    })
                except OSError:
                    continue
            
            return sorted(items, key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
        except Exception as e:
            self.foundation.startup_print("Error listing SD files: " + str(e))
            return []

    def get_sd_storage_info(self):
        """Get SD card storage information."""
        if not self.sd_mounted:
            return None
            
        try:
            statvfs = os.statvfs("/sd")
            block_size = statvfs[0]
            total_blocks = statvfs[2]
            free_blocks = statvfs[3]
            
            total_bytes = block_size * total_blocks
            free_bytes = block_size * free_blocks
            used_bytes = total_bytes - free_bytes
            
            return {
                'total_mb': round(total_bytes / (1024 * 1024), 2),
                'free_mb': round(free_bytes / (1024 * 1024), 2),
                'used_mb': round(used_bytes / (1024 * 1024), 2),
                'usage_percent': round((used_bytes / total_bytes) * 100, 1) if total_bytes > 0 else 0
            }
        except Exception as e:
            self.foundation.startup_print("Error getting SD storage info: " + str(e))
            return None

    def register_routes(self, server):
        """Register HTTP routes for SD card web interface."""
        
        @server.route("/sd-test-status", methods=['POST'])
        def sd_test_status(request: Request):
            """Get SD card status and storage information."""
            try:
                if not self.sd_mounted:
                    return Response(request, "SD card not mounted", content_type="text/plain")

                storage_info = self.get_sd_storage_info()
                if not storage_info:
                    return Response(request, "Error reading SD card storage", content_type="text/plain")

                status_text = "SD Card Status: Mounted<br>"
                status_text += "Storage: " + str(storage_info['total_mb']) + " MB total<br>"
                status_text += "Free: " + str(storage_info['free_mb']) + " MB<br>"
                status_text += "Used: " + str(storage_info['used_mb']) + " MB<br>"
                status_text += "Usage: " + str(storage_info['usage_percent']) + "%<br>"
                status_text += "Test file rows: " + str(self._get_csv_row_count() + 1)  # +1 for header

                return Response(request, status_text, content_type="text/html")

            except Exception as e:
                error_msg = "SD card status error: " + str(e)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/sd-test-files", methods=['POST'])
        def sd_test_files(request: Request):
            """List files on SD card."""
            try:
                if not self.sd_mounted:
                    return Response(request, "SD card not mounted", content_type="text/plain")

                files = self.list_sd_files()
                
                if not files:
                    return Response(request, "No files found on SD card", content_type="text/plain")

                files_html = "<strong>SD Card Files:</strong><br><br>"
                for item in files:
                    icon = "📁" if item['type'] == 'directory' else "📄"
                    size_text = " (" + str(item['size']) + " bytes)" if item['type'] == 'file' else ""
                    files_html += icon + " " + item['name'] + size_text + "<br>"

                return Response(request, files_html, content_type="text/html")

            except Exception as e:
                error_msg = "SD file listing error: " + str(e)
                return Response(request, error_msg, content_type="text/plain")

        @server.route("/sd-test-download/<filename>", methods=['GET'])
        def sd_test_download(request: Request, filename: str):
            """Download file from SD card."""
            try:
                if not self.sd_mounted:
                    return Response(request, "SD card not mounted", content_type="text/plain")

                file_path = "/sd/" + filename
                
                # Validate file exists
                if not self._path_exists(file_path):
                    return Response(request, "File not found: " + filename, content_type="text/plain")

                # Return file using FileResponse
                return FileResponse(request, filename, root_path="/sd", 
                                  content_type="text/csv", as_attachment=True,
                                  download_filename=filename)

            except Exception as e:
                error_msg = "SD download error: " + str(e)
                return Response(request, error_msg, content_type="text/plain")

    def get_dashboard_html(self):
        """Generate HTML dashboard widget for SD card test."""
        return '''
        <div class="module">
            <h3>SD Card Test</h3>
            <div class="control-group">
                <button id="sd-test-status-btn" onclick="getSDTestStatus()">Get SD Status</button>
                <button id="sd-test-files-btn" onclick="getSDTestFiles()">List Files</button>
                <button id="sd-test-download-btn" onclick="downloadTestData()">Download Test Data</button>
            </div>
            <p id="sd-test-status">SD Status: Click button</p>
            <div id="sd-test-files" style="margin-top: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px; display: none;">
                <div id="sd-test-files-content"></div>
            </div>
        </div>

        <script>
        function getSDTestStatus() {
            const btn = document.getElementById('sd-test-status-btn');
            btn.disabled = true;
            btn.textContent = 'Reading...';

            fetch('/sd-test-status', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'Get SD Status';
                    document.getElementById('sd-test-status').innerHTML = result;
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'Get SD Status';
                    document.getElementById('sd-test-status').textContent = 'Error: ' + error.message;
                });
        }

        function getSDTestFiles() {
            const btn = document.getElementById('sd-test-files-btn');
            const fileDiv = document.getElementById('sd-test-files');
            const filesContent = document.getElementById('sd-test-files-content');
            
            btn.disabled = true;
            btn.textContent = 'Loading...';

            fetch('/sd-test-files', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'List Files';
                    filesContent.innerHTML = result;
                    fileDiv.style.display = 'block';
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'List Files';
                    filesContent.textContent = 'Error: ' + error.message;
                    fileDiv.style.display = 'block';
                });
        }

        function downloadTestData() {
            const btn = document.getElementById('sd-test-download-btn');
            btn.disabled = true;
            btn.textContent = 'Downloading...';

            // Create download link and trigger download
            const link = document.createElement('a');
            link.href = '/sd-test-download/test_data.csv';
            link.download = 'test_data.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Reset button after short delay
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = 'Download Test Data';
            }, 2000);
        }
        </script>
        '''

    def update(self):
        """Periodic update - add new test data every 30 seconds."""
        self._update_test_data()

    def cleanup(self):
        """Cleanup method called during system shutdown."""
        if self.sd_mounted:
            try:
                storage.umount("/sd")
                self.foundation.startup_print("SD card unmounted")
            except:
                pass

    @property 
    def mounted(self):
        """Check if SD card is currently mounted."""
        return self.sd_mounted