# mqtt_no_auth_test.py - Test MQTT without authentication
import time
import wifi
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT

# Pi5 WCS Hub connection settings
WIFI_SSID = "joepardue"
WIFI_PASSWORD = "pudden789"
MQTT_BROKER = "192.168.99.1"
MQTT_PORT = 1883

print("=== MQTT TEST WITHOUT AUTHENTICATION ===")

# Connect to WiFi
print(f"Connecting to WiFi: {WIFI_SSID}")
wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
print(f"Connected! IP: {wifi.radio.ipv4_address}")

# Create socket pool
pool = socketpool.SocketPool(wifi.radio)

# Create MQTT client WITH proper credentials
mqtt_client = MQTT.MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    username="picowicd",      # Use the user we created
    password="picowicd123",   # Use the password we set
    socket_pool=pool,
    is_ssl=False
)

# Connect to MQTT broker
print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT} (picowicd user)")
try:
    mqtt_client.connect()
    print("✓ MQTT connection successful!")
    
    # Publish test message
    mqtt_client.publish("wcs/node01/test", "Hello no auth!")
    print("✓ Published test message!")
    
except Exception as e:
    print(f"MQTT Error: {e}")

print("=== NO AUTH TEST COMPLETE ===")