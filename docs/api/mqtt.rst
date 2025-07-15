MQTT Communication
==================

.. automodule:: mqtt_module
   :members:
   :undoc-members:
   :show-inheritance:

MQTT Module Class
----------------

.. autoclass:: mqtt_module.MQTTModule
   :members:

Topic Structure
--------------

The MQTT module publishes sensor data to the following topic hierarchy:

* ``wcs/{node_id}/temperature`` - Temperature readings in Celsius
* ``wcs/{node_id}/humidity`` - Humidity percentage  
* ``wcs/{node_id}/battery`` - Battery voltage
* ``wcs/{node_id}/status`` - JSON status with all data