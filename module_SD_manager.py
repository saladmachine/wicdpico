# module_SD_manager.py

import os
import gc
import board
import busio
import storage
import adafruit_sdcard
import digitalio
from module_base import WicdpicoModule
from adafruit_httpserver import Response
import re

def url_unquote(s):
    def repl(match):
        return chr(int(match.group(1), 16))
    return re.sub(r'%([0-9A-Fa-f]{2})', repl, s)

class SDManagerModule(WicdpicoModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "SD Manager"
        self.version = "v4.2 (Final)"
        self.path = "/files"
        self.mount_point = "/sd"
        self.card_available = False

        try:
            self._detect_and_mount_card()
            if self.card_available:
                self.foundation.startup_print("SD card detected and mounted successfully.")
            else:
                self.foundation.startup_print("SD card not detected or mount failed.")
        except Exception as e:
            self.card_available = False
            self.foundation.startup_print("SD card initialization failed: " + str(e))

    def _detect_and_mount_card(self):
        try:
            spi = busio.SPI(board.GP18, board.GP19, board.GP16)
            cs = digitalio.DigitalInOut(board.GP17)
            sdcard = adafruit_sdcard.SDCard(spi, cs)
            vfs = storage.VfsFat(sdcard)
            
            try:
                storage.umount(self.mount_point)
            except OSError:
                pass

            storage.mount(vfs, self.mount_point, readonly=False)
            self.card_available = True
            self.foundation.startup_print("SD card mounted at {}".format(self.mount_point))
        except Exception as e:
            self.card_available = False
            raise e
    
    # --- NEW METHOD TO CREATE THE DASHBOARD CARD ---
    def get_dashboard_html(self):
        """Generates the HTML dashboard widget for the SD Manager."""
        if self.card_available:
            status_text = "Mounted"
            status_color = "green"
        else:
            status_text = "Not Detected"
            status_color = "red"
        
        return f"""
        <div class="module">
            <h2>Files</h2>
            <p><strong>SD Card Status:</strong> <span style="color:{status_color};">{status_text}</span></p>
            <div class="control-group">
                <a href="/files"><button>Open File Manager</button></a>
            </div>
        </div>
        """

    def get_routes(self):
        return [
            ("/files", self.files_page),
            ("/list-files", self.list_files),
            ("/open-file", self.open_file),
            ("/create-file", self.create_file),
            ("/save-file", self.save_file),
            ("/delete-file", self.delete_file),
            ("/download_file", self.download_file),
        ]

    def register_routes(self, server):
        for route, handler in self.get_routes():
            server.route(route, methods=['GET', 'POST'])(handler)

    def files_page(self, request):
        module_html = '<div class="module">{}</div>'.format(self.get_html_template())
        full_page = self.foundation.templates.render_page("SD Manager", module_html)
        return Response(request, full_page, content_type="text/html")

    def list_files(self, request):
        files = []
        if self.card_available:
            try:
                for file in os.listdir(self.mount_point):
                    if not file.startswith('.'):
                        files.append("{}/{}".format(self.mount_point, file))
                response_body = "Files found:\n\n" + "\n".join(sorted(files))
            except Exception as e:
                response_body = "Error listing files: " + str(e)
        else:
            response_body = "No SD card mounted."
        return Response(request, response_body, content_type="text/plain")

    def open_file(self, request):
        try:
            filename = request.form_data.get('filename', '')
            if filename:
                with open(filename, 'r') as f: content = f.read()
                return Response(request, "File: {}\n\n{}".format(filename, content), content_type="text/plain")
            return Response(request, "No file specified.", content_type="text/plain")
        except Exception as e:
            return Response(request, "Error: Could not read file - {}".format(str(e)), content_type="text/plain")
        
    def download_file(self, request):
        try:
            # Get just the filename, not the full path
            filename = request.query_params.get("file", None)
            if not filename:
                return Response(request, "No file specified.", content_type="text/plain")
            
            filename = url_unquote(filename)
            
            # Reconstruct the full path on the server side
            filepath = self.mount_point + "/" + filename
            
            with open(filepath, "r") as f:
                file_content = f.read()
            
            headers = { "Content-Disposition": "attachment; filename={}".format(filename) }
            return Response(request, file_content, content_type="text/plain", headers=headers)
        
        except Exception as e:
            return Response(request, "Error downloading file: " + str(e), content_type="text/plain")

    def save_file(self, request):
        if not self.card_available: return Response(request, "Error: SD Card not available.", content_type="text/plain")
        try:
            filename = request.form_data.get('filename', '')
            content = request.form_data.get('content', '')
            if not filename.startswith(self.mount_point):
                 return Response(request, "Error: Can only save to SD card.", content_type="text/plain")

            with open(filename, 'w') as f: f.write(content)
            return Response(request, "File '{}' saved successfully!".format(filename), content_type="text/plain")
        except Exception as e:
            return Response(request, "Error: Could not save file - {}".format(str(e)), content_type="text/plain")

    def create_file(self, request):
        if not self.card_available: return Response(request, "Error: SD Card not available.", content_type="text/plain")
        try:
            filename = request.form_data.get('filename', '').strip()
            content = request.form_data.get('content', '')
            if not filename:
                return Response(request, "Filename cannot be empty.", content_type="text/plain")
            
            full_path = "{}/{}".format(self.mount_point, filename)

            try:
                os.stat(full_path)
                return Response(request, "Error: File '{}' already exists.".format(full_path), content_type="text/plain")
            except OSError:
                with open(full_path, 'w') as f: f.write(content)
                return Response(request, "File '{}' created successfully!".format(full_path), content_type="text/plain")
        except Exception as e:
            return Response(request, "Error: Could not create file - {}".format(str(e)), content_type="text/plain")

    def delete_file(self, request):
        if not self.card_available: return Response(request, "Error: SD Card not available.", content_type="text/plain")
        try:
            filename = request.form_data.get('filename', '')
            if not filename.startswith(self.mount_point):
                 return Response(request, "Error: Can only delete from SD card.", content_type="text/plain")
            os.remove(filename)
            return Response(request, "File '{}' deleted successfully!".format(filename), content_type="text/plain")
        except Exception as e:
            return Response(request, "Error: Could not delete file - {}".format(str(e)), content_type="text/plain")

    def get_html_template(self):
        card_info_html = "SD Card is mounted." if self.card_available else "SD Card is NOT mounted. File operations will fail."
        
        html_template = """
        <style>
        .file-list {{ margin-top: 20px; text-align: left; }}
        .files {{ border: 2px solid #e5e7eb; border-radius: 6px; max-height: 200px; overflow-y: auto; background-color: #f9fafb; }}
        .file-row {{ padding: 8px 12px; border-bottom: 1px solid #e5e7eb; cursor: pointer; }}
        .file-row:hover {{ background-color: #e5e7eb; }}
        #file-editor, #new-file-content {{ width: 100%; min-height: 300px; font-family: monospace; font-size: 14px; line-height: 1.4; padding: 12px; border: 2px solid #e5e7eb; border-radius: 6px; resize: vertical; margin-top: 10px; }}
        #new-file-content {{ min-height: 150px; }}
        </style>
        <h2>SD Manager {version_placeholder}</h2>
        <p>{card_info_placeholder}</p>
        <a href="/"><button>← Back to Dashboard</button></a>
        <button onclick="loadFileManager()">List Files</button>
        <button onclick="showCreateFile()">Create File</button>
        <div id="create-file-section" style="display: none; margin-top: 20px;">
            <h3>Create New File on SD Card</h3>
            <input type="text" id="new-filename" placeholder="filename.txt" style="width: 100%; padding: 8px;">
            <textarea id="new-file-content" placeholder="Enter file content..."></textarea>
            <button onclick="createFile()">Save New File</button>
            <button onclick="hideCreateFile()">Cancel</button>
        </div>
        <div id="file-operations" style="display: none; margin-top: 10px;">
            <span id="selected-file-span" style="font-family: monospace; padding-right: 10px;"></span>
            <button id="open-btn" onclick="openSelectedFile()">Open</button>
            <button id="download-btn" onclick="downloadSelectedFile()">Download</button>
            <button id="delete-btn" onclick="showDeleteConfirm()">Delete</button>
        </div>
        <div id="file-list-wrapper" style="display: none;">
            <div id="files" class="files"></div>
        </div>
        <div id="editor-section" style="display: none;">
            <h3 id="editor-title">Editing: </h3>
            <textarea id="file-editor"></textarea>
            <button onclick="saveFile()">Save Changes</button>
            <button onclick="closeEditor()">Close</button>
        </div>
        <script>
            let selectedFile = null;
            function showUi(elementId, show) {{ document.getElementById(elementId).style.display = show ? 'block' : 'none'; }}
            function selectFile(filename) {{
                selectedFile = filename;
                document.getElementById('selected-file-span').textContent = filename;
                showUi('file-operations', true);
                document.querySelectorAll('.file-row').forEach(row => {{
                    row.style.backgroundColor = row.textContent === filename ? '#dbeafe' : '';
                }});
            }}
            function loadFileManager() {{
                fetch('/list-files', {{ method: 'POST' }})
                .then(r => r.text())
                .then(text => {{
                    const lines = text.split('\\n');
                    const filesDiv = document.getElementById('files');
                    filesDiv.innerHTML = '';
                    if (lines[0].includes('Files found:')) {{
                        const files = lines.slice(2).filter(line => line.trim() !== '');
                        files.forEach(filename => {{
                            const row = document.createElement('div');
                            row.className = 'file-row';
                            row.textContent = filename;
                            row.onclick = () => selectFile(filename);
                            filesDiv.appendChild(row);
                        }});
                    }} else {{
                        filesDiv.textContent = lines[0];
                    }}
                    showUi('file-list-wrapper', true);
                    showUi('file-operations', false);
                    selectedFile = null;
                }});
            }}
            function openSelectedFile() {{
                if (!selectedFile) return;
                const formData = new FormData();
                formData.append('filename', selectedFile);
                fetch('/open-file', {{ method: 'POST', body: formData }})
                .then(r => r.text())
                .then(text => {{
                    const content = text.substring(text.indexOf('\\n\\n') + 2);
                    document.getElementById('editor-title').textContent = 'Editing: ' + selectedFile;
                    document.getElementById('file-editor').value = content;
                    showUi('editor-section', true);
                }});
            }}
            function downloadSelectedFile() {{
                if (!selectedFile) return;
                const filename = selectedFile.split('/').pop();
                window.location.href = '/download_file?file=' + encodeURIComponent(filename);
            }}
            function saveFile() {{
                if (!selectedFile) return;
                const content = document.getElementById('file-editor').value;
                const formData = new FormData();
                formData.append('filename', selectedFile);
                formData.append('content', content);
                fetch('/save-file', {{ method: 'POST', body: formData }})
                .then(r => r.text()).then(alert);
            }}
            function createFile() {{
                const filename = document.getElementById('new-filename').value.trim();
                const content = document.getElementById('new-file-content').value;
                if (!filename) {{ alert('Filename cannot be empty.'); return; }}
                const formData = new FormData();
                formData.append('filename', filename);
                formData.append('content', content);
                fetch('/create-file', {{ method: 'POST', body: formData }})
                .then(r => r.text())
                .then(result => {{
                    alert(result);
                    if (result.includes('created successfully')) {{
                        hideCreateFile();
                        loadFileManager();
                    }}
                }});
            }}
            function showDeleteConfirm() {{
                if (!selectedFile) return;
                if (confirm("Are you sure you want to delete '" + selectedFile + "'?")) {{
                    const formData = new FormData();
                    formData.append('filename', selectedFile);
                    fetch('/delete-file', {{ method: 'POST', body: formData }})
                    .then(r => r.text())
                    .then(result => {{
                        alert(result);
                        loadFileManager();
                    }});
                }}
            }}
            function showCreateFile() {{ showUi('create-file-section', true); }}
            function hideCreateFile() {{ showUi('create-file-section', false); }}
            function closeEditor() {{ showUi('editor-section', false); }}
        </script>
        """
        return html_template.format(
            card_info_placeholder=card_info_html,
            version_placeholder=self.version
        )