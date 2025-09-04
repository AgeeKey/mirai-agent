"""
HTML UI for Mirai Agent Web Interface
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from .utils import verify_credentials

# Create router for UI routes
ui_router = APIRouter()

# Simple HTML template as string (no external files needed)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mirai Agent - Web Panel</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 24px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            padding: 16px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        .status-card h3 {
            margin: 0 0 8px 0;
            color: #333;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-card .value {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        .controls {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-primary:hover { background: #0056b3; }
        .btn-warning { background: #ffc107; color: #212529; }
        .btn-warning:hover { background: #e0a800; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #218838; }
        .kill-section {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 12px;
        }
        .form-group label {
            display: block;
            margin-bottom: 4px;
            font-weight: 500;
        }
        .form-group input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
        }
        .auto-refresh {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
        .error { color: #dc3545; }
        .success { color: #28a745; }
        .paused { border-left-color: #ffc107; }
        .active { border-left-color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Mirai Agent - Web Panel</h1>
            <p>Real-time monitoring and control interface</p>
        </div>

        <div class="status-grid" id="statusGrid">
            <!-- Status cards will be populated by JavaScript -->
        </div>

        <div class="controls">
            <button class="btn btn-warning" onclick="pauseAgent()">⏸️ Pause</button>
            <button class="btn btn-success" onclick="resumeAgent()">▶️ Resume</button>
            <select id="modeSelect" onchange="changeMode()">
                <option value="advisor">Advisor Mode</option>
                <option value="semi">Semi-Auto Mode</option>
                <option value="auto">Auto Mode</option>
            </select>
        </div>

        <div class="kill-section">
            <h3>🚨 Emergency Kill Switch</h3>
            <div class="form-group">
                <label for="killSymbol">Symbol:</label>
                <input type="text" id="killSymbol" placeholder="BTCUSDT" value="BTCUSDT">
                <button class="btn btn-danger" onclick="killSwitch()">💀 Kill Switch</button>
            </div>
        </div>

        <div class="auto-refresh">
            Auto-refresh every 5 seconds | Last updated: <span id="lastUpdate">--</span>
        </div>
    </div>

    <script>
        let refreshInterval;

        async function fetchStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                updateStatusDisplay(data);
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                return data;
            } catch (error) {
                console.error('Error fetching status:', error);
                document.getElementById('lastUpdate').textContent = 'Error: ' + error.message;
            }
        }

        function updateStatusDisplay(status) {
            const grid = document.getElementById('statusGrid');
            const isPaused = status.agentPaused;
            
            grid.innerHTML = `
                <div class="status-card ${isPaused ? 'paused' : 'active'}">
                    <h3>Status</h3>
                    <div class="value">${isPaused ? '⏸️ PAUSED' : '▶️ ACTIVE'}</div>
                </div>
                <div class="status-card">
                    <h3>Mode</h3>
                    <div class="value">${status.mode.toUpperCase()}</div>
                </div>
                <div class="status-card">
                    <h3>Day P&L</h3>
                    <div class="value" style="color: ${status.dayPnL >= 0 ? '#28a745' : '#dc3545'}">
                        $${status.dayPnL.toFixed(2)}
                    </div>
                </div>
                <div class="status-card">
                    <h3>Max Day P&L</h3>
                    <div class="value">$${status.maxDayPnL.toFixed(2)}</div>
                </div>
                <div class="status-card">
                    <h3>Trades Today</h3>
                    <div class="value">${status.tradesToday}</div>
                </div>
                <div class="status-card">
                    <h3>Consecutive Losses</h3>
                    <div class="value" style="color: ${status.consecutiveLosses > 0 ? '#ffc107' : '#28a745'}">
                        ${status.consecutiveLosses}
                    </div>
                </div>
                <div class="status-card">
                    <h3>Open Positions</h3>
                    <div class="value">${status.openPositions.length}</div>
                </div>
                <div class="status-card">
                    <h3>Errors Count</h3>
                    <div class="value" style="color: ${status.errorsCount > 0 ? '#dc3545' : '#28a745'}">
                        ${status.errorsCount}
                    </div>
                </div>
            `;

            // Update mode selector
            document.getElementById('modeSelect').value = status.mode;
        }

        async function pauseAgent() {
            try {
                const response = await fetch('/pause', { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    alert('✅ Agent paused successfully');
                    fetchStatus();
                } else {
                    alert('❌ Failed to pause agent');
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }

        async function resumeAgent() {
            try {
                const response = await fetch('/resume', { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    alert('✅ Agent resumed successfully');
                    fetchStatus();
                } else {
                    alert('❌ Failed to resume agent');
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }

        async function changeMode() {
            const mode = document.getElementById('modeSelect').value;
            try {
                const response = await fetch('/mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: mode })
                });
                const result = await response.json();
                if (result.success) {
                    alert(`✅ Mode changed to ${mode}`);
                    fetchStatus();
                } else {
                    alert('❌ Failed to change mode');
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }

        async function killSwitch() {
            const symbol = document.getElementById('killSymbol').value.trim().toUpperCase();
            if (!symbol) {
                alert('❌ Please enter a symbol');
                return;
            }

            if (!confirm(`🚨 Are you sure you want to trigger kill switch for ${symbol}?`)) {
                return;
            }

            try {
                const response = await fetch('/kill', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol: symbol })
                });
                const result = await response.json();
                if (result.success) {
                    alert(`💀 Kill switch executed for ${symbol}`);
                    fetchStatus();
                } else {
                    alert('❌ Kill switch failed: ' + result.message);
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            fetchStatus();
            refreshInterval = setInterval(fetchStatus, 5000); // Refresh every 5 seconds
        });

        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>
"""


@ui_router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request, authorized: bool = Depends(verify_credentials)):
    """Serve the main dashboard HTML page"""
    return HTMLResponse(content=HTML_TEMPLATE)
