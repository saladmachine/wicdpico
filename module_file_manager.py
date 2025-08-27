from adafruit_httpserver import Response
import os
from module_base import WicdpicoModule

class FileManagerModule(WicdpicoModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "File Manager"
        self.path = "/files"

    def get_routes(self):
        return [
            ("/files", self.files_page),
            ("/list-files", self.list_files),
            ("/select-file", self.select_file),
            ("/open-file", self.open_file),
            ("/save-file", self.save_file),
            ("/create-file", self.create_file),
            ("/delete-file", self.delete_file)
        ]

    def register_routes(self, server):
        """Register all module routes with the server"""
        for route, handler in self.get_routes():
            server.route(route, methods=['GET', 'POST'])(handler)

    def files_page(self, request):
        module_html = f'<div class="module">{self.get_html_template()}</div>'
        full_page = self.foundation.templates.render_page("File Manager", module_html)
        return Response(request, full_page, content_type="text/html")

    def list_files(self, request):
        files = []
        try:
            # Try to list SD card files first (if mounted)
            sd_path = "/sd"
            try:
                if os.path.exists(sd_path):
                    for file in os.listdir(sd_path):
                        files.append(f"SD: {file}")
            except OSError:
                pass
            
            # Also show data files from root (where CSV might be saved)
            try:
                for file in os.listdir("/"):
                    # Only show data files, not system files
                    if file.endswith(('.csv', '.log', '.txt', '.json')):
                        files.append(file)
            except OSError:
                pass

        if files:
            file_list = "\n".join(files)
            response_body = f"Files found:\n\n{file_list}"
        else:
            response_body = "No files found in CIRCUITPY root directory."
        return Response(request, response_body, content_type="text/plain")

    def select_file(self, request):
        try:
            filename = request.form_data.get('filename', '')
            if filename:
                return Response(request, f"Open '{filename}'?", content_type="text/plain")
            else:
                return Response(request, "No file selected", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {str(e)}", content_type="text/plain")

    def open_file(self, request):
        try:
            filename = request.form_data.get('filename', '')
            if filename:
                try:
                    with open(filename, 'r') as f:
                        content = f.read()
                    return Response(request, f"File: {filename}\n\n{content}", content_type="text/plain")
                except OSError:
                    return Response(request, f"Error: Could not read file '{filename}'", content_type="text/plain")
            else:
                return Response(request, "No file specified", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {str(e)}", content_type="text/plain")

    def save_file(self, request):
        try:
            filename = request.form_data.get('filename', '')
            content = request.form_data.get('content', '')
            content = self.decode_html_entities(content)

            if filename:
                try:
                    with open(filename, 'w') as f:
                        f.write(content)
                    return Response(request, f"File '{filename}' saved successfully!", content_type="text/plain")
                except OSError as e:
                    return Response(request, f"Error: Could not save file '{filename}' - {str(e)}", content_type="text/plain")
            else:
                return Response(request, "No filename specified for saving", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {str(e)}", content_type="text/plain")

    def create_file(self, request):
        try:
            filename = request.form_data.get('filename', '')
            if not filename:
                return Response(request, "No filename specified", content_type="text/plain")

            try:
                with open(filename, 'r'):
                    return Response(request, f"Error: File '{filename}' already exists", content_type="text/plain")
            except OSError:
                try:
                    with open(filename, 'w') as f:
                        f.write('')
                    return Response(request, f"File '{filename}' created successfully!", content_type="text/plain")
                except OSError as e:
                    return Response(request, f"Error: Could not create file '{filename}' - {str(e)}", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {str(e)}", content_type="text/plain")

    def delete_file(self, request):
        try:
            filename = request.form_data.get('filename', '')
            if not filename:
                return Response(request, "No filename specified", content_type="text/plain")

            try:
                os.remove(filename)
                return Response(request, f"File '{filename}' deleted successfully!", content_type="text/plain")
            except OSError as e:
                return Response(request, f"Error: Could not delete file '{filename}' - {str(e)}", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {str(e)}", content_type="text/plain")

    def decode_html_entities(self, text):
        """Decode common HTML entities from web form submissions."""
        text = text.replace('&quot;', '"')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&#39;', "'")
        return text

    def get_html_template(self):
        return """
        <style>
        /* File Manager Styles */
        .file-list {
            margin-top: 20px;
            text-align: left;
        }

        .files {
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            max-height: 200px;
            overflow-y: auto;
            background-color: #f9fafb;
        }

        .file-row {
            padding: 8px 12px;
            border-bottom: 1px solid #e5e7eb;
            cursor: pointer;
            transition: background-color 0.2s ease;
            min-height: 44px;
            display: flex;
            align-items: center;
        }

        .file-row:hover {
            background-color: #e5e7eb;
        }

        #file-editor {
            width: 100%;
            min-height: 300px;
            font-family: 'Courier New', Consolas, Monaco, monospace;
            font-size: 14px;
            line-height: 1.4;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            resize: vertical;
            background-color: #fafafa;
        }
        </style>

        <h2>File Manager</h2>
        <a href="/" style="text-decoration: none;"><button>← Back to Dashboard</button></a>

        <button onclick="loadFileManager()">List Files</button>
        <button onclick="showCreateFile()">Create File</button>

        <div id="create-file-section" style="display: none;">
            <h3>Create New File:</h3>
            <input type="text" id="new-filename" placeholder="filename.py">
            <button onclick="createFile()">Create</button>
            <button onclick="hideCreateFile()">Cancel</button>
        </div>

        <button id="open-btn" style="display: none;" onclick="openSelectedFile()">Open</button>
        <button id="delete-btn" style="display: none;" onclick="showDeleteConfirm()">Delete</button>

        <div id="file-list" class="file-list" style="display: none;">
            <h3>Files:</h3>
            <div id="files" class="files"></div>
            <button onclick="closeFileList()">Close File List</button>
        </div>

        <div id="editor-section" style="display: none;">
            <h3 id="editor-title">Editing: filename</h3>
            <textarea id="file-editor" rows="20" cols="80"></textarea>
            <button onclick="saveFile()">Save</button>
            <button onclick="closeEditor()">Close</button>
        </div>

        <script>
        // File Manager JavaScript Functions
        function loadFileManager() {
            fetch('/list-files', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    const lines = result.split('\\n');
                    if (lines[0].includes('Files found:')) {
                        const files = lines.slice(2).filter(line => line.trim() !== '');
                        const filesDiv = document.getElementById('files');
                        filesDiv.innerHTML = '';
                        files.forEach(filename => {
                            const fileRow = document.createElement('div');
                            fileRow.className = 'file-row';
                            fileRow.textContent = filename;
                            fileRow.onclick = () => selectFile(filename);
                            filesDiv.appendChild(fileRow);
                        });
                        document.getElementById('file-list').style.display = 'block';
                    }
                });
        }

        function selectFile(filename) {
            const formData = new FormData();
            formData.append('filename', filename);
            fetch('/select-file', { method: 'POST', body: formData })
                .then(response => response.text())
                .then(result => {
                    document.getElementById('open-btn').style.display = 'inline-block';
                    document.getElementById('delete-btn').style.display = 'inline-block';
                    document.getElementById('open-btn').setAttribute('data-filename', filename);
                    document.getElementById('delete-btn').setAttribute('data-filename', filename);
                });
        }

        function openSelectedFile() {
            const filename = document.getElementById('open-btn').getAttribute('data-filename');
            const formData = new FormData();
            formData.append('filename', filename);
            fetch('/open-file', { method: 'POST', body: formData })
                .then(response => response.text())
                .then(result => {
                    const lines = result.split('\\n');
                    const content = lines.slice(2).join('\\n');
                    document.getElementById('file-editor').value = content;
                    document.getElementById('editor-title').textContent = `Editing: ${filename}`;
                    document.getElementById('editor-section').style.display = 'block';
                });
        }

        function saveFile() {
            const filename = document.getElementById('editor-title').textContent.replace('Editing: ', '');
            const content = document.getElementById('file-editor').value;
            const formData = new FormData();
            formData.append('filename', filename);
            formData.append('content', content);
            fetch('/save-file', { method: 'POST', body: formData })
                .then(response => response.text())
                .then(result => {
                    alert(result);
                });
        }

        function createFile() {
            const filename = document.getElementById('new-filename').value.trim();
            if (!filename) return;
            const formData = new FormData();
            formData.append('filename', filename);
            fetch('/create-file', { method: 'POST', body: formData })
                .then(response => response.text())
                .then(result => {
                    alert(result);
                    if (result.includes('created successfully')) {
                        hideCreateFile();
                        loadFileManager();
                    }
                });
        }

        function showCreateFile() {
            document.getElementById('create-file-section').style.display = 'block';
        }

        function hideCreateFile() {
            document.getElementById('create-file-section').style.display = 'none';
            document.getElementById('new-filename').value = '';
        }

        function showDeleteConfirm() {
            const filename = document.getElementById('delete-btn').getAttribute('data-filename');
            if (confirm(`Are you sure you want to delete '${filename}'?`)) {
                deleteSelectedFileConfirmed(filename);
            }
        }

        function deleteSelectedFileConfirmed(filename) {
            const formData = new FormData();
            formData.append('filename', filename);
            fetch('/delete-file', { method: 'POST', body: formData })
                .then(response => response.text())
                .then(result => {
                    alert(result);
                    if (result.includes('deleted successfully')) {
                        loadFileManager();
                    }
                });
        }

        function closeFileList() {
            document.getElementById('file-list').style.display = 'none';
            document.getElementById('open-btn').style.display = 'none';
            document.getElementById('delete-btn').style.display = 'none';
        }

        function closeEditor() {
            document.getElementById('editor-section').style.display = 'none';
        }
        </script>
        """

    def get_dashboard_html(self):
        """Return HTML for dashboard display"""
        return f'<a href="{self.path}" style="text-decoration: none;"><button style="width: 100%; margin: 5px 0;">Open {self.name}</button></a>'