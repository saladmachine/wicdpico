from module_base import WicdpicoModule
from adafruit_httpserver import Response
import os
import re

def url_unquote(s):
    # Minimal URL decode for CircuitPython (handles %XX)
    def repl(match):
        return chr(int(match.group(1), 16))
    return re.sub(r'%([0-9A-Fa-f]{2})', repl, s)

class MonitorModule(WicdpicoModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Monitor"
        self.path = "/monitor"
        self.monitor_enabled = False
        self.console_buffer = []
        self.log_file = "/monitor.log"
        self.buffer_size = 50  # Could be loaded from settings.toml

    def register_routes(self, server):
        server.route(self.path, methods=['GET'])(self.serve_monitor_page)
        server.route("/monitor/toggle", methods=['POST'])(self.toggle_monitor)
        server.route("/monitor/output", methods=['GET'])(self.get_console_output)
        server.route("/monitor/download", methods=['GET'])(self.download_csv_file)
        server.route("/monitor/list_csv", methods=['GET'])(self.list_csv_files)
        server.route("/monitor/load", methods=['GET'])(self.load_console_log)
        server.route("/monitor/clear", methods=['POST'])(self.clear_console_log)

    def serve_monitor_page(self, request):
        module_html = f'<div class="module">{self.get_html_template()}</div>'
        full_page = self.foundation.templates.render_page("Monitor", module_html)
        return Response(request, full_page, content_type="text/html")

    def toggle_monitor(self, request):
        self.monitor_enabled = not self.monitor_enabled
        if self.monitor_enabled:
            status = "Monitor is ON"
            self.console_print("Monitoring started")
        else:
            status = "Monitor is OFF"
            self.console_buffer = []
        return Response(request, status, content_type="text/plain")

    def get_console_output(self, request):
        if self.console_buffer:
            output = "\n".join(self.console_buffer)
            self.console_buffer = []
            return Response(request, output, content_type="text/plain")
        else:
            return Response(request, "No new output", content_type="text/plain")

    def save_console_log(self, request):
        try:
            with open(self.log_file, "a") as f:
                for line in self.console_buffer:
                    f.write(line + "\n")
            self.console_buffer = []
            return Response(request, "Log saved", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error saving log: {e}", content_type="text/plain")

    def load_console_log(self, request):
        try:
            with open(self.log_file, "r") as f:
                log = f.read()
            return Response(request, log, content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error loading log: {e}", content_type="text/plain")

    def clear_console_log(self, request):
        try:
            with open(self.log_file, "w") as f:
                f.write("")
            return Response(request, "Log cleared", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error clearing log: {e}", content_type="text/plain")

    def console_print(self, message):
        print(f"[Monitor]: {message}")
        if self.monitor_enabled:
            self.console_buffer.append(message)
            if len(self.console_buffer) > self.buffer_size:
                self.console_buffer = self.console_buffer[-self.buffer_size//2:]

    def list_csv_files(self, request):
        # List all .csv files in the /sd directory only
        try:
            files = []
            if "sd" in os.listdir("/"):
                for fname in os.listdir("/sd"):
                    if fname.endswith(".csv"):
                        files.append(fname)  # Only the filename, no sd/ prefix
            return Response(request, ",".join(files), content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error listing CSV files: {e}", content_type="text/plain")

    def download_csv_file(self, request):
        try:
            query = request.query_params
            filename = query.get("file", None)
            if not filename:
                return Response(request, "No file specified.", content_type="text/plain")
            filename = url_unquote(filename)
            if not filename.endswith(".csv"):
                return Response(request, "Invalid file type.", content_type="text/plain")
            filepath = "/sd/" + filename  # Always use SD card
            download_name = filename
            with open(filepath, "r") as f:
                csv_data = f.read()
            headers = {
                "Content-Disposition": f'attachment; filename="{download_name}"'
            }
            return Response(request, csv_data, content_type="text/csv", headers=headers)
        except Exception as e:
            return Response(request, f"Error downloading CSV file: {e}", content_type="text/plain")

    def get_html_template(self):
        return """
        <h2>Files</h2>
        <button onclick="showCsvList()">List CSV Files</button>
        <div id="csv-list" style="margin-bottom: 20px; display:none;"></div>
        <button onclick="showDownloadCsvList()">Download CSV</button>
        <div id="download-csv-list" style="margin-bottom: 20px; display:none;"></div>
        <script>
        function fetchCsvFiles(callback) {
            fetch('/monitor/list_csv', { method: 'GET' })
                .then(response => response.text())
                .then(result => {
                    const files = result.split(',').map(f => f.trim()).filter(f => f !== "");
                    callback(files);
                });
        }
        function showCsvList() {
            fetchCsvFiles(function(files) {
                const csvListDiv = document.getElementById('csv-list');
                if (files.length === 0) {
                    csvListDiv.innerHTML = "<p>No CSV files found.</p>";
                } else {
                    let html = "<ul style='font-size:1.1em;'>";
                    files.forEach(function(fname) {
                        html += "<li>" + fname + "</li>";
                    });
                    html += "</ul>";
                    csvListDiv.innerHTML = html;
                }
                csvListDiv.style.display = 'block';
                document.getElementById('download-csv-list').style.display = 'none';
            });
        }
        function showDownloadCsvList() {
            fetchCsvFiles(function(files) {
                const downloadDiv = document.getElementById('download-csv-list');
                if (files.length === 0) {
                    downloadDiv.innerHTML = "<p>No CSV files found.</p>";
                } else {
                    let html = "<ul style='font-size:1.1em;'>";
                    files.forEach(function(fname) {
                        html += "<li><a href='/monitor/download?file=" + encodeURIComponent(fname) +
                                "' download style='text-decoration:none;'>" +
                                fname + " &#x1F4E5;</a></li>";
                    });
                    html += "</ul>";
                    downloadDiv.innerHTML = html;
                }
                downloadDiv.style.display = 'block';
                document.getElementById('csv-list').style.display = 'none';
            });
        }
        </script>
        """

    def get_dashboard_html(self):
        return f'<div class="module">{self.get_html_template()}</div>'