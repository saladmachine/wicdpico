class TemplateSystem:
    """Centralized HTML template and styling system for wicdpico"""
    
    def __init__(self):
        self.base_css = self._get_base_css()
        self.base_js = self._get_base_js()
    
    def _get_base_css(self):
        """Responsive CSS framework for all modules"""
        return """
        <style>
        * { box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 10px;
            background: #f5f5f5;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
        }
        .module { 
            background: white;
            border: 1px solid #ddd; 
            border-radius: 8px;
            padding: 15px; 
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .module h3 { 
            margin-top: 0; 
            color: #333;
        }
        button { 
            padding: 12px 20px; 
            margin: 5px; 
            border: none;
            border-radius: 5px;
            background: #007bff;
            color: white;
            cursor: pointer;
            font-size: 16px;
            min-height: 44px; /* Touch friendly */
        }
        button:hover { background: #0056b3; }
        button:disabled { 
            background: #ccc; 
            cursor: not-allowed; 
        }
        .status { 
            background: #e9ecef; 
            padding: 10px; 
            border-radius: 5px;
            margin: 10px 0;
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 15px; 
        }
        @media (max-width: 768px) {
            .container { padding: 5px; }
            .module { padding: 10px; margin: 5px 0; }
            button { width: 100%; margin: 5px 0; }
        }
        </style>
        """
    
    def _get_base_js(self):
        """Common JavaScript utilities"""
        return """
        <script>
        // Standard server communication
        function serverRequest(endpoint, method = 'POST', data = null) {
            const options = { method: method };
            if (data) {
                options.body = data;
            }
            return fetch(endpoint, options)
                .then(response => response.text())
                .catch(error => {
                    console.error('Server request failed:', error);
                    throw error;
                });
        }
        
        // Show loading state
        function setButtonLoading(buttonId, loading = true) {
            const button = document.getElementById(buttonId);
            if (button) {
                button.disabled = loading;
                if (loading) {
                    button.dataset.originalText = button.textContent;
                    button.textContent = 'Loading...';
                } else {
                    button.textContent = button.dataset.originalText || button.textContent;
                }
            }
        }
        
        // Update element content safely
        function updateElement(id, content) {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = content;
            }
        }
        </script>
        """
    
    def render_page(self, title, modules_html, system_info=None):
        """Render complete responsive page with modules"""
        system_section = ""
        if system_info:
            system_section = f"""
            <div class="module">
                <h3>System Status</h3>
                <div class="status">
                    {system_info}
                </div>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            {self.base_css}
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                
                <div class="grid">
                    {modules_html}
                </div>
                
                {system_section}
            </div>
            {self.base_js}
        </body>
        </html>
        """