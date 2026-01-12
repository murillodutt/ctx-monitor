#!/usr/bin/env python3
"""
dashboard-server.py - HTTP + WebSocket server for ctx-monitor web dashboard

Serves the React frontend and provides real-time event streaming via WebSocket.
Reuses existing MetricsCollector and StackAnalyzer logic.

Usage:
    python dashboard-server.py <project_dir> [--port 3847] [--no-open]

Features:
    - HTTP server for static frontend and REST API
    - WebSocket for real-time event streaming
    - File watcher for trace file changes
    - Auto-opens browser on start
"""

import argparse
import asyncio
import json
import os
import signal
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, urlparse
import hashlib

# Import existing analysis modules
sys.path.insert(0, str(Path(__file__).parent))
from dashboard_renderer import MetricsCollector, StackAnalyzer

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_PORT = 3847
WEBSOCKET_PORT_OFFSET = 1  # WebSocket runs on port + 1
POLL_INTERVAL = 1.0  # Seconds between file checks


# =============================================================================
# API HANDLERS
# =============================================================================

class DashboardAPI:
    """REST API for dashboard data."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.traces_dir = project_dir / ".claude" / "ctx-monitor" / "traces"
        self._cache: Dict[str, Any] = {}
        self._cache_hash: str = ""

    def _get_metrics(self, session_id: Optional[str] = None) -> MetricsCollector:
        """Get metrics collector for session."""
        return MetricsCollector(self.project_dir, session_id)

    def _get_stack(self) -> StackAnalyzer:
        """Get stack analyzer."""
        return StackAnalyzer(self.project_dir)

    def get_sessions(self) -> Dict[str, Any]:
        """Get list of all sessions."""
        sessions_file = self.traces_dir / "sessions.json"
        if not sessions_file.exists():
            return {"sessions": [], "count": 0}

        try:
            with open(sessions_file) as f:
                data = json.load(f)
                sessions = data.get("sessions", [])
                # Sort by started_at descending
                sessions.sort(key=lambda s: s.get("started_at", ""), reverse=True)
                return {
                    "sessions": sessions,
                    "count": len(sessions)
                }
        except (json.JSONDecodeError, IOError):
            return {"sessions": [], "count": 0}

    def get_overview(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get overview metrics."""
        metrics = self._get_metrics(session_id)
        stack = self._get_stack()

        session_info = metrics.get_session_info()
        health = metrics.calculate_health_score()
        stats = metrics.compute_statistics()
        stack_summary = stack.get_stack_summary(metrics.events)

        # Calculate token breakdown
        total_stack_tokens = stack_summary["total_tokens"]
        estimated_message_tokens = session_info["event_count"] * 50
        total_used = total_stack_tokens + estimated_message_tokens
        total_available = 200000

        return {
            "session": {
                "id": session_info["session_id"],
                "project": session_info["project"],
                "started_at": session_info["started_at"].isoformat() if session_info["started_at"] else None,
                "duration": session_info["duration"],
                "event_count": session_info["event_count"]
            },
            "health": {
                "score": health,
                "status": "ok" if health >= 70 else "warn" if health >= 50 else "alert"
            },
            "stats": {
                "total_events": stats["total_events"],
                "total_calls": stats["total_calls"],
                "total_errors": stats["total_errors"],
                "error_rate": round(stats["error_rate"], 2),
                "mean_duration": round(stats["mean_duration"], 3),
                "events_per_min": round(stats["events_per_min"], 2)
            },
            "tokens": {
                "used": total_used,
                "available": total_available,
                "percentage": round(total_used / total_available * 100, 1),
                "breakdown": {
                    "rules": stack_summary["rules"]["total_tokens"],
                    "hooks": stack_summary["hooks"].get("tokens", 50),
                    "skills": stack_summary["skills"]["total_tokens"],
                    "agents": stack_summary["agents"]["total_tokens"],
                    "messages": estimated_message_tokens
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_tools(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tool metrics."""
        metrics = self._get_metrics(session_id)
        tool_metrics = metrics.get_tool_metrics()

        tools = []
        for tool in tool_metrics:
            tools.append({
                "name": tool["tool"],
                "calls": tool["calls"],
                "success": tool["success"],
                "errors": tool["errors"],
                "rate": round(tool["rate"], 1),
                "mean_time": round(tool["mean_time"], 3),
                "stdev_time": round(tool["stdev_time"], 3),
                "min_time": round(tool["min_time"], 3),
                "max_time": round(tool["max_time"], 3),
                "sparkline": metrics.get_event_sparkline_data(None, 15)
            })

        total_calls = sum(t["calls"] for t in tools)
        total_errors = sum(t["errors"] for t in tools)

        return {
            "tools": tools,
            "summary": {
                "total_tools": len(tools),
                "total_calls": total_calls,
                "total_errors": total_errors,
                "overall_rate": round((total_calls - total_errors) / total_calls * 100, 1) if total_calls > 0 else 100
            }
        }

    def get_timeline(self, session_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get timeline events."""
        metrics = self._get_metrics(session_id)
        events = metrics.get_timeline_events(limit)
        distribution = metrics.get_event_distribution()

        return {
            "events": events,
            "distribution": distribution,
            "total": metrics.get_session_info()["event_count"]
        }

    def get_alerts(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get alerts."""
        metrics = self._get_metrics(session_id)
        alerts = metrics.get_alerts()

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for alert in alerts:
            sev = alert.get("severity", "INFO")
            if sev in severity_counts:
                severity_counts[sev] += 1

        return {
            "alerts": alerts,
            "counts": severity_counts,
            "total": len(alerts),
            "actionable": sum(v for k, v in severity_counts.items() if k != "INFO")
        }

    def get_stack(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get stack analysis."""
        metrics = self._get_metrics(session_id)
        stack = self._get_stack()
        stack_summary = stack.get_stack_summary(metrics.events)

        return {
            "rules": stack_summary["rules"],
            "hooks": stack_summary["hooks"],
            "skills": stack_summary["skills"],
            "agents": stack_summary["agents"],
            "total_tokens": stack_summary["total_tokens"],
            "total_components": stack_summary["total_components"]
        }

    def get_events_since(self, session_id: Optional[str], last_event_id: Optional[str] = None) -> List[Dict]:
        """Get new events since last_event_id for real-time streaming."""
        metrics = self._get_metrics(session_id)

        if not last_event_id:
            # Return last 10 events
            return metrics.events[-10:] if metrics.events else []

        # Find events after last_event_id
        found = False
        new_events = []
        for event in metrics.events:
            if found:
                new_events.append(event)
            elif event.get("event_id") == last_event_id:
                found = True

        return new_events


# =============================================================================
# HTTP REQUEST HANDLER
# =============================================================================

class DashboardHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler for dashboard API and static files."""

    api: DashboardAPI = None
    frontend_dir: Path = None

    def __init__(self, *args, **kwargs):
        # Set directory for static files
        super().__init__(*args, directory=str(self.frontend_dir), **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API routes
        if path.startswith("/api/"):
            self._handle_api(path, query)
            return

        # Serve index.html for SPA routes
        if not path.startswith("/assets/") and not path.endswith((".js", ".css", ".ico", ".png", ".svg")):
            self.path = "/index.html"

        # Serve static files
        super().do_GET()

    def _handle_api(self, path: str, query: Dict):
        """Handle API requests."""
        session_id = query.get("session", [None])[0]

        try:
            if path == "/api/sessions":
                data = self.api.get_sessions()
            elif path == "/api/overview":
                data = self.api.get_overview(session_id)
            elif path == "/api/tools":
                data = self.api.get_tools(session_id)
            elif path == "/api/timeline":
                limit = int(query.get("limit", [50])[0])
                data = self.api.get_timeline(session_id, limit)
            elif path == "/api/alerts":
                data = self.api.get_alerts(session_id)
            elif path == "/api/stack":
                data = self.api.get_stack(session_id)
            elif path == "/api/events":
                last_id = query.get("since", [None])[0]
                data = {"events": self.api.get_events_since(session_id, last_id)}
            else:
                self._send_error(404, "API endpoint not found")
                return

            self._send_json(data)

        except Exception as e:
            self._send_error(500, str(e))

    def _send_json(self, data: Any):
        """Send JSON response."""
        content = json.dumps(data, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(content))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def _send_error(self, code: int, message: str):
        """Send error response."""
        content = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args):
        """Suppress default logging."""
        pass


# =============================================================================
# FILE WATCHER
# =============================================================================

class TraceWatcher:
    """Watch trace files for changes and notify clients."""

    def __init__(self, traces_dir: Path, callback):
        self.traces_dir = traces_dir
        self.callback = callback
        self._running = False
        self._last_sizes: Dict[str, int] = {}
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start watching."""
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop watching."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _watch_loop(self):
        """Main watch loop."""
        while self._running:
            try:
                self._check_files()
            except Exception:
                pass
            threading.Event().wait(POLL_INTERVAL)

    def _check_files(self):
        """Check for file changes."""
        if not self.traces_dir.exists():
            return

        for trace_file in self.traces_dir.glob("session_*.jsonl"):
            current_size = trace_file.stat().st_size
            last_size = self._last_sizes.get(str(trace_file), 0)

            if current_size > last_size:
                # File grew, read new content
                self._last_sizes[str(trace_file)] = current_size
                self._read_new_events(trace_file, last_size)

    def _read_new_events(self, trace_file: Path, offset: int):
        """Read new events from file."""
        try:
            with open(trace_file, "r") as f:
                f.seek(offset)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            self.callback(event)
                        except json.JSONDecodeError:
                            pass
        except IOError:
            pass


# =============================================================================
# EMBEDDED FRONTEND
# =============================================================================

def get_embedded_frontend() -> str:
    """Return the embedded React frontend as a single HTML file."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ctx-monitor Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        :root {
            /* Brand Colors - ctx-monitor Visual Identity */
            --brand-deep-slate: #2C3E50;
            --brand-audit-blue: #3498DB;
            --brand-white: #FFFFFF;
            --brand-light-gray: #F4F7F6;

            /* Theme Colors */
            --bg-primary: var(--brand-light-gray);
            --bg-secondary: var(--brand-white);
            --bg-tertiary: #E8EDEF;
            --text-primary: var(--brand-deep-slate);
            --text-secondary: #5D6D7E;
            --text-muted: #85929E;
            --border-color: #D5DBDB;
            --border-strong: #AAB7B8;
            --accent-primary: var(--brand-audit-blue);
            --accent-secondary: #2980B9;
            --success: #27AE60;
            --error: #E74C3C;
            --warning: #F39C12;
            --info: var(--brand-audit-blue);
            --shadow-sm: 0 1px 2px rgba(44,62,80,0.04);
            --shadow-md: 0 4px 6px rgba(44,62,80,0.06);
            --shadow-lg: 0 10px 15px rgba(44,62,80,0.08);
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        .dark {
            --bg-primary: #1A252F;
            --bg-secondary: var(--brand-deep-slate);
            --bg-tertiary: #34495E;
            --text-primary: var(--brand-white);
            --text-secondary: #BDC3C7;
            --text-muted: #7F8C8D;
            --border-color: #34495E;
            --border-strong: #5D6D7E;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.2);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.3);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.4);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--font-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            font-size: 13px;
            min-height: 100vh;
        }

        /* Code elements use monospace */
        code, pre, .event-time, .event-tool, .bar-value, .metric-value {
            font-family: var(--font-mono);
        }

        #root {
            min-height: 100vh;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border-strong);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }

        /* Layout */
        .app {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 15px;
        }

        .logo-icon {
            width: 28px;
            height: 28px;
            background: var(--accent-primary);
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: var(--brand-white);
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            color: var(--success);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .nav {
            display: flex;
            gap: 4px;
            background: var(--bg-tertiary);
            padding: 4px;
            border-radius: var(--radius-md);
        }

        .nav-item {
            padding: 8px 16px;
            background: transparent;
            border: none;
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .nav-item:hover {
            color: var(--text-primary);
            background: var(--bg-secondary);
        }

        .nav-item.active {
            color: var(--text-primary);
            background: var(--bg-secondary);
            box-shadow: var(--shadow-sm);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .theme-toggle {
            padding: 8px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 14px;
            transition: all 0.15s ease;
        }

        .theme-toggle:hover {
            color: var(--text-primary);
            border-color: var(--border-strong);
        }

        .main {
            flex: 1;
            padding: 24px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }

        /* Cards */
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            overflow: hidden;
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
        }

        .card-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
        }

        .card-body {
            padding: 20px;
        }

        /* Grid */
        .grid {
            display: grid;
            gap: 20px;
        }

        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        .grid-5 { grid-template-columns: repeat(5, 1fr); }

        @media (max-width: 1200px) {
            .grid-5 { grid-template-columns: repeat(3, 1fr); }
            .grid-4 { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 768px) {
            .grid-5, .grid-4, .grid-3, .grid-2 { grid-template-columns: 1fr; }
        }

        /* Metrics */
        .metric-card {
            text-align: center;
            padding: 20px;
        }

        .metric-value {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .metric-label {
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 10px;
            font-weight: 600;
            margin-top: 8px;
        }

        .status-ok { background: rgba(34, 197, 94, 0.1); color: var(--success); }
        .status-warn { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
        .status-alert { background: rgba(239, 68, 68, 0.1); color: var(--error); }

        /* Sparkline */
        .sparkline {
            display: flex;
            align-items: flex-end;
            gap: 1px;
            height: 24px;
        }

        .sparkline-bar {
            flex: 1;
            background: var(--accent-primary);
            border-radius: 1px;
            min-width: 3px;
            transition: height 0.3s ease;
        }

        /* Progress */
        .progress {
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--accent-primary);
            transition: width 0.3s ease;
        }

        /* Table */
        .table {
            width: 100%;
            border-collapse: collapse;
        }

        .table th, .table td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        .table th {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            background: var(--bg-tertiary);
        }

        .table tr:last-child td {
            border-bottom: none;
        }

        .table tr:hover td {
            background: var(--bg-tertiary);
        }

        /* Event Stream */
        .event-stream {
            max-height: 400px;
            overflow-y: auto;
        }

        .event-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 16px;
            border-bottom: 1px solid var(--border-color);
            font-size: 12px;
        }

        .event-item:last-child {
            border-bottom: none;
        }

        .event-time {
            color: var(--text-muted);
            font-variant-numeric: tabular-nums;
        }

        .event-type {
            padding: 2px 8px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-sm);
            font-weight: 500;
        }

        .event-tool {
            color: var(--accent-primary);
            font-weight: 500;
        }

        .event-status {
            margin-left: auto;
        }

        .event-status.success { color: var(--success); }
        .event-status.error { color: var(--error); }
        .event-status.pending { color: var(--text-muted); }

        /* Alerts */
        .alert-item {
            display: flex;
            gap: 12px;
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
        }

        .alert-item:last-child {
            border-bottom: none;
        }

        .alert-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-top: 6px;
            flex-shrink: 0;
        }

        .alert-indicator.critical { background: var(--error); }
        .alert-indicator.high { background: #F97316; }
        .alert-indicator.medium { background: var(--warning); }
        .alert-indicator.low { background: var(--info); }
        .alert-indicator.info { background: var(--text-muted); }

        .alert-content { flex: 1; }

        .alert-severity {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .alert-message {
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .alert-recommendation {
            font-size: 12px;
            color: var(--text-secondary);
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            color: var(--text-secondary);
        }

        .spinner {
            width: 24px;
            height: 24px;
            border: 2px solid var(--border-color);
            border-top-color: var(--accent-primary);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 12px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }

        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        .empty-state-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        /* Bar Chart */
        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .bar-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .bar-label {
            width: 80px;
            font-weight: 500;
            font-size: 12px;
        }

        .bar-track {
            flex: 1;
            height: 20px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-sm);
            overflow: hidden;
            display: flex;
        }

        .bar-success {
            background: var(--success);
            height: 100%;
        }

        .bar-error {
            background: var(--error);
            height: 100%;
        }

        .bar-value {
            width: 50px;
            text-align: right;
            font-size: 12px;
            color: var(--text-secondary);
        }

        /* Rate Circle */
        .rate-circle {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            font-size: 12px;
            font-weight: 600;
        }

        .rate-excellent { background: rgba(34, 197, 94, 0.15); color: var(--success); }
        .rate-good { background: rgba(59, 130, 246, 0.15); color: var(--info); }
        .rate-warning { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
        .rate-poor { background: rgba(239, 68, 68, 0.15); color: var(--error); }

        /* Footer */
        .footer {
            padding: 16px 24px;
            text-align: center;
            color: var(--text-muted);
            font-size: 11px;
            border-top: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect, useCallback } = React;

        // API Helper
        const api = {
            fetch: async (endpoint, params = {}) => {
                const url = new URL(endpoint, window.location.origin);
                Object.entries(params).forEach(([k, v]) => {
                    if (v !== undefined && v !== null) url.searchParams.set(k, v);
                });
                const res = await fetch(url);
                if (!res.ok) throw new Error('API Error');
                return res.json();
            }
        };

        // SVG Icons
        const Icons = {
            // Audit Shield Logo - ctx-monitor brand identity
            AuditShield: ({ size = 28 }) => (
                <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
                    <path d="M50 12L88 28V55C88 77.5 50 88 50 88C50 88 12 77.5 12 55V28L50 12Z" stroke="var(--brand-deep-slate)" strokeWidth="5" strokeLinejoin="round"/>
                    <path d="M28 50H41L47 38L53 62L59 50H72" stroke="var(--brand-audit-blue)" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
            ),
            Sun: () => (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>
            ),
            Moon: () => (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>
            ),
            Check: () => (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            ),
            X: () => (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            ),
            Circle: () => (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                </svg>
            ),
            Inbox: () => (
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
                </svg>
            ),
            CheckCircle: () => (
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
            ),
            Lightbulb: () => (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
                </svg>
            )
        };

        // Sparkline Component
        function Sparkline({ data = [], height = 24, color = 'var(--accent-primary)' }) {
            const max = Math.max(...data, 1);
            return (
                <div className="sparkline" style={{ height }}>
                    {data.map((val, i) => (
                        <div
                            key={i}
                            className="sparkline-bar"
                            style={{
                                height: `${(val / max) * 100}%`,
                                background: color
                            }}
                        />
                    ))}
                </div>
            );
        }

        // Progress Bar
        function ProgressBar({ value, max = 100 }) {
            const pct = Math.min((value / max) * 100, 100);
            return (
                <div className="progress">
                    <div className="progress-fill" style={{ width: `${pct}%` }} />
                </div>
            );
        }

        // Rate Circle
        function RateCircle({ rate }) {
            const className = rate >= 95 ? 'rate-excellent'
                : rate >= 80 ? 'rate-good'
                : rate >= 60 ? 'rate-warning'
                : 'rate-poor';
            return (
                <span className={`rate-circle ${className}`}>
                    {rate.toFixed(0)}%
                </span>
            );
        }

        // Overview Page
        function OverviewPage({ data }) {
            if (!data) return <div className="loading"><div className="spinner" />Loading...</div>;

            return (
                <div className="grid" style={{ gap: '24px' }}>
                    {/* Top Metrics */}
                    <div className="grid grid-5">
                        <div className="card metric-card">
                            <div className="metric-value" style={{ color: data.health.status === 'ok' ? 'var(--success)' : data.health.status === 'warn' ? 'var(--warning)' : 'var(--error)' }}>
                                {data.health.score}
                            </div>
                            <div className="metric-label">Health Score</div>
                            <span className={`metric-status status-${data.health.status}`}>
                                {data.health.status.toUpperCase()}
                            </span>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.stats.total_events}</div>
                            <div className="metric-label">Total Events</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.stats.total_calls}</div>
                            <div className="metric-label">Tool Calls</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value" style={{ color: data.stats.total_errors > 0 ? 'var(--error)' : 'var(--success)' }}>
                                {data.stats.total_errors}
                            </div>
                            <div className="metric-label">Errors</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.stats.error_rate}%</div>
                            <div className="metric-label">Error Rate</div>
                        </div>
                    </div>

                    {/* Token Usage */}
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">Token Usage</span>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                                {((data.tokens.used / data.tokens.available) * 100).toFixed(1)}% used
                            </span>
                        </div>
                        <div className="card-body">
                            <ProgressBar value={data.tokens.used} max={data.tokens.available} />
                            <div className="grid grid-5" style={{ marginTop: '16px' }}>
                                {Object.entries(data.tokens.breakdown).map(([key, value]) => (
                                    <div key={key} style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: '16px', fontWeight: '600' }}>{value.toLocaleString()}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{key}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Session Info */}
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">Session Info</span>
                        </div>
                        <div className="card-body">
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>SESSION ID</div>
                                    <div style={{ fontWeight: '500' }}>{data.session.id?.slice(0, 8) || 'N/A'}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>PROJECT</div>
                                    <div style={{ fontWeight: '500' }}>{data.session.project}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>DURATION</div>
                                    <div style={{ fontWeight: '500' }}>{Math.round(data.session.duration)}s</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>EVENTS/MIN</div>
                                    <div style={{ fontWeight: '500' }}>{data.stats.events_per_min.toFixed(1)}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        // Tools Page
        function ToolsPage({ data }) {
            if (!data) return <div className="loading"><div className="spinner" />Loading...</div>;

            return (
                <div className="grid" style={{ gap: '24px' }}>
                    {/* Summary */}
                    <div className="grid grid-4">
                        <div className="card metric-card">
                            <div className="metric-value">{data.summary.total_tools}</div>
                            <div className="metric-label">Active Tools</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.summary.total_calls}</div>
                            <div className="metric-label">Total Calls</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value" style={{ color: data.summary.total_errors > 0 ? 'var(--error)' : 'var(--success)' }}>
                                {data.summary.total_errors}
                            </div>
                            <div className="metric-label">Total Errors</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.summary.overall_rate}%</div>
                            <div className="metric-label">Success Rate</div>
                        </div>
                    </div>

                    {/* Bar Chart */}
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">Call Distribution</span>
                        </div>
                        <div className="card-body">
                            <div className="bar-chart">
                                {data.tools.map(tool => {
                                    const maxCalls = Math.max(...data.tools.map(t => t.calls), 1);
                                    const successPct = (tool.success / maxCalls) * 100;
                                    const errorPct = (tool.errors / maxCalls) * 100;
                                    return (
                                        <div key={tool.name} className="bar-row">
                                            <span className="bar-label">{tool.name}</span>
                                            <div className="bar-track">
                                                <div className="bar-success" style={{ width: `${successPct}%` }} />
                                                <div className="bar-error" style={{ width: `${errorPct}%` }} />
                                            </div>
                                            <span className="bar-value">{tool.calls}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    {/* Detailed Table */}
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">Detailed Metrics</span>
                        </div>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Tool</th>
                                    <th>Calls</th>
                                    <th>Success</th>
                                    <th>Errors</th>
                                    <th>Rate</th>
                                    <th>Mean Time</th>
                                    <th>Std Dev</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.tools.map(tool => (
                                    <tr key={tool.name}>
                                        <td style={{ fontWeight: '500', color: 'var(--accent-primary)' }}>{tool.name}</td>
                                        <td>{tool.calls}</td>
                                        <td style={{ color: 'var(--success)' }}>{tool.success}</td>
                                        <td style={{ color: tool.errors > 0 ? 'var(--error)' : 'inherit' }}>{tool.errors}</td>
                                        <td><RateCircle rate={tool.rate} /></td>
                                        <td>{tool.mean_time.toFixed(2)}s</td>
                                        <td>{tool.stdev_time.toFixed(2)}s</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            );
        }

        // Timeline Page
        function TimelinePage({ data }) {
            if (!data) return <div className="loading"><div className="spinner" />Loading...</div>;

            return (
                <div className="grid" style={{ gap: '24px' }}>
                    {/* Event Distribution */}
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">Event Distribution</span>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                                {data.total} total events
                            </span>
                        </div>
                        <div className="card-body">
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                                {Object.entries(data.distribution).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                                    <div key={type} style={{
                                        padding: '8px 16px',
                                        background: 'var(--bg-tertiary)',
                                        borderRadius: 'var(--radius-sm)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px'
                                    }}>
                                        <span style={{ fontWeight: '500' }}>{type}</span>
                                        <span style={{
                                            background: 'var(--accent-primary)',
                                            color: 'var(--brand-white)',
                                            padding: '2px 8px',
                                            borderRadius: '9999px',
                                            fontSize: '11px',
                                            fontWeight: '600'
                                        }}>{count}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Event Stream */}
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">Recent Events</span>
                        </div>
                        <div className="event-stream">
                            {data.events.length === 0 ? (
                                <div className="empty-state">
                                    <div className="empty-state-icon"><Icons.Inbox /></div>
                                    <div className="empty-state-title">No events yet</div>
                                    <p>Events will appear here as they occur</p>
                                </div>
                            ) : (
                                data.events.map((event, i) => (
                                    <div key={i} className="event-item">
                                        <span className="event-time">{event.time}</span>
                                        <span className="event-type">{event.event_type}</span>
                                        <span className="event-tool">{event.tool_name}</span>
                                        <span className={`event-status ${event.status}`}>
                                            {event.status === 'success' ? <Icons.Check /> : event.status === 'error' ? <Icons.X /> : <Icons.Circle />}
                                        </span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            );
        }

        // Alerts Page
        function AlertsPage({ data }) {
            if (!data) return <div className="loading"><div className="spinner" />Loading...</div>;

            return (
                <div className="grid" style={{ gap: '24px' }}>
                    {/* Alert Counts */}
                    <div className="grid grid-5">
                        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map(sev => (
                            <div key={sev} className="card metric-card">
                                <div className="metric-value" style={{
                                    color: sev === 'CRITICAL' ? 'var(--error)'
                                        : sev === 'HIGH' ? '#F97316'
                                        : sev === 'MEDIUM' ? 'var(--warning)'
                                        : sev === 'LOW' ? 'var(--info)'
                                        : 'var(--text-muted)'
                                }}>
                                    {data.counts[sev]}
                                </div>
                                <div className="metric-label">{sev}</div>
                            </div>
                        ))}
                    </div>

                    {/* Active Alerts */}
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">Active Alerts</span>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                                {data.actionable} actionable
                            </span>
                        </div>
                        <div>
                            {data.alerts.length === 0 ? (
                                <div className="empty-state">
                                    <div className="empty-state-icon"><Icons.CheckCircle /></div>
                                    <div className="empty-state-title">All Clear!</div>
                                    <p>No active alerts. System is healthy.</p>
                                </div>
                            ) : (
                                data.alerts.map((alert, i) => (
                                    <div key={i} className="alert-item">
                                        <div className={`alert-indicator ${alert.severity.toLowerCase()}`} />
                                        <div className="alert-content">
                                            <div className="alert-severity" style={{
                                                color: alert.severity === 'CRITICAL' ? 'var(--error)'
                                                    : alert.severity === 'HIGH' ? '#F97316'
                                                    : alert.severity === 'MEDIUM' ? 'var(--warning)'
                                                    : 'var(--info)'
                                            }}>
                                                {alert.severity}
                                            </div>
                                            <div className="alert-message">{alert.message}</div>
                                            <div className="alert-recommendation">
                                                <Icons.Lightbulb /> {alert.recommendation}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            );
        }

        // Stack Page
        function StackPage({ data }) {
            if (!data) return <div className="loading"><div className="spinner" />Loading...</div>;

            return (
                <div className="grid" style={{ gap: '24px' }}>
                    {/* Token Summary */}
                    <div className="grid grid-4">
                        <div className="card metric-card">
                            <div className="metric-value">{data.total_tokens.toLocaleString()}</div>
                            <div className="metric-label">Total Tokens</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.total_components}</div>
                            <div className="metric-label">Components</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.hooks.efficiency.toFixed(1)}%</div>
                            <div className="metric-label">Hook Efficiency</div>
                        </div>
                        <div className="card metric-card">
                            <div className="metric-value">{data.hooks.total_fired}</div>
                            <div className="metric-label">Hooks Fired</div>
                        </div>
                    </div>

                    {/* Components Breakdown */}
                    <div className="grid grid-2">
                        {/* Rules */}
                        <div className="card">
                            <div className="card-header">
                                <span className="card-title">Rules ({data.rules.count})</span>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                                    {data.rules.total_tokens} tokens
                                </span>
                            </div>
                            <div className="card-body">
                                {data.rules.sources.map((source, i) => (
                                    <div key={i} style={{ marginBottom: '12px' }}>
                                        <div style={{ fontWeight: '500', marginBottom: '4px' }}>{source.name}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                                            {source.tokens} tokens • {source.lines} lines
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Hooks */}
                        <div className="card">
                            <div className="card-header">
                                <span className="card-title">Hooks ({data.hooks.count})</span>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                                    {data.hooks.total_matchers} matchers
                                </span>
                            </div>
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Event</th>
                                        <th>Fired</th>
                                        <th>Errors</th>
                                        <th>Rate</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.hooks.hooks.filter(h => h.fired > 0).map(hook => (
                                        <tr key={hook.event}>
                                            <td>{hook.event}</td>
                                            <td>{hook.fired}</td>
                                            <td style={{ color: hook.errors > 0 ? 'var(--error)' : 'inherit' }}>{hook.errors}</td>
                                            <td>{hook.rate !== null ? `${hook.rate.toFixed(0)}%` : '-'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Skills & Agents */}
                    <div className="grid grid-2">
                        <div className="card">
                            <div className="card-header">
                                <span className="card-title">Skills ({data.skills.count})</span>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                                    {data.skills.total_tokens} tokens
                                </span>
                            </div>
                            <div className="card-body">
                                {data.skills.skills.length === 0 ? (
                                    <p style={{ color: 'var(--text-muted)' }}>No skills configured</p>
                                ) : (
                                    data.skills.skills.map((skill, i) => (
                                        <div key={i} style={{ marginBottom: '8px' }}>
                                            <span style={{ fontWeight: '500' }}>{skill.name}</span>
                                            <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>{skill.tokens} tokens</span>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                        <div className="card">
                            <div className="card-header">
                                <span className="card-title">Agents ({data.agents.count})</span>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>
                                    {data.agents.total_tokens} tokens
                                </span>
                            </div>
                            <div className="card-body">
                                {data.agents.agents.length === 0 ? (
                                    <p style={{ color: 'var(--text-muted)' }}>No agents configured</p>
                                ) : (
                                    data.agents.agents.map((agent, i) => (
                                        <div key={i} style={{ marginBottom: '8px' }}>
                                            <span style={{ fontWeight: '500' }}>{agent.name}</span>
                                            <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>{agent.tokens} tokens</span>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        // Main App
        function App() {
            const [page, setPage] = useState('overview');
            const [darkMode, setDarkMode] = useState(false);
            const [data, setData] = useState({});
            const [loading, setLoading] = useState(true);

            const fetchData = useCallback(async () => {
                try {
                    const endpoints = {
                        overview: '/api/overview',
                        tools: '/api/tools',
                        timeline: '/api/timeline',
                        alerts: '/api/alerts',
                        stack: '/api/stack'
                    };
                    const result = await api.fetch(endpoints[page]);
                    setData(prev => ({ ...prev, [page]: result }));
                    setLoading(false);
                } catch (err) {
                    console.error('API Error:', err);
                    setLoading(false);
                }
            }, [page]);

            useEffect(() => {
                fetchData();
                const interval = setInterval(fetchData, 2000);
                return () => clearInterval(interval);
            }, [fetchData]);

            useEffect(() => {
                document.documentElement.classList.toggle('dark', darkMode);
            }, [darkMode]);

            const pages = [
                { id: 'overview', label: 'Overview' },
                { id: 'tools', label: 'Tools' },
                { id: 'timeline', label: 'Timeline' },
                { id: 'alerts', label: 'Alerts' },
                { id: 'stack', label: 'Stack' }
            ];

            const renderPage = () => {
                const pageData = data[page];
                switch (page) {
                    case 'overview': return <OverviewPage data={pageData} />;
                    case 'tools': return <ToolsPage data={pageData} />;
                    case 'timeline': return <TimelinePage data={pageData} />;
                    case 'alerts': return <AlertsPage data={pageData} />;
                    case 'stack': return <StackPage data={pageData} />;
                    default: return null;
                }
            };

            return (
                <div className="app">
                    <header className="header">
                        <div className="logo">
                            <Icons.AuditShield size={32} />
                            <span><span style={{color: "var(--brand-deep-slate)"}}>ctx</span><span style={{color: "var(--brand-audit-blue)"}}>-monitor</span></span>
                        </div>

                        <nav className="nav">
                            {pages.map(p => (
                                <button
                                    key={p.id}
                                    className={`nav-item ${page === p.id ? 'active' : ''}`}
                                    onClick={() => setPage(p.id)}
                                >
                                    {p.label}
                                </button>
                            ))}
                        </nav>

                        <div className="header-actions">
                            <div className="live-indicator">
                                <div className="live-dot" />
                                Live
                            </div>
                            <button
                                className="theme-toggle"
                                onClick={() => setDarkMode(!darkMode)}
                                title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                            >
                                {darkMode ? <Icons.Sun /> : <Icons.Moon />}
                            </button>
                        </div>
                    </header>

                    <main className="main">
                        {renderPage()}
                    </main>

                    <footer className="footer">
                        ctx-monitor v0.3.5 • Context Oracle
                    </footer>
                </div>
            );
        }

        ReactDOM.createRoot(document.getElementById('root')).render(<App />);
    </script>
</body>
</html>'''


# =============================================================================
# MAIN SERVER
# =============================================================================

def create_temp_frontend_dir() -> Path:
    """Create temporary directory with frontend files."""
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix="ctx-monitor-"))

    # Write index.html
    index_file = temp_dir / "index.html"
    index_file.write_text(get_embedded_frontend())

    return temp_dir


def run_server(project_dir: str, port: int = DEFAULT_PORT, no_open: bool = False):
    """Run the dashboard server."""
    project_path = Path(project_dir).resolve()

    if not project_path.exists():
        print(f"Error: Project directory not found: {project_path}", file=sys.stderr)
        sys.exit(2)

    # Create API
    api = DashboardAPI(project_path)

    # Create temp frontend directory
    frontend_dir = create_temp_frontend_dir()

    # Configure handler
    DashboardHTTPHandler.api = api
    DashboardHTTPHandler.frontend_dir = frontend_dir

    # Create server
    server = HTTPServer(("", port), DashboardHTTPHandler)

    # Start file watcher
    traces_dir = project_path / ".claude" / "ctx-monitor" / "traces"
    watcher = TraceWatcher(traces_dir, lambda e: None)  # WebSocket notifications handled separately
    watcher.start()

    # Handle shutdown
    def shutdown(signum, frame):
        print("\nShutting down...")
        watcher.stop()
        server.shutdown()
        # Cleanup temp dir
        import shutil
        shutil.rmtree(frontend_dir, ignore_errors=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    url = f"http://localhost:{port}"
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  ctx-monitor Dashboard")
    print(f"  {url}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Press Ctrl+C to stop")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Open browser
    if not no_open:
        webbrowser.open(url)

    # Run server
    server.serve_forever()


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Launch ctx-monitor web dashboard"
    )
    parser.add_argument(
        "project_dir",
        help="Path to project directory"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Server port (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't open browser automatically"
    )

    args = parser.parse_args()
    run_server(args.project_dir, args.port, args.no_open)


if __name__ == "__main__":
    main()
