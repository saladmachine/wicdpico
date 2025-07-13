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
        self.max_file_size = 1024 * 1024  # 1MB default limit
        self.allowed_extensions = ['.txt', '.log', '.json', '.csv', '.py', '.md', '.html', '.css', '.js']
        
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

    def _validate_file_path(self, filepath):
        """
        Validate file path for safety and compatibility.
        
        :param filepath: Path to validate
        :type filepath: str
        :return: True if valid, False otherwise
        :rtype: bool
        """
        if not filepath or not isinstance(filepath, str):
            return False
        
        # Check for dangerous path components
        dangerous_chars = ['..', '<', '>', '|', '*', '?', '"']
        for char in dangerous_chars:
            if char in filepath:
                return False
        
        # Must start with /
        if not filepath.startswith('/'):
            return False
        
        # Check file extension if it's a file (has extension)
        if '.' in filepath.split('/')[-1]:
            ext = '.' + filepath.split('.')[-1].lower()
            if ext not in self.allowed_extensions:
                self.foundation.startup_print(f"File extension {ext} not allowed")
                return False
        
        return True

    def _validate_file_size(self, content):
        """
        Validate content size against limits.
        
        :param content: Content to validate
        :type content: str or bytes
        :return: True if valid, False otherwise
        :rtype: bool
        """
        size = len(content)
        if size > self.max_file_size:
            self.foundation.startup_print(f"File size {size} exceeds limit {self.max_file_size}")
            return False
        return True

    def create_directory(self, dirpath):
        """
        Create a new directory.
        
        :param dirpath: Path to the directory to create
        :type dirpath: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        if not self._validate_file_path(dirpath):
            return False
        
        try:
            os.mkdir(dirpath)
            self.foundation.startup_print(f"Directory created: {dirpath}")
            return True
        except OSError as e:
            if e.errno == 17:  # Directory already exists
                self.foundation.startup_print(f"Directory already exists: {dirpath}")
                return True
            else:
                self.foundation.startup_print(f"Error creating directory {dirpath}: {str(e)}")
                return False
        except Exception as e:
            self.foundation.startup_print(f"Error creating directory {dirpath}: {str(e)}")
            return False

    def delete_directory(self, dirpath, recursive=False):
        """
        Delete a directory.
        
        :param dirpath: Path to the directory to delete
        :type dirpath: str
        :param recursive: If True, delete contents recursively
        :type recursive: bool
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        if not self._validate_file_path(dirpath):
            return False
        
        try:
            if recursive:
                # Delete contents first
                items = self.list_directory(dirpath)
                for item in items:
                    if item['type'] == 'directory':
                        self.delete_directory(item['path'], recursive=True)
                    else:
                        self.delete_file(item['path'])
            
            os.rmdir(dirpath)
            self.foundation.startup_print(f"Directory deleted: {dirpath}")
            return True
        except Exception as e:
            self.foundation.startup_print(f"Error deleting directory {dirpath}: {str(e)}")
            return False

    def copy_file(self, source_path, dest_path):
        """
        Copy a file from source to destination.
        
        :param source_path: Source file path
        :type source_path: str
        :param dest_path: Destination file path
        :type dest_path: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        if not self._validate_file_path(source_path) or not self._validate_file_path(dest_path):
            return False
        
        try:
            # Read source file in chunks to handle large files
            chunk_size = 1024
            with open(source_path, 'rb') as src:
                with open(dest_path, 'wb') as dst:
                    while True:
                        chunk = src.read(chunk_size)
                        if not chunk:
                            break
                        dst.write(chunk)
            
            self.foundation.startup_print(f"File copied: {source_path} -> {dest_path}")
            return True
        except Exception as e:
            self.foundation.startup_print(f"Error copying file {source_path} to {dest_path}: {str(e)}")
            return False

    def move_file(self, source_path, dest_path):
        """
        Move a file from source to destination.
        
        :param source_path: Source file path
        :type source_path: str
        :param dest_path: Destination file path
        :type dest_path: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        if self.copy_file(source_path, dest_path):
            if self.delete_file(source_path):
                self.foundation.startup_print(f"File moved: {source_path} -> {dest_path}")
                return True
            else:
                # Clean up destination if source deletion failed
                self.delete_file(dest_path)
                return False
        return False

    def get_file_extension(self, filepath):
        """
        Get file extension from path.
        
        :param filepath: File path
        :type filepath: str
        :return: File extension (including dot) or empty string
        :rtype: str
        """
        if '.' in filepath.split('/')[-1]:
            return '.' + filepath.split('.')[-1].lower()
        return ''

    def get_file_type(self, filepath):
        """
        Determine file type based on extension.
        
        :param filepath: File path
        :type filepath: str
        :return: File type description
        :rtype: str
        """
        ext = self.get_file_extension(filepath)
        
        type_map = {
            '.txt': 'Text File',
            '.log': 'Log File',
            '.json': 'JSON Data',
            '.csv': 'CSV Data',
            '.py': 'Python Code',
            '.md': 'Markdown',
            '.html': 'HTML Document',
            '.css': 'Stylesheet',
            '.js': 'JavaScript'
        }
        
        return type_map.get(ext, 'Unknown File')

    def list_directory(self, path="/"):
        """
        List contents of a directory on the SD card.
        
        :param path: Directory path to list (default: root)
        :type path: str
        :return: List of dictionaries containing file/directory info
        :rtype: list
        """
        if not self.card_available:
            return []
        
        try:
            items = []
            for item in os.listdir(path):
                item_path = path.rstrip('/') + '/' + item if path != '/' else '/' + item
                try:
                    stat_result = os.stat(item_path)
                    is_dir = (stat_result[0] & 0x4000) != 0  # Check if directory
                    
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': 'directory' if is_dir else 'file',
                        'size': stat_result[6] if not is_dir else 0,
                        'file_type': 'Directory' if is_dir else self.get_file_type(item_path),
                        'extension': '' if is_dir else self.get_file_extension(item_path)
                    })
                except OSError:
                    # Skip items we can't stat
                    continue
            
            return sorted(items, key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
        except Exception as e:
            self.foundation.startup_print(f"Error listing directory {path}: {str(e)}")
            return []

    def create_file(self, filepath, content=""):
        """
        Create a new file with optional content.
        
        :param filepath: Path to the file to create
        :type filepath: str
        :param content: Initial content for the file
        :type content: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        if not self._validate_file_path(filepath):
            return False
        
        if not self._validate_file_size(content):
            return False
        
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            self.foundation.startup_print(f"File created: {filepath}")
            return True
        except Exception as e:
            self.foundation.startup_print(f"Error creating file {filepath}: {str(e)}")
            return False

    def read_file(self, filepath, max_size=1024):
        """
        Read content from a file.
        
        :param filepath: Path to the file to read
        :type filepath: str
        :param max_size: Maximum number of bytes to read
        :type max_size: int
        :return: File content as string, or None if error
        :rtype: str or None
        """
        if not self.card_available:
            return None
        
        try:
            with open(filepath, 'r') as f:
                content = f.read(max_size)
            return content
        except Exception as e:
            self.foundation.startup_print(f"Error reading file {filepath}: {str(e)}")
            return None

    def write_file(self, filepath, content, append=False):
        """
        Write content to a file.
        
        :param filepath: Path to the file to write
        :type filepath: str
        :param content: Content to write to the file
        :type content: str
        :param append: If True, append to file; if False, overwrite
        :type append: bool
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        if not self._validate_file_path(filepath):
            return False
        
        # For append mode, check final size
        if append and self.file_exists(filepath):
            existing_size = self.get_file_info(filepath)
            if existing_size:
                total_size = existing_size.get('size', 0) + len(content)
                if total_size > self.max_file_size:
                    self.foundation.startup_print(f"Append would exceed file size limit")
                    return False
        elif not self._validate_file_size(content):
            return False
        
        try:
            mode = 'a' if append else 'w'
            with open(filepath, mode) as f:
                f.write(content)
            self.foundation.startup_print(f"File {'appended' if append else 'written'}: {filepath}")
            return True
        except Exception as e:
            self.foundation.startup_print(f"Error writing file {filepath}: {str(e)}")
            return False

    def delete_file(self, filepath):
        """
        Delete a file from the SD card.
        
        :param filepath: Path to the file to delete
        :type filepath: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        try:
            os.remove(filepath)
            self.foundation.startup_print(f"File deleted: {filepath}")
            return True
        except Exception as e:
            self.foundation.startup_print(f"Error deleting file {filepath}: {str(e)}")
            return False

    def file_exists(self, filepath):
        """
        Check if a file exists on the SD card.
        
        :param filepath: Path to check
        :type filepath: str
        :return: True if file exists, False otherwise
        :rtype: bool
        """
        if not self.card_available:
            return False
        
        try:
            os.stat(filepath)
            return True
        except OSError:
            return False

    def get_file_info(self, filepath):
        """
        Get detailed information about a file.
        
        :param filepath: Path to the file
        :type filepath: str
        :return: Dictionary with file info or None if error
        :rtype: dict or None
        """
        if not self.card_available:
            return None
        
        try:
            stat_result = os.stat(filepath)
            is_dir = (stat_result[0] & 0x4000) != 0
            
            return {
                'name': filepath.split('/')[-1],
                'path': filepath,
                'type': 'directory' if is_dir else 'file',
                'size': stat_result[6] if not is_dir else 0,
                'file_type': 'Directory' if is_dir else self.get_file_type(filepath),
                'extension': '' if is_dir else self.get_file_extension(filepath),
                'exists': True
            }
        except Exception as e:
            return None

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
        """
        @server.route("/sd-status", methods=['POST'])
        def sd_status(request: Request):
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

        @server.route("/sd-files", methods=['POST'])
        def sd_files(request: Request):
            try:
                if not self.card_available:
                    return Response(request, "SD card not available", content_type="text/plain")

                # Get directory path from request, default to root
                path = "/"
                if hasattr(request, 'form') and 'path' in request.form:
                    path = request.form['path']

                files = self.list_directory(path)
                
                if not files:
                    return Response(request, f"No files found in {path}", content_type="text/plain")

                # Build HTML file listing
                files_html = f"<strong>Contents of {path}:</strong><br><br>"
                
                for item in files:
                    icon = "📁" if item['type'] == 'directory' else "📄"
                    size_text = f" ({item['size']} bytes)" if item['type'] == 'file' else ""
                    files_html += f"{icon} {item['name']}{size_text}<br>"

                self.foundation.startup_print(f"SD Files: Listed {len(files)} items in {path}")

                return Response(request, files_html, content_type="text/html")

            except Exception as e:
                error_msg = f"Error listing SD files: {str(e)}"
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
                <button id="sd-files-btn" onclick="getSDFiles()">List Files</button>
                <a href="/sd-browse" target="_blank" class="btn" style="display: inline-block; padding: 8px 16px; background: #27ae60; color: white; text-decoration: none; border-radius: 4px;">File Browser</a>
            </div>
            <p id="sd-display-status">SD Status: Click button</p>
            <div id="sd-file-list" style="margin-top: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px; display: none;">
                <strong>Files:</strong><br>
                <div id="sd-files-content"></div>
            </div>
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

        // JavaScript for List Files
        function getSDFiles() {
            const btn = document.getElementById('sd-files-btn');
            const fileList = document.getElementById('sd-file-list');
            const filesContent = document.getElementById('sd-files-content');
            
            btn.disabled = true;
            btn.textContent = 'Loading...';

            fetch('/sd-files', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    btn.disabled = false;
                    btn.textContent = 'List Files';
                    filesContent.innerHTML = result;
                    fileList.style.display = 'block';
                })
                .catch(error => {
                    btn.disabled = false;
                    btn.textContent = 'List Files';
                    filesContent.textContent = 'Error: ' + error.message;
                    fileList.style.display = 'block';
                });
        }
        </script>
        '''

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Performs regular maintenance tasks if needed.
        Currently no periodic tasks required for SD card.
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
        """
        if self.card_available:
            try:
                status = self.get_card_status()
                return status['card_info']
            except Exception:
                return None
        return None