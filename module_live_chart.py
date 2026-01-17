# module_live_chart.py
from module_base import WicdpicoModule

class LiveChartModule(WicdpicoModule):
    def __init__(self):
        super().__init__()
        self.name = "Live Trends"
        
    def get_dashboard_html(self):
        # Returns a self-contained JS plotter that consumes existing API
        return """
        <div class="module">
            <h3>Live CO2 Trend</h3>
            <canvas id="chartCanvas" width="300" height="150" style="width:100%; border:1px solid #ddd; background:#fff;"></canvas>
            <div style="font-size:0.8em; color:#666; text-align:center;">Last 60 seconds</div>
            
            <script>
            (function() {
                const maxPoints = 30; // 30 points @ 2s interval = 60 seconds history
                const delay = 2000;
                let dataPoints = []; 
                let ctx = document.getElementById('chartCanvas').getContext('2d');
                let width = ctx.canvas.width;
                let height = ctx.canvas.height;
                let timer = null;

                function drawChart() {
                    // Clear background
                    ctx.clearRect(0, 0, width, height);
                    
                    if (dataPoints.length < 2) return;

                    // 1. Calculate Scales
                    let minVal = Math.min(...dataPoints);
                    let maxVal = Math.max(...dataPoints);
                    let padding = (maxVal - minVal) * 0.1;
                    if (padding === 0) padding = 10;
                    
                    let yMin = minVal - padding;
                    let yMax = maxVal + padding;
                    let range = yMax - yMin;

                    // 2. Draw Line
                    ctx.beginPath();
                    ctx.strokeStyle = '#007bff';
                    ctx.lineWidth = 2;
                    ctx.lineJoin = 'round';

                    let xStep = width / (maxPoints - 1);
                    
                    dataPoints.forEach((val, i) => {
                        let x = i * xStep;
                        // Invert Y because canvas 0 is top
                        let y = height - ((val - yMin) / range * height);
                        
                        // Shift x to right align if data is filling up
                        // OR just let it fill from left. Filling from left is simpler.
                        if (i === 0) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                    });
                    ctx.stroke();

                    // 3. Draw Text Labels
                    ctx.fillStyle = '#333';
                    ctx.font = '10px sans-serif';
                    ctx.fillText(Math.round(maxVal), 5, 10);
                    ctx.fillText(Math.round(minVal), 5, height - 5);
                }

                function fetchData() {
                    // Polls the existing SCD30 module API
                    fetch('/scd30/data')
                        .then(r => r.json())
                        .then(d => {
                            if (!d.error && d.co2) {
                                dataPoints.push(d.co2);
                                if (dataPoints.length > maxPoints) dataPoints.shift();
                                drawChart();
                            }
                        })
                        .catch(e => console.log("Chart fetch error:", e));
                }

                // Start loop when page loads
                if (!timer) timer = setInterval(fetchData, delay);
            })();
            </script>
        </div>
        """

    def update(self):
        pass
