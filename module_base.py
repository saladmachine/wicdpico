class PicowidModule:
    """Base class for all picowicd modules"""
    
    def __init__(self, foundation):
        self.foundation = foundation
        self.enabled = False
        
    def register_routes(self, server):
        """Add module's web endpoints to server"""
        pass
        
    def get_dashboard_html(self):
        """Return HTML for dashboard integration"""
        return ""
        
    def update(self):
        """Called from main loop for real-time updates"""
        pass
        
    def cleanup(self):
        """Shutdown procedures"""
        pass