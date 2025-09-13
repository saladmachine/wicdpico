# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`sd_card_module`
====================================================

SD Card control module for WicdPico system.

Provides web interface and management for SD card storage
on Raspberry Pi Pico with CircuitPython.

* Author(s): WicdPico Development Team
"""

import storage
import os
import gc
from module_base import WicdpicoModule
from adafruit_httpserver import Response

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/wicdpico/wicdpico.git"

class SDCardModule(WicdpicoModule):
    def __init__(self, foundation):
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
        try:
            statvfs = os.statvfs("/")
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
        if not filepath or not isinstance(filepath, str):
            return False
        dangerous_chars = ['..', '<', '>', '|', '*', '?', '"']
        for char in dangerous_chars:
            if char in filepath:
                return False
        if not filepath.startswith('/'):
            return False
        if '.' in filepath.split('/')[-1]:
            ext = '.' + filepath.split('.')[-1].lower()
            if ext not in self.allowed_extensions:
                self.foundation.startup_print(f"File extension {ext} not allowed")
                return False
        return True

    def _validate_file_size(self, content):
        size = len(content)
        if size > self.max_file_size:
            self.foundation.startup_print(f"File size {size} exceeds limit {self.max_file_size}")
            return False
        return True

    def create_directory(self, dirpath):
        if not self.card_available:
            return False
        if not self._validate_file_path(dirpath):
            return False
        try:
            os.mkdir(dirpath)
            self.foundation.startup_print(f"Directory created: {dirpath}")
            return True
        except OSError as e:
            if e.errno == 17:
                self.foundation.startup_print(f"Directory already exists: {dirpath}")
                return True
            else:
                self.foundation.startup_print(f"Error creating directory {dirpath}: {str(e)}")
                return False
        except Exception as e:
            self.foundation.startup_print(f"Error creating directory {dirpath}: {str(e)}")
            return False

    def delete_directory(self, dirpath, recursive=False):
        if not self.card_available:
            return False
        if not self._validate_file_path(dirpath):
            return False
        try:
            if recursive:
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
        if not self.card_available:
            return False
        if not self._validate_file_path(source_path) or not self._validate_file_path(dest_path):
            return False
        try:
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
        if not self.card_available:
            return False
        if self.copy_file(source_path, dest_path):
            if self.delete_file(source_path):
                self.foundation.startup_print(f"File moved: {source_path} -> {dest_path}")
                return True
            else:
                self.delete_file(dest_path)
                return False
        return False

    def get_file_extension(self, filepath):
        if '.' in filepath.split('/')[-1]:
            return '.' + filepath.split('.')[-1].lower()
        return ''

    def get_file_type(self, filepath):
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
        if not self.card_available:
            return []
        try:
            items = []
            for item in os.listdir(path):
                item_path = path.rstrip('/') + '/' + item if path != '/' else '/' + item
                try:
                    stat_result = os.stat(item_path)
                    is_dir = (stat_result[0] & 0x4000) != 0
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': 'directory' if is_dir else 'file',
                        'size': stat_result[6] if not is_dir else 0,
                        'file_type': 'Directory' if is_dir else self.get_file_type(item_path),
                        'extension': '' if is_dir else self.get_file_extension(item_path)
                    })
                except OSError:
                    continue
            return sorted(items, key=lambda x: (x['type'] == 'file', x['name'].lower()))
        except Exception as e:
            self.foundation.startup_print(f"Error listing directory {path}: {str(e)}")
            return []

    def create_file(self, filepath, content=""):
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
        if not self.card_available:
            return False
        if not self._validate_file_path(filepath):
            return False
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
        if not self.card_available:
            return False
        try:
            os.stat(filepath)
            return True
        except OSError:
            return False

    def get_file_info(self, filepath):
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
        if self.card_available:
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

    def get_dashboard_html(self):
        return """
        <div class="module">
            <h2>SD Card</h2>
            <div class="control-group">
                <form method="POST" action="/list_sd_files">
                    <button type="submit">SD Files</button>
                </form>
            </div>
        </div>
        """

    def register_routes(self, server):
        @server.route("/", methods=["GET"])
        def dashboard(request):
            css = """
            <style>
                .module {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 1em;
                    margin-bottom: 1em;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    background: #fff;
                }
                .control-group {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1em;
                    margin-top: 1em;
                }
                button {
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0.75em 2em;
                    cursor: pointer;
                    font-size: 1em;
                    margin: 0.5em 0;
                }
                button:active, button:focus {
                    outline: none;
                }
                .file-list {
                    margin-top: 1em;
                    font-size: 0.95em;
                }
                .file-list ul {
                    padding-left: 1.5em;
                }
                .file-content {
                    margin-top: 2em;
                    padding: 1em;
                    background: #f9f9f9;
                    border-radius: 8px;
                    border: 1px solid #eee;
                    font-family: monospace;
                    white-space: pre-wrap;
                }
            </style>
            """
            html = f"""
            <html>
            <head>
                <title>WicdPico SD Card Dashboard</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                {css}
            </head>
            <body>
                {self.get_dashboard_html()}
            </body>
            </html>
            """
            return Response(request, html, content_type="text/html")

        @server.route("/list_sd_files", methods=["GET", "POST"])
        def list_sd_files(request):
            css = """
            <style>
                .module {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 1em;
                    margin-bottom: 1em;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    background: #fff;
                }
                .control-group {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1em;
                    margin-top: 1em;
                }
                button {
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0.75em 2em;
                    cursor: pointer;
                    font-size: 1em;
                    margin: 0.5em 0;
                }
                button:active, button:focus {
                    outline: none;
                }
                .file-list {
                    margin-top: 1em;
                    font-size: 0.95em;
                }
                .file-list ul {
                    padding-left: 1.5em;
                }
                .file-content {
                    margin-top: 2em;
                    padding: 1em;
                    background: #f9f9f9;
                    border-radius: 8px;
                    border: 1px solid #eee;
                    font-family: monospace;
                    white-space: pre-wrap;
                }
            </style>
            """
            files = self.list_directory(self.mount_point)
            file_list_html = "<div class='file-list'><strong>SD Card Files:</strong><ul>"
            if files:
                for f in files:
                    if f['type'] == 'file':
                        file_list_html += (
                            f"<li><a href='/view_file?path={f['path']}'>{f['name']}</a> ({f['type']})</li>"
                        )
                    else:
                        file_list_html += f"<li>{f['name']} ({f['type']})</li>"
            else:
                file_list_html += "<li>No files found or SD card unavailable.</li>"
            file_list_html += "</ul></div>"

            html = f"""
            <html>
            <head>
                <title>WicdPico SD Card Dashboard</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                {css}
            </head>
            <body>
                {self.get_dashboard_html()}
                {file_list_html}
            </body>
            </html>
            """
            return Response(request, html, content_type="text/html")

        @server.route("/view_file", methods=["GET"])
        def view_file(request):
            css = """
            <style>
                .module {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 1em;
                    margin-bottom: 1em;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    background: #fff;
                }
                .file-content {
                    margin-top: 2em;
                    padding: 1em;
                    background: #f9f9f9;
                    border-radius: 8px;
                    border: 1px solid #eee;
                    font-family: monospace;
                    white-space: pre-wrap;
                }
            </style>
            """
            # Use request.query_params for CircuitPython
            file_path = request.query_params.get("path", "")
            file_name = file_path.split("/")[-1] if file_path else "Unknown"
            file_content = ""
            error_msg = ""
            if file_path and self.file_exists(file_path):
                file_content = self.read_file(file_path, max_size=4096)
                if file_content is None:
                    error_msg = "Error reading file."
            else:
                error_msg = "File not found or invalid path."

            def html_escape(text):
                return (
                    text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&#39;")
                ) if text else ""

            file_content_html = (
                f"<div class='file-content'><strong>{file_name}</strong><br><pre>{html_escape(file_content)}</pre></div>"
                if not error_msg else f"<div class='file-content'><strong>{error_msg}</strong></div>"
            )

            back_link = "<div style='margin-top:1em;'><a href='/list_sd_files'>&larr; Back to file list</a></div>"

            html = f"""
            <html>
            <head>
                <title>View SD Card File</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                {css}
            </head>
            <body>
                {self.get_dashboard_html()}
                {file_content_html}
                {back_link}
            </body>
            </html>
            """
            return Response(request, html, content_type="text/html")

    def update(self):
        pass

    def cleanup(self):
        pass

    @property
    def storage_info(self):
        if self.card_available:
            try:
                status = self.get_card_status()
                return status['card_info']
            except Exception:
                return None
        return None