"""
MQTT Module - MQTT Configuration and Connection for Wireless Sensor Networks
============================================================================

Provides robust MQTT communication for sensor data transmission to central hub 
systems. Features automatic reconnection, configurable topics, and comprehensive 
error handling for reliable wireless sensor network operation.

Hardware Requirements
--------------------
* Raspberry Pi Pico 2 W microcontroller
* WiFi connectivity (managed by foundation)
* MQTT broker accessibility (typically Pi5 WCS Hub)

Software Dependencies
--------------------
* adafruit_minimqtt.adafruit_minimqtt
* wifi (built-in CircuitPython)
* socketpool (built-in CircuitPython)
* ssl (built-in CircuitPython)

MQTT Topics Structure
--------------------
The module publishes sensor data to a hierarchical topic structure:

* ``wcs/{node_id}/temperature`` - Temperature readings (°C)
* ``wcs/{node_id}/humidity`` - Humidity readings (%)
* ``wcs/{node_id}/battery`` - Battery voltage (V)
* ``wcs/{node_id}/status`` - Node status and JSON data

Configuration (settings.toml)
----------------------------
.. code-block:: toml

    MQTT_BROKER = "192.168.99.1"
    MQTT_PORT = "1883"
    MQTT_USERNAME = "picowicd"
    MQTT_PASSWORD = "picowicd123"
    MQTT_NODE_ID = "node01"
    MQTT_PUBLISH_INTERVAL = "30"
    MQTT_TOPIC_BASE = "wcs"

Basic Usage Example
------------------
.. code-block:: python

    # Initialize MQTT module
    foundation = PicowicdFoundation()
    mqtt = MQTTModule(foundation)
    
    # Connect and publish data
    success, message = mqtt.connect_mqtt()
    if success:
        mqtt.publish_sensor_data()

Integration Example
------------------
.. code-block:: python

    # Complete sensor node setup
    foundation = PicowicdFoundation()
    foundation.initialize_network()
    
    # Add MQTT functionality  
    mqtt = MQTTModule(foundation)
    foundation.register_module("mqtt", mqtt)
    
    # Start system with automatic publishing
    foundation.start_server()
    foundation.run_main_loop()  # Handles auto-publish via update()
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
    """
    MQTT Client Module for Wireless Sensor Networks.
    
    Provides robust MQTT communication for sensor data transmission to
    central hub systems. Features automatic reconnection, configurable
    topics, and comprehensive error handling.
    
    :param foundation: PicoWicd foundation instance for system integration
    :type foundation: PicowicdFoundation
    
    **Basic Usage:**
    
    .. code-block:: python
    
        # Initialize MQTT module
        foundation = PicowicdFoundation()
        mqtt = MQTTModule(foundation)
        
        # Connect and publish data
        success, message = mqtt.connect_mqtt()
        if success:
            mqtt.publish_sensor_data()
    
    **Integration Example:**
    
    .. code-block:: python
    
        # Complete sensor node setup
        foundation = PicowicdFoundation()
        foundation.initialize_network()
        
        # Add MQTT functionality  
        mqtt = MQTTModule(foundation)
        foundation.register_module("mqtt", mqtt)
        
        # Start system with automatic publishing
        foundation.start_server()
        foundation.run_main_loop()  # Handles auto-publish via update()
    """
    
    def __init__(self, foundation):
        """
        Initialize MQTT module with foundation integration.
        
        Sets up MQTT client configuration, loads settings from foundation
        configuration system, and prepares callback handlers.
        
        :param foundation: Foundation instance for system integration
        :type foundation: PicowicdFoundation
        """
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
        """
        Load MQTT configuration from settings.toml with fallback defaults.
        
        Reads MQTT broker settings from environment variables (settings.toml)
        and provides robust fallback values if configuration is incomplete.
        """
        try:
            # MQTT broker settings
            self.broker_host = os.getenv("MQTT_BROKER", "192.168.99.1")
            self.broker_port = int(os.getenv("MQTT_PORT", "1883"))
            self.username = os.getenv("MQTT_USERNAME", None)
            self.password = os.getenv("MQTT_PASSWORD", None)
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
            self.username = None
            self.password = None
            self.node_id = "node01"
            self.publish_interval = 60
            self.keepalive = 60
            self.topic_temperature = f"wcs/{self.node_id}/temperature"
            self.topic_humidity = f"wcs/{self.node_id}/humidity"
            self.topic_battery = f"wcs/{self.node_id}/battery"
            self.topic_status = f"wcs/{self.node_id}/status"
    
    def _setup_mqtt_client(self):
        """
        Initialize MQTT client with callbacks and connection parameters.
        
        Creates MQTT client instance with proper socket pool, keepalive
        settings, authentication, and callback function assignments.
        """
        try:
            # Create socket pool
            pool = socketpool.SocketPool(wifi.radio)
            
            # Create MQTT client with authentication
            self.mqtt_client = MQTT.MQTT(
                broker=self.broker_host,
                port=self.broker_port,
                username=self.username,
                password=self.password,
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
        """
        Callback for successful MQTT connection.
        
        Updates connection status and publishes initial online status
        to the status topic.
        
        :param client: MQTT client instance
        :param userdata: User data (unused)
        :param flags: Connection flags
        :param rc: Return code
        """
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
        """
        Callback for MQTT disconnection.
        
        Updates connection status and logs disconnection reason.
        
        :param client: MQTT client instance
        :param userdata: User data (unused)
        :param rc: Return code indicating disconnection reason
        """
        self.connected = False
        self.status_message = f"Disconnected (code: {rc})"
        self.foundation.startup_print(f"MQTT disconnected: {self.status_message}")
    
    def _on_message(self, client, topic, message):
        """
        Callback for received MQTT messages (for future use).
        
        Handles incoming MQTT messages. Currently logs messages for
        debugging; can be extended for remote control functionality.
        
        :param client: MQTT client instance
        :param topic: Message topic
        :type topic: str
        :param message: Message payload
        :type message: str
        """
        self.foundation.startup_print(f"MQTT message: {topic} = {message}")
    
    def connect_mqtt(self):
        """
        Establish connection to MQTT broker.
        
        Attempts connection using configured broker settings with
        comprehensive error handling and status reporting.
        
        :return: Tuple of (success_flag, status_message)
        :rtype: tuple[bool, str]
        :raises ConnectionError: If broker unreachable
        
        .. code-block:: python
        
            success, msg = mqtt.connect_mqtt()
            if success:
                print(f"Connected: {msg}")
            else:
                print(f"Failed: {msg}")
        """
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
        """
        Disconnect from MQTT broker with graceful shutdown.
        
        Publishes offline status before disconnecting to notify
        the hub of intentional shutdown.
        
        :return: Tuple of (success_flag, status_message)
        :rtype: tuple[bool, str]
        """
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
        """
        Get sensor readings from real SHT45 hardware or fallback to mock data.
        
        Attempts to get actual sensor readings from registered SHT45 module.
        Falls back to mock data if SHT45 module is not available or fails.
        
        :return: Dictionary containing sensor readings
        :rtype: dict
        
        **Data Structure:**
        
        * temperature: Temperature in Celsius
        * humidity: Humidity percentage  
        * battery_voltage: Battery voltage (simulated)
        * timestamp: Unix timestamp
        * node_id: Node identifier
        
        .. code-block:: python
        
            # Get current sensor readings
            data = mqtt.get_sensor_data()
            print(f"Temperature: {data['temperature']}°C")
        """
        import time
        import random
        
        current_time = time.monotonic()
        
        # Try to get real sensor data from SHT45 module
        try:
            sht45_module = self.foundation.get_module("sht45")
            if sht45_module and sht45_module.sensor_available:
                reading = sht45_module.get_sensor_reading()
                
                if reading['success']:
                    # Use real SHT45 data
                    sensor_data = {
                        "temperature": reading['temperature'],
                        "humidity": reading['humidity'],
                        "battery_voltage": round(3.7 + 0.3 * random.random(), 2),  # Still simulated
                        "timestamp": int(current_time),
                        "node_id": self.node_id
                    }
                    return sensor_data
                    
        except Exception as e:
            self.foundation.startup_print(f"MQTT: Failed to get SHT45 data: {e}")
        
        # Fallback to mock data if SHT45 not available
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
        """
        Publish current sensor readings to MQTT broker.
        
        Gathers sensor data and publishes to configured topics.
        Currently uses mock data that can be easily replaced with
        real sensor readings.
        
        :return: True if publish successful, False otherwise
        :rtype: bool
        :raises PublishError: If MQTT publish fails
        
        **Published Topics:**
        
        * Temperature (°C) to temperature topic
        * Humidity (%) to humidity topic
        * Battery voltage (V) to battery topic
        * Complete JSON status to status topic
        
        .. code-block:: python
        
            # Manual publish trigger
            if mqtt.connected:
                success = mqtt.publish_sensor_data()
                print(f"Publish: {'OK' if success else 'Failed'}")
        """
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
        """
        Register MQTT control web endpoints.
        
        Adds HTTP routes for manual MQTT control via web interface.
        Provides endpoints for connection, disconnection, and test publishing.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        """
        
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
        """
        Return HTML for MQTT control interface.
        
        Generates interactive web dashboard widget for MQTT status
        monitoring and manual control operations.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
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
                    updateElement('mqtt-status', 'Status: ' + result);
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
        """
        Helper to show last error if any.
        
        :return: HTML error display or empty string
        :rtype: str
        """
        if self.last_error:
            return f'''
            <div class="status" style="border-left: 4px solid #dc3545;">
                <strong>Last Error:</strong> {self.last_error}
            </div>
            '''
        return ""
    
    def _format_last_publish(self):
        """
        Helper to format last publish time.
        
        :return: Human-readable time since last publish
        :rtype: str
        """
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
        """
        Called from main loop - handle MQTT operations.
        
        Performs periodic MQTT maintenance including connection monitoring,
        automatic reconnection, and scheduled sensor data publishing.
        Called continuously by the foundation main loop.
        """
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
        """
        Attempt automatic reconnection.
        
        Internal method for handling automatic MQTT reconnection
        when connection is lost.
        """
        self._last_reconnect_attempt = time.monotonic()
        self.foundation.startup_print("Attempting MQTT reconnection...")
        success, message = self.connect_mqtt()
        if not success:
            self.status_message = f"Reconnect failed: {message}"
    
    def cleanup(self):
        """
        Shutdown MQTT connections cleanly.
        
        Performs graceful shutdown by publishing offline status
        and disconnecting from MQTT broker. Called during system shutdown.
        """
        if self.connected and self.mqtt_client:
            try:
                self.foundation.startup_print("MQTT cleanup: Publishing offline status")
                self.mqtt_client.publish(self.topic_status, "offline")
                self.mqtt_client.disconnect()
                self.connected = False
            except Exception as e:
                self.foundation.startup_print(f"MQTT cleanup error: {e}")