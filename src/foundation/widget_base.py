from .module_base import PicowidModule

class DashboardWidget(PicowidModule):
    """Base class for dashboard widgets"""
    
    def __init__(self, foundation, widget_id, widget_type):
        super().__init__(foundation)
        self.widget_id = widget_id
        self.widget_type = widget_type
        self.value = None
        
    def get_widget_html(self):
        """Return widget HTML for embedding"""
        return f'<div id="{self.widget_id}" class="widget {self.widget_type}"></div>'
        
    def get_widget_js(self):
        """Return widget JavaScript for interactions"""
        return ""

class ButtonWidget(DashboardWidget):
    """Momentary or toggle button widget"""
    
    def __init__(self, foundation, widget_id, label, action_endpoint):
        super().__init__(foundation, widget_id, "button")
        self.label = label
        self.action_endpoint = action_endpoint
        self.state = False

class SliderWidget(DashboardWidget):
    """Continuous value input widget"""
    
    def __init__(self, foundation, widget_id, min_val, max_val, step):
        super().__init__(foundation, widget_id, "slider")
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

class GaugeWidget(DashboardWidget):
    """Value display widget"""
    
    def __init__(self, foundation, widget_id, min_val, max_val, units):
        super().__init__(foundation, widget_id, "gauge")
        self.min_val = min_val
        self.max_val = max_val
        self.units = units