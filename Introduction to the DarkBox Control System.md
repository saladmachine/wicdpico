# Introduction to the DarkBox Control System

## Overview

The **DarkBox Control System** is a modular sensor and automation platform built for the Raspberry Pi Pico W using CircuitPython.  
It is designed to monitor environmental conditions and light events in a controlled chamber, providing real-time data logging and remote control via a built-in WiFi hotspot and web dashboard.

### Key Features

- **CO2, Temperature, and Humidity Monitoring:**  
  Uses the SCD41 sensor for accurate environmental readings.
- **Light Event Detection:**  
  Tracks illumination changes using the BH1750 sensor.
- **Power Source Monitoring:**  
  Detects and logs transitions between USB and battery power.
- **Data Logging:**  
  Records sensor readings and events to an SD card for later analysis.
- **Web-Based Control Panel:**  
  Access and control the system from any device connected to the Pico’s WiFi hotspot.

---

## Getting Started

1. **Power Up the System:**  
   Connect the Pico W to USB or battery power. The device will start its WiFi hotspot (default SSID: `PicoTest-Node00`).

2. **Connect to the WiFi Hotspot:**  
   On your computer or mobile device, connect to the Pico’s WiFi network.

3. **Access the Web Dashboard:**  
   Open a browser and go to [http://192.168.4.1](http://192.168.4.1).  
   You will see the DarkBox virtual control panel.

---

## Using the Virtual Control Panel

The web dashboard is organized into interactive modules, each representing a key function of the DarkBox system:

### **Environment Sensor Module**

- **CO2, Temperature, Humidity Display:**  
  Shows live readings from the SCD41 sensor.
- **Get Reading Button:**  
  Click to trigger a new measurement. The latest values will update automatically.
- **Calibration Button:**  
  Opens the calibration page for CO2 sensor adjustment.
- **Log to SD Button:**  
  Saves the current environmental readings to the SD card.
- **Read Log File Button:**  
  Displays the contents of the environment log file.

### **Light Status Module**

- **Light Level Display:**  
  Shows the current lux value from the BH1750 sensor.
- **Update Status Button:**  
  Refreshes the light reading.
- **Read Light Log Button:**  
  Shows a history of detected light events.
- **Clear Light Events Button:**  
  Clears the recorded light event history.

### **Power Monitoring Module**

- **Get Voltage Button:**  
  Displays the current system voltage (VSYS).
- **Get Power Source Button:**  
  Shows whether the system is running on USB or battery power.
- **View Log Button:**  
  Displays a log of all power events (power-ups and transitions between USB and battery).

---

## Data Logging and Event History

- All sensor readings and events are timestamped and saved to the SD card.
- You can view logs directly from the dashboard or download them for offline analysis.

---

## Best Practices

- Use the control panel buttons to manually trigger readings and log events as needed.
- Regularly check the power source and voltage to ensure reliable operation.
- Clear event logs periodically to maintain organized records.

---

## Support and Troubleshooting

- If the dashboard does not load, ensure your device is connected to the Pico’s WiFi hotspot.
- For SD card issues, verify the card is properly inserted and formatted.
- Consult the project documentation for advanced configuration and module details.

---

**The DarkBox Control System makes environmental monitoring and automation simple, reliable, and accessible from any web-enabled device.**