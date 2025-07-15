.. picowicd documentation master file

===================================
picowicd: Wireless Sensor Networks
===================================

**picowicd** is a modular CircuitPython framework for building low-cost wireless sensor networks using Raspberry Pi Pico 2 W microcontrollers. Designed for research applications in precision agriculture and controlled environment agriculture (CEA).

.. image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

.. image:: https://readthedocs.org/projects/picowicd/badge/?version=latest
   :target: https://picowicd.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

🎯 **Key Features**
==================

* **Low-Cost Architecture**: Order-of-magnitude savings vs commercial systems
* **Modular Design**: Plug-and-play sensor integration
* **Wireless Communication**: WiFi + MQTT for reliable data transmission
* **Academic Ready**: Professional documentation and reproducible designs
* **Open Source**: Complete transparency and community contributions

🔧 **System Components**
=======================

**Hardware Infrastructure**
   * Pi5 WCS Hub (Raspberry Pi 5 + Home Assistant + Mosquitto MQTT)
   * Multi-node Pico 2 W sensor networks
   * Modular sensor integration (RTC, SD card, battery monitoring)

**Software Framework**
   * Robust CircuitPython foundation with WiFi/AP modes
   * MQTT communication with auto-reconnect
   * Web-based dashboard for monitoring and control
   * Comprehensive error handling and logging

📚 **Documentation Sections**
=============================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   hardware_setup
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   configuration
   sensor_integration
   mqtt_setup
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/foundation
   api/mqtt
   api/sensors
   api/utilities

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic_sensor
   examples/multi_node
   examples/data_logging

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog
   license

🚀 **Quick Start**
=================

1. **Install CircuitPython** on your Pico 2 W
2. **Copy picowicd files** to CIRCUITPY drive
3. **Configure WiFi settings** in settings.toml
4. **Access web dashboard** at device IP address

.. code-block:: python

   # Basic sensor node setup
   from foundation_core import PicowicdFoundation
   from mqtt_module import MQTTModule
   
   # Initialize system
   foundation = PicowicdFoundation()
   foundation.initialize_network()
   
   # Add MQTT functionality
   mqtt = MQTTModule(foundation)
   foundation.register_module("mqtt", mqtt)
   
   # Start system
   foundation.start_server()
   foundation.run_main_loop()

📊 **Academic Impact**
=====================

picowicd democratizes access to precision agriculture research tools by providing:

* **Cost Reduction**: Sub-$50 sensor nodes vs $500+ commercial alternatives
* **Open Design**: Fully reproducible hardware and software
* **Research Ready**: Professional documentation and validation data
* **Scalable**: Proven architecture for 5-10+ node deployments

🤝 **Contributing**
==================

We welcome contributions! See our `Contributing Guide <contributing.html>`_ for details.

📄 **License**
=============

This project is licensed under the MIT License - see the `LICENSE <license.html>`_ file for details.

.. note::
   
   This documentation is built with `Sphinx <https://www.sphinx-doc.org/>`_ and hosted on 
   `Read the Docs <https://readthedocs.org/>`_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`