"""
MQTT Module - Step 2: MQTT Configuration and Connection
Part of picowicd modular system for academic WCS Hub demonstration
"""
import time
import os
import wifi
import socketpool
import ssl
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from module_base import PicowicdModule
from adafruit_httpserver import Request, Response

class MQTTModule(PicowicdModule):
    def __init__(self, foundation):
        super().__init__(foundation)
        
        # Module identification
        self.name = "MQTT Client"
        
        # Load MQTT configuration
        self._load_mqtt_config()
        
        # MQTT state tracking
        self.mqtt_client = None
        self.connected = False
        self.last_publish = 0
        self.connection_attempts = 0
        
        # Status tracking for dashboard
        self.status_message = "MQTT module initialized"
        self.last_error = None
        
        # Initialize MQTT client
        self._setup_mqtt_client()
        
        self.foundation.startup_print(f"MQTT module created for node: {self.node_id}")
        self.foundation.startup_print(f"MQTT broker: {self.broker_host}:{self.broker_port}")
    
    def _load_mqtt_config(self):
        """Load MQTT configuration from settings.toml"""
        try:
            # MQTT broker settings
            self.broker_host = os.getenv("MQTT_BROKER", "192.168.99.1")
            self.broker_port = int(os.getenv("MQTT_PORT", "1883"))
            self.node_id = os.getenv("MQTT_NODE_ID", "node01")
            self.publish_interval = int(os.getenv("MQTT_PUBLISH_INTERVAL", "60"))
            self.keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
            
            # Topic configuration
            topic_base = os.getenv("MQTT_TOPIC_BASE", "wcs")
            self.topic_temperature = f"{topic_base}/{self.node_id}/temperature"
            self.topic_humidity = f"{topic_base}/{self.node_id}/humidity"
            self.topic_battery = f"{topic_base}/{self.node_id}/battery"
            self.topic_status = f"{topic_base}/{self.node_id}/status"
            
            self.foundation.startup_print("MQTT config loaded from settings.toml")
            
        except Exception as e:
            self.foundation.startup_print(f"MQTT config error: {e}")
            # Use defaults
            self.broker_host = "192.168.99.1"
            self.broker_port = 1883
            self.node_id = "node01"
            self.publish_interval = 60
            self.keepalive = 60
            self.topic_temperature = f"wcs/{self.node_id}/temperature"
            self.topic_humidity = f"wcs/{self.node_id}/humidity"
            self.topic_battery = f"wcs/{self.node_id}/battery"
            self.topic_status = f"wcs/{self.node_id}/status"
    
    def _setup_mqtt_client(self):
        """Initialize MQTT client with callbacks"""
        try:
            # Create socket pool
            pool = socketpool.SocketPool(wifi.radio)
            
            # Create MQTT client
            self.mqtt_client = MQTT.MQTT(
                broker=self.broker_host,
                port=self.broker_port,
                socket_pool=pool,
                keep_alive=self.keepalive,
                is_ssl=False  # No SSL for local broker
            )
            
            # Set up callbacks
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_disconnect = self._on_disconnect
            self.mqtt_client.on_message = self._on_message
            
            self.status_message = "MQTT client configured"
            
        except Exception as e:
            self.last_error = f"MQTT setup failed: {e}"
            self.status_message = self.last_error
            self.foundation.startup_print(self.last_error)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful MQTT connection"""
        self.connected = True
        self.connection_attempts += 1
        self.status_message = f"Connected to {self.broker_host}"
        self.last_error = None
        self.foundation.startup_print(f"MQTT connected: {self.status_message}")
        
        # Publish online status
        try:
            self.mqtt_client.publish(self.topic_status, "online")
        except Exception as e:
            self.foundation.startup_print(f"Status publish failed: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        self.status_message = f"Disconnected (code: {rc})"
        self.foundation.startup_print(f"MQTT disconnected: {self.status_message}")
    
    def _on_message(self, client, topic, message):
        """Callback for received MQTT messages (for future use)"""
        self.foundation.startup_print(f"MQTT message: {topic} = {message}")
    
    def connect_mqtt(self):
        """Attempt MQTT connection"""
        if self.connected:
            return True, "Already connected"
        
        if not self.mqtt_client:
            return False, "MQTT client not initialized"
        
        try:
            self.status_message = "Connecting..."
            self.foundation.startup_print(f"Connecting to MQTT broker {self.broker_host}:{self.broker_port}")
            
            self.mqtt_client.connect()
            return True, "Connection initiated"
            
        except Exception as e:
            self.last_error = f"Connection failed: {e}"
            self.status_message = self.last_error
            self.foundation.startup_print(self.last_error)
            return False, str(e)
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT broker"""
        if not self.connected:
            return True, "Not connected"
        
        try:
            # Publish offline status before disconnecting
            self.mqtt_client.publish(self.topic_status, "offline")
            self.mqtt_client.disconnect()
            return True, "Disconnected"
            
        except Exception as e:
            self.last_error = f"Disconnect failed: {e}"
            self.foundation.startup_print(self.last_error)
            return False, str(e)
    
    def get_sensor_data(self):
        """Get sensor readings - mock data for now, easy to replace with real sensors"""
        import time
        import random
        
        # Mock sensor data - replace this section with real sensor readings
        current_time = time.monotonic()
        
        # Simulate realistic environmental data with some variation
        base_temp = 22.0  # Base temperature in Celsius
        base_humidity = 65.0  # Base humidity percentage
        
        # Add some realistic variation
        temp_variation = 2.0 * (0.5 - random.random())  # ±1°C variation
        humidity_variation = 5.0 * (0.5 - random.random())  # ±2.5% variation
        
        sensor_data = {
            "temperature": round(base_temp + temp_variation, 2),
            "humidity": round(base_humidity + humidity_variation, 1),
            "battery_voltage": round(3.7 + 0.3 * random.random(), 2),  # 3.7-4.0V
            "timestamp": int(current_time),
            "node_id": self.node_id
        }
        
        return sensor_data
    
    def publish_sensor_data(self):
        """Publish sensor data to MQTT broker"""
        if not self.connected or not self.mqtt_client:
            self.last_error = "Not connected to MQTT broker"
            return False
        
        try:
            # Get sensor readings
            sensor_data = self.get_sensor_data()
            
            # Publish individual sensor values
            self.mqtt_client.publish(self.topic_temperature, str(sensor_data["temperature"]))
            self.mqtt_client.publish(self.topic_humidity, str(sensor_data["humidity"]))
            self.mqtt_client.publish(self.topic_battery, str(sensor_data["battery_voltage"]))
            
            # Publish complete JSON data to status topic
            import json
            status_data = {
                "status": "online",
                "timestamp": sensor_data["timestamp"],
                "data": sensor_data
            }
            self.mqtt_client.publish(self.topic_status, json.dumps(status_data))
            
            # Update status
            self.status_message = f"Published: T={sensor_data['temperature']}°C, H={sensor_data['humidity']}%"
            self.last_publish = time.monotonic()
            
            self.foundation.startup_print(f"MQTT published: {self.status_message}")
            return True
            
        except Exception as e:
            self.last_error = f"Publish failed: {e}"
            self.foundation.startup_print(self.last_error)
            return False
        
    def register_routes(self, server):
        """Register MQTT control web endpoints"""
        
        @server.route("/mqtt-connect", methods=['POST'])
        def mqtt_connect(request: Request):
            """Manual MQTT connection trigger"""
            try:
                success, message = self.connect_mqtt()
                return Response(request, message, content_type="text/plain")
            except Exception as e:
                self.last_error = str(e)
                return Response(request, f"Error: {str(e)}", content_type="text/plain")
        
        @server.route("/mqtt-disconnect", methods=['POST'])
        def mqtt_disconnect(request: Request):
            """Manual MQTT disconnection"""
            try:
                success, message = self.disconnect_mqtt()
                return Response(request, message, content_type="text/plain")
            except Exception as e:
                self.last_error = str(e)
                return Response(request, f"Error: {str(e)}", content_type="text/plain")
        
        @server.route("/mqtt-publish", methods=['POST'])
        def mqtt_publish_manual(request: Request):
            """Manual publish trigger for testing"""
            try:
                if not self.connected:
                    return Response(request, "Not connected", content_type="text/plain")
                
                # Publish test sensor data
                success = self.publish_sensor_data()
                if success:
                    return Response(request, "Test data published", content_type="text/plain")
                else:
                    return Response(request, f"Publish failed: {self.last_error}", content_type="text/plain")
                    
            except Exception as e:
                self.last_error = str(e)
                return Response(request, f"Error: {str(e)}", content_type="text/plain")
    
    def get_dashboard_html(self):
        """Return HTML for MQTT control interface"""
        connection_status = "Connected" if self.connected else "Disconnected"
        connection_color = "#28a745" if self.connected else "#dc3545"
        
        return f'''
        <div class="module">
            <h3>MQTT Client - {self.node_id}</h3>
            
            <div class="status" style="border-left: 4px solid {connection_color};">
                <strong>Status:</strong> {connection_status}<br>
                <strong>Message:</strong> {self.status_message}<br>
                <strong>Attempts:</strong> {self.connection_attempts}<br>
                <strong>Last Published:</strong> {self._format_last_publish()}
            </div>
            
            <div class="control-group">
                <button id="mqtt-connect-btn" onclick="mqttConnect()">Connect</button>
                <button id="mqtt-disconnect-btn" onclick="mqttDisconnect()">Disconnect</button>
                <button id="mqtt-publish-btn" onclick="mqttPublish()">Test Publish</button>
            </div>
            
            <div id="mqtt-status" class="status">
                Ready for MQTT operations
            </div>
            
            {self._get_error_display()}
        </div>

        <script>
        function mqttConnect() {{
            setButtonLoading('mqtt-connect-btn', true);
            serverRequest('/mqtt-connect')
                .then(result => {{
                    updateElement('mqtt-status', 'Status: ' + result);
                    setTimeout(() => location.reload(), 1000); // Refresh to show new status
                }})
                .catch(error => {{
                    updateElement('mqtt-status', 'Error: ' + error.message);
                }})
                .finally(() => {{
                    setButtonLoading('mqtt-connect-btn', false);
                }});
        }}

        function mqttDisconnect() {{
            setButtonLoading('mqtt-disconnect-btn', true);
            serverRequest('/mqtt-disconnect')
                .then(result => {{
                    updateElement('mqtt-status', 'Status: ' + result);
                    setTimeout(() => location.reload(), 1000); // Refresh to show new status
                }})
                .catch(error => {{
                    updateElement('mqtt-status', 'Error: ' + error.message);
                }})
                .finally(() => {{
                    setButtonLoading('mqtt-disconnect-btn', false);
                }});
        }}

        function mqttPublish() {{
            setButtonLoading('mqtt-publish-btn', true);
            serverRequest('/mqtt-publish')
                .then(result => {{
                    updateElement('mqtt-status', 'Publish: ' + result);
                }})
                .catch(error => {{
                    updateElement('mqtt-status', 'Error: ' + error.message);
                }})
                .finally(() => {{
                    setButtonLoading('mqtt-publish-btn', false);
                }});
        }}
        </script>
        '''
    
    def _get_error_display(self):
        """Helper to show last error if any"""
        if self.last_error:
            return f'''
            <div class="status" style="border-left: 4px solid #dc3545;">
                <strong>Last Error:</strong> {self.last_error}
            </div>
            '''
        return ""
    
    def _format_last_publish(self):
        """Helper to format last publish time"""
        if self.last_publish == 0:
            return "Never"
        
        import time
        current_time = time.monotonic()
        seconds_ago = int(current_time - self.last_publish)
        
        if seconds_ago < 60:
            return f"{seconds_ago}s ago"
        elif seconds_ago < 3600:
            return f"{seconds_ago // 60}m ago"
        else:
            return f"{seconds_ago // 3600}h ago"
    
    def update(self):
        """Called from main loop - handle MQTT operations"""
        current_time = time.monotonic()
        
        # Handle MQTT client loop (process callbacks)
        if self.mqtt_client:
            try:
                self.mqtt_client.loop()  # Process MQTT callbacks
            except Exception as e:
                if self.connected:  # Only log if we were connected
                    self.foundation.startup_print(f"MQTT loop error: {e}")
                    self.connected = False
                    self.last_error = f"Connection lost: {e}"
        
        # Auto-reconnect logic
        if not self.connected and self.mqtt_client:
            # Try to reconnect every 30 seconds
            if hasattr(self, '_last_reconnect_attempt'):
                if current_time - self._last_reconnect_attempt > 30:
                    self._attempt_reconnect()
            else:
                self._last_reconnect_attempt = current_time
        
        # Automatic publishing when connected
        if self.connected and (current_time - self.last_publish >= self.publish_interval):
            self.foundation.startup_print("Auto-publishing sensor data...")
            self.publish_sensor_data()
    
    def _attempt_reconnect(self):
        """Attempt automatic reconnection"""
        self._last_reconnect_attempt = time.monotonic()
        self.foundation.startup_print("Attempting MQTT reconnection...")
        success, message = self.connect_mqtt()
        if not success:
            self.status_message = f"Reconnect failed: {message}"
    
    def cleanup(self):
        """Shutdown MQTT connections cleanly"""
        if self.connected and self.mqtt_client:
            try:
                self.foundation.startup_print("MQTT cleanup: Publishing offline status")
                self.mqtt_client.publish(self.topic_status, "offline")
                self.mqtt_client.disconnect()
                self.connected = False
            except Exception as e:
                self.foundation.startup_print(f"MQTT cleanup error: {e}")