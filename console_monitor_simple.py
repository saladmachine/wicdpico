from adafruit_httpserver import Response
from module_base import PicowidModule

class ConsoleMonitorModule(PicowidModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Console Monitor"
        self.path = "/console"
        self.monitor_enabled = False
        self.console_buffer = []

    def get_routes(self):
        return [
            ("/console", self.console_page),
            ("/toggle-monitor", self.toggle_monitor),
            ("/get-console", self.get_console)
        ]

    def register_routes(self, server):
        """Register all module routes with the server"""
        for route, handler in self.get_routes():
            server.route(route, methods=['GET', 'POST'])(handler)

    def console_page(self, request):
        """Main console monitor page"""
        module_html = f'<div class="module">{self.get_html_template()}</div>'
        full_page = self.foundation.templates.render_page("Console Monitor", module_html)
        return Response(request, full_page, content_type="text/html")

    def toggle_monitor(self, request):
        """Toggle console monitoring on/off"""
        try:
            self.monitor_enabled = not self.monitor_enabled
            if self.monitor_enabled:
                status = "Monitor is ON"
                self.console_print("Console monitoring started")
            else:
                status = "Monitor is OFF"
                self.console_buffer = []
            return Response(request, status, content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {str(e)}", content_type="text/plain")

    def get_console(self, request):
        """Get console output"""
        try:
            if self.console_buffer:
                output = "\n".join(self.console_buffer)
                self.console_buffer = []
                return Response(request, output, content_type="text/plain")
            else:
                return Response(request, "No new output", content_type="text/plain")
        except Exception as e:
            return Response(request, f"Error: {str(e)}", content_type="text/plain")

    def console_print(self, message):
        """Add message to console buffer"""
        print(f"[Picowicd]: {message}")
        if self.monitor_enabled:
            self.console_buffer.append(message)
            if len(self.console_buffer) > 50:
                self.console_buffer = self.console_buffer[-25:]

    def get_html_template(self):
        return """
        <h2>Console Monitor</h2>
        <a href="/" style="text-decoration: none;"><button>Back to Dashboard</button></a>

        <p>Status: <span id="status">Monitor is OFF</span></p>

        <button id="toggle-btn" onclick="toggleMonitor()">Start Monitor</button>
        <button onclick="getConsole()">Get Output</button>

        <div id="console-area" style="display: none;">
            <h3>Console Output:</h3>
            <pre id="console-output" style="background: #f0f0f0; padding: 10px; height: 200px; overflow-y: auto;"></pre>
        </div>

        <script>
        function toggleMonitor() {
            fetch('/toggle-monitor', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    document.getElementById('status').textContent = result;
                    if (result.includes('ON')) {
                        document.getElementById('toggle-btn').textContent = 'Stop Monitor';
                        document.getElementById('console-area').style.display = 'block';
                    } else {
                        document.getElementById('toggle-btn').textContent = 'Start Monitor';
                        document.getElementById('console-area').style.display = 'none';
                    }
                });
        }

        function getConsole() {
            fetch('/get-console', { method: 'POST' })
                .then(response => response.text())
                .then(result => {
                    const output = document.getElementById('console-output');
                    if (result !== 'No new output') {
                        output.textContent += result + '\\n';
                        output.scrollTop = output.scrollHeight;
                    }
                });
        }
        </script>
        """

    def get_dashboard_html(self):
        """Return HTML for dashboard display"""
        return f'<a href="{self.path}" style="text-decoration: none;"><button style="width: 100%; margin: 5px 0;">Open {self.name}</button></a>'