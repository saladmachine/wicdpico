# module_terminal.py - Pure Web-to-UART Serial Gateway with Control Signals
# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

import busio
import board
from module_base import WicdpicoModule
from adafruit_httpserver import Request, Response
# Need to import sys for printing exception in code.py's handler, but not used here.
# Need to import time for the REPL to use.
import time 

# ASCII control codes
CTRL_C = b'\x03' # End of Text (ETX) - Used for Keyboard Interrupt
CTRL_D = b'\x04' # End of Transmission (EOT) - Used for Soft Reset

class TerminalModule(WicdpicoModule):
    """
    Web-based Serial Terminal (Pure UART Gateway).
    Communicates via UART on GP0 (TX) and GP1 (RX).
    """

    def __init__(self, foundation):
        super().__init__(foundation)
        self.name = "Web Terminal"
        self.version = "v1.0"
        self.max_buffer_size = 4096      
        self.serial_buffer = ""          
        self.rtc_available = False
        # Accesses the guaranteed-to-exist self.i2c from foundation (which may be None)
        self.i2c = foundation.i2c 

        # --- THE I/O SIDE-EFFECT FIX ---
        # Initialize an RTC or similar I2C device to trigger I/O redirection
        try:
            # Need to import adafruit_pcf8523 for the RTC side effect
            from adafruit_pcf8523.pcf8523 import PCF8523
            self.rtc = PCF8523(self.i2c)
            self.rtc_available = True
            foundation.startup_print("✓ I/O Fix: RTC initialized to enable console echo.")
        except Exception:
            self.rtc_available = False
            foundation.startup_print("✗ I/O Fix: RTC not available. Console echo may fail.")

        # UART Setup on GP0 (TX) and GP1 (RX)
        try:
            self.uart = busio.UART(board.GP0, board.GP1, baudrate=115200)
            self.available = True
            foundation.startup_print("✓ Terminal UART initialized on GP0/GP1.")
        except Exception as e:
            self.uart = None
            self.available = False
            foundation.startup_print("✗ Terminal UART unavailable: {}".format(e))

    def get_routes(self):
        return [
            ("/terminal-send", self.handle_send),
            ("/terminal-read", self.handle_read),
            ("/terminal-ctrl-c", self.handle_ctrl_c),
            ("/terminal-ctrl-d", self.handle_ctrl_d),
        ]

    def register_routes(self, server):
        for route, handler in self.get_routes():
            server.route(route, methods=["POST"])(handler)

    def handle_send(self, request: Request):
        if not self.available:
            return Response(request, "Error: Terminal not available.", content_type="text/plain")
        try:
            data_to_send = request.body.decode('utf-8')
            self.uart.write(data_to_send.encode('utf-8'))
            return Response(request, "Data sent to UART: {} bytes".format(len(data_to_send)), content_type="text/plain")
        except Exception as e:
            return Response(request, "Error sending data: {}".format(e), content_type="text/plain")

    def handle_ctrl_c(self, request: Request):
        if not self.available:
            return Response(request, "Error: Terminal not available.", content_type="text/plain")
        try:
            self.uart.write(CTRL_C)
            return Response(request, "Sent Ctrl-C (Interrupt)", content_type="text/plain")
        except Exception as e:
            return Response(request, "Error sending Ctrl-C: {}".format(e), content_type="text/plain")

    def handle_ctrl_d(self, request: Request):
        if not self.available:
            return Response(request, "Error: Terminal not available.", content_type="text/plain")
        try:
            self.uart.write(CTRL_D)
            return Response(request, "Sent Ctrl-D (Soft Reset)", content_type="text/plain")
        except Exception as e:
            return Response(request, "Error sending Ctrl-D: {}".format(e), content_type="text/plain")

    def handle_read(self, request: Request):
        data = self.serial_buffer
        self.serial_buffer = ""
        return Response(request, data, content_type="text/plain")

    def update(self):
        if not self.available:
            return
        try:
            if self.uart.in_waiting:
                data = self.uart.read(self.uart.in_waiting)
                if data:
                    new_data = data.decode('utf-8', errors='ignore')
                    self.serial_buffer += new_data
                    if len(self.serial_buffer) > self.max_buffer_size:
                        self.serial_buffer = self.serial_buffer[-self.max_buffer_size:]
        except Exception:
            pass

    def get_dashboard_html(self):
        return """
        <div class="module">
            <h2>Web Terminal (UART)</h2>
            <div style="margin-top: 10px;">
                <strong>Status:</strong> <span id="terminal-status">Polling...</span>
            </div>
            <textarea id="terminal-output" style="width: 100%; height: 200px; background: #222; color: #0f0; font-family: monospace; border: none; padding: 10px; margin-top: 8px;" readonly></textarea>
            
            <div class="control-group" style="margin-top: 10px;">
                <input type="text" id="terminal-input" 
                       placeholder="Type data to send via UART" 
                       inputmode="text" 
                       autocorrect="off" 
                       autocapitalize="none"
                       style="width: 100%; padding: 12px; border: 2px solid #007bff; border-radius: 5px; min-height: 48px; box-shadow: 0 0 5px rgba(0, 123, 255, 0.5); font-size: 1.1em;">

                <button id="terminal-send-btn" onclick="sendTerminalData()">Send Command/Data</button>
            </div>
            
            <div class="control-group" style="margin-top: 15px; display: flex; justify-content: space-between;">
                <button id="ctrl-c-btn" onclick="sendCtrlC()" style="width: 48%; background: #dc3545;">Send Ctrl-C</button>
                <button id="ctrl-d-btn" onclick="sendCtrlD()" style="width: 48%; background: #ffc107; color: #333;">Send Ctrl-D</button>
            </div>
        </div>
        <script>
        const outputEl = document.getElementById('terminal-output');
        const inputEl = document.getElementById('terminal-input');
        const statusEl = document.getElementById('terminal-status');
        let pollingInterval = 500; // ms

        document.addEventListener('DOMContentLoaded', function() {
            inputEl.focus(); 
        });

        function pollTerminalRead() {
            fetch('/terminal-read', {method:'POST'})
                .then(response => response.text())
                .then(data => {
                    if (data && data.length > 0) {
                        outputEl.value += data;
                        outputEl.scrollTop = outputEl.scrollHeight;
                        statusEl.textContent = 'Active (Recv)';
                    } else {
                        statusEl.textContent = 'Active (Idle)';
                    }
                })
                .catch(error => {
                    statusEl.textContent = 'Error: Failed to poll.';
                    console.error('Terminal poll error:', error);
                });
        }
        
        function sendTerminalData() {
            const btn = document.getElementById('terminal-send-btn');
            const data = inputEl.value;
            if (!data) return;

            btn.disabled = true;
            statusEl.textContent = 'Sending...';

            fetch('/terminal-send', {
                method: 'POST',
                body: data,
                headers: { 'Content-Type': 'text/plain' }
            })
            .then(response => response.text())
            .then(message => {
                outputEl.value += '> ' + data + '\\n';
                outputEl.scrollTop = outputEl.scrollHeight;
                inputEl.value = '';
                statusEl.textContent = 'Sent.';
                inputEl.focus(); 
            })
            .catch(error => {
                statusEl.textContent = 'Error: Failed to send.';
                console.error('Terminal send error:', error);
            })
            .finally(() => {
                btn.disabled = false;
            });
        }
        
        function sendCtrlC() {
            const btn = document.getElementById('ctrl-c-btn');
            btn.disabled = true;
            statusEl.textContent = 'Sending Ctrl-C...';
            fetch('/terminal-ctrl-c', { method: 'POST' })
                .then(response => response.text())
                .then(message => {
                    outputEl.value += '[SENT: Ctrl-C] ' + message + '\\n';
                    outputEl.scrollTop = outputEl.scrollHeight;
                    statusEl.textContent = 'Ctrl-C Sent.';
                })
                .finally(() => {
                    btn.disabled = false;
                    inputEl.focus(); 
                });
        }

        function sendCtrlD() {
            const btn = document.getElementById('ctrl-d-btn');
            btn.disabled = true;
            statusEl.textContent = 'Sending Ctrl-D...';
            fetch('/terminal-ctrl-d', { method: 'POST' })
                .then(response => response.text())
                .then(message => {
                    outputEl.value += '[SENT: Ctrl-D] ' + message + '\\n';
                    outputEl.scrollTop = outputEl.scrollHeight;
                    statusEl.textContent = 'Ctrl-D Sent.';
                })
                .finally(() => {
                    btn.disabled = false;
                    inputEl.focus(); 
                });
        }

        inputEl.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault(); 
                sendTerminalData();
            }
        });

        setInterval(pollTerminalRead, pollingInterval);
        </script>
        """

    def cleanup(self):
        if self.uart:
            self.uart.deinit()