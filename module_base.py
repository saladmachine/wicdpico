"""
Module Base - Foundation for PicoWicd Module System
===================================================

Provides the base class and interface definition for all picowicd modules.
Establishes the standard pattern for module integration, web interface
generation, and lifecycle management within the picowicd framework.

Module Architecture
------------------
All picowicd modules inherit from PicowicdModule and implement:

* **Web Integration**: HTTP route registration for web interface
* **Dashboard Generation**: HTML widget creation for unified dashboard
* **Lifecycle Management**: Update and cleanup methods for system integration
* **Foundation Access**: Direct access to core system services

Usage Pattern
------------
.. code-block:: python

    # Create custom module
    class MyModule(PicowicdModule):
        def __init__(self, foundation):
            super().__init__(foundation)
            self.name = "My Custom Module"
        
        def register_routes(self, server):
            @server.route("/my-endpoint", methods=['POST'])
            def my_handler(request):
                return Response(request, "Success")
        
        def get_dashboard_html(self):
            return "<button onclick='myFunction()'>My Button</button>"
        
        def update(self):
            # Called from main loop
            pass

Integration Example
------------------
.. code-block:: python

    # Register module with foundation
    foundation = PicowicdFoundation()
    my_module = MyModule(foundation)
    foundation.register_module("custom", my_module)
"""

class PicowicdModule:
    """
    Base class for all picowicd modules.
    
    Provides the standard interface and integration pattern for modules
    within the picowicd system. All modules should inherit from this class
    and implement the required methods for proper system integration.
    
    :param foundation: PicoWicd foundation instance for system integration
    :type foundation: PicowicdFoundation
    
    **Required Implementations:**
    
    Subclasses should override these methods as needed:
    
    * ``register_routes()`` - Add web endpoints
    * ``get_dashboard_html()`` - Generate dashboard widget  
    * ``update()`` - Handle periodic tasks
    * ``cleanup()`` - Perform shutdown procedures
    
    **Integration Pattern:**
    
    .. code-block:: python
    
        # Standard module creation pattern
        class CustomModule(PicowicdModule):
            def __init__(self, foundation):
                super().__init__(foundation)
                self.name = "Custom Module"
                # Module-specific initialization
        
        # Register with foundation
        module = CustomModule(foundation)
        foundation.register_module("custom", module)
    """
    
    def __init__(self, foundation):
        """
        Initialize base module with foundation integration.
        
        Sets up foundation reference and default enabled state.
        Subclasses should call super().__init__(foundation) first,
        then perform module-specific initialization.
        
        :param foundation: Foundation instance for system services
        :type foundation: PicowicdFoundation
        """
        self.foundation = foundation
        self.enabled = False
        
    def register_routes(self, server):
        """
        Add module's web endpoints to server.
        
        Override this method to register HTTP routes for web interface
        functionality. Use the server.route decorator to add endpoints.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        
        **Example Implementation:**
        
        .. code-block:: python
        
            def register_routes(self, server):
                @server.route("/module-action", methods=['POST'])
                def handle_action(request):
                    # Process request
                    return Response(request, "Success")
        """
        pass
        
    def get_dashboard_html(self):
        """
        Return HTML for dashboard integration.
        
        Override this method to provide HTML widget content for
        inclusion in the main system dashboard. Should return
        self-contained HTML with embedded CSS and JavaScript.
        
        :return: HTML string for dashboard widget
        :rtype: str
        
        **Example Implementation:**
        
        .. code-block:: python
        
            def get_dashboard_html(self):
                return '''
                <div class="module">
                    <h3>My Module</h3>
                    <button onclick="myAction()">Action</button>
                    <script>
                    function myAction() {
                        fetch('/module-action', { method: 'POST' });
                    }
                    </script>
                </div>
                '''
        """
        return ""
        
    def update(self):
        """
        Called from main loop for real-time updates.
        
        Override this method to perform periodic tasks, sensor readings,
        or state updates. Called continuously by the foundation main loop,
        so avoid blocking operations.
        
        **Implementation Guidelines:**
        
        * Keep execution time minimal (< 10ms typical)
        * Use non-blocking operations only
        * Handle exceptions gracefully
        * Use time-based intervals for periodic tasks
        
        **Example Implementation:**
        
        .. code-block:: python
        
            def update(self):
                current_time = time.monotonic()
                if current_time - self.last_reading > self.read_interval:
                    self.read_sensors()
                    self.last_reading = current_time
        """
        pass
        
    def cleanup(self):
        """
        Shutdown procedures.
        
        Override this method to perform cleanup operations before
        system shutdown. Called when the system is stopping or
        when modules are being unloaded.
        
        **Common Cleanup Tasks:**
        
        * Close file handles
        * Disconnect from services  
        * Save state information
        * Release hardware resources
        
        **Example Implementation:**
        
        .. code-block:: python
        
            def cleanup(self):
                if hasattr(self, 'connection'):
                    self.connection.close()
                if hasattr(self, 'data_file'):
                    self.data_file.close()
        """
        pass