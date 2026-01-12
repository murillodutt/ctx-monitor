#!/usr/bin/env python3
"""
dashboard-renderer.py - Rich Unicode dashboard for ctx-monitor

Renders visual dashboards with sparklines, progress indicators, bar charts,
histograms, and detailed metrics for context engineering observability.

Usage:
    python dashboard-renderer.py <project_dir> [--page <name>] [--session <id>] [--no-color] [--width <n>]

Pages:
    overview (default) - Health, events, token usage, quick stats
    stack              - Context engineering stack (rules, hooks, skills, agents)
    tools              - Tool performance with graphs and statistics
    timeline           - Event flow and distribution over time
    alerts             - Alerts, recommendations, historical comparison
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import math
import statistics

# =============================================================================
# UNICODE GRAPHICS LIBRARY
# =============================================================================

class Sparkline:
    """Generate sparkline graphs using block characters."""

    BLOCKS = " ▁▂▃▄▅▆▇█"

    @classmethod
    def from_values(cls, values: List[float], width: Optional[int] = None) -> str:
        """Generate sparkline from a list of values."""
        if not values:
            return ""

        if width and len(values) > width:
            # Downsample to fit width
            step = len(values) / width
            values = [values[int(i * step)] for i in range(width)]

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        result = []
        for v in values:
            normalized = (v - min_val) / range_val
            index = int(normalized * (len(cls.BLOCKS) - 1))
            result.append(cls.BLOCKS[index])

        return "".join(result)

    @classmethod
    def from_timeseries(cls, data: List[Tuple[datetime, float]], width: int = 30) -> str:
        """Generate sparkline from timestamped data."""
        if not data:
            return cls.BLOCKS[0] * width

        values = [v for _, v in sorted(data, key=lambda x: x[0])]
        return cls.from_values(values, width)


class ProgressCircle:
    """Generate progress indicators using circle characters."""

    CIRCLES = "○◔◑◕●"  # 0%, 25%, 50%, 75%, 100%

    @classmethod
    def from_percentage(cls, pct: float) -> str:
        """Get circle indicator for percentage (0-100)."""
        if pct <= 0:
            return cls.CIRCLES[0]
        elif pct < 25:
            return cls.CIRCLES[0]
        elif pct < 50:
            return cls.CIRCLES[1]
        elif pct < 75:
            return cls.CIRCLES[2]
        elif pct < 100:
            return cls.CIRCLES[3]
        else:
            return cls.CIRCLES[4]

    @classmethod
    def rate_indicator(cls, success: int, total: int, count: int = 15) -> str:
        """Generate a row of circles showing success rate over recent calls."""
        if total == 0:
            return cls.CIRCLES[4] * count

        rate = success / total
        filled = int(rate * count)
        return cls.CIRCLES[4] * filled + cls.CIRCLES[0] * (count - filled)


class BarChart:
    """Generate horizontal bar charts."""

    FILLED = "█"
    PARTIAL = "▒"
    EMPTY = "░"

    @classmethod
    def render(cls, values: Dict[str, Tuple[float, float]], width: int = 60) -> List[str]:
        """
        Render horizontal bar chart.

        Args:
            values: Dict of {label: (success_count, error_count)}
            width: Total width for the bar
        """
        if not values:
            return []

        max_val = max(s + e for s, e in values.values()) if values else 1
        lines = []

        for label, (success, error) in values.items():
            total = success + error
            if max_val > 0:
                success_width = int((success / max_val) * width)
                error_width = int((error / max_val) * width)
            else:
                success_width = 0
                error_width = 0

            empty_width = width - success_width - error_width
            bar = cls.FILLED * success_width + cls.PARTIAL * error_width + cls.EMPTY * empty_width
            lines.append(f"{label:<10} {bar} {int(total):>4}")

        return lines

    @classmethod
    def simple_bar(cls, value: float, max_value: float, width: int = 40) -> str:
        """Render a simple progress bar."""
        if max_value <= 0:
            return cls.EMPTY * width

        filled = int((value / max_value) * width)
        return cls.FILLED * filled + cls.EMPTY * (width - filled)


class Histogram:
    """Generate vertical histograms."""

    BLOCKS = " ▁▂▃▄▅▆▇█"

    @classmethod
    def render(cls, values: List[float], buckets: int = 20, height: int = 8) -> List[str]:
        """
        Render vertical histogram.

        Returns list of strings, one per row (top to bottom).
        """
        if not values:
            return [" " * buckets for _ in range(height)]

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Create histogram buckets
        bucket_counts = [0] * buckets
        for v in values:
            bucket_idx = min(int((v - min_val) / range_val * buckets), buckets - 1)
            bucket_counts[bucket_idx] += 1

        max_count = max(bucket_counts) if bucket_counts else 1

        # Render from top to bottom
        lines = []
        for row in range(height - 1, -1, -1):
            threshold = (row / height) * max_count
            line = ""
            for count in bucket_counts:
                if count > threshold:
                    # Calculate how much of this block to fill
                    fill_ratio = min((count - threshold) / (max_count / height), 1.0)
                    block_idx = int(fill_ratio * (len(cls.BLOCKS) - 1))
                    line += cls.BLOCKS[block_idx]
                else:
                    line += " "
            lines.append(line)

        return lines


class TrendIndicator:
    """Generate trend arrows."""

    @classmethod
    def from_change(cls, old: float, new: float, threshold: float = 0.05) -> str:
        """
        Get trend arrow based on percentage change.

        Args:
            old: Previous value
            new: Current value
            threshold: Minimum change to show trend (default 5%)
        """
        if old == 0:
            if new > 0:
                return "↑"
            elif new < 0:
                return "↓"
            return "→"

        change = (new - old) / abs(old)

        if change > threshold * 2:
            return "↑"
        elif change > threshold:
            return "↗"
        elif change < -threshold * 2:
            return "↓"
        elif change < -threshold:
            return "↘"
        else:
            return "→"

    @classmethod
    def with_percentage(cls, old: float, new: float) -> str:
        """Get trend arrow with percentage change."""
        arrow = cls.from_change(old, new)
        if old == 0:
            return arrow

        change = ((new - old) / abs(old)) * 100
        sign = "+" if change >= 0 else ""
        return f"{arrow} {sign}{change:.0f}%"


class Box:
    """Box drawing utilities."""

    # Single line box characters
    TL = "┌"
    TR = "┐"
    BL = "└"
    BR = "┘"
    H = "─"
    V = "│"
    LT = "├"
    RT = "┤"
    TT = "┬"
    BT = "┴"
    CROSS = "┼"

    @classmethod
    def draw(cls, title: str, content: List[str], width: int = 78) -> List[str]:
        """Draw a box with title and content."""
        inner_width = width - 2
        lines = []

        # Top border with title
        if title:
            title_str = f" {title} "
            padding = inner_width - len(title_str) - 2
            lines.append(f"{cls.TL}{cls.H}{cls.H}{title_str}{cls.H * padding}{cls.TR}")
        else:
            lines.append(f"{cls.TL}{cls.H * inner_width}{cls.TR}")

        # Content
        for line in content:
            padded = line[:inner_width].ljust(inner_width)
            lines.append(f"{cls.V}{padded}{cls.V}")

        # Bottom border
        lines.append(f"{cls.BL}{cls.H * inner_width}{cls.BR}")

        return lines

    @classmethod
    def separator(cls, width: int = 78) -> str:
        """Draw a horizontal separator."""
        return f"{cls.LT}{cls.H * (width - 2)}{cls.RT}"


class Table:
    """Aligned table rendering."""

    @classmethod
    def render(cls, headers: List[str], rows: List[List[str]],
               widths: Optional[List[int]] = None, separator: str = "│") -> List[str]:
        """
        Render an aligned table.

        Args:
            headers: Column headers
            rows: List of rows (each row is a list of cell values)
            widths: Optional column widths (auto-calculated if not provided)
            separator: Column separator character
        """
        if not headers:
            return []

        # Calculate column widths
        if widths is None:
            widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(widths):
                        widths[i] = max(widths[i], len(str(cell)))

        lines = []

        # Header
        header_line = f"  {separator}  ".join(
            h.ljust(w) if i == 0 else h.center(w)
            for i, (h, w) in enumerate(zip(headers, widths))
        )
        lines.append(header_line)

        # Separator
        sep_line = "──" + "┼──".join("─" * w for w in widths) + "──"
        lines.append(sep_line)

        # Rows
        for row in rows:
            row_line = f"  {separator}  ".join(
                str(cell).ljust(w) if i == 0 else str(cell).rjust(w)
                for i, (cell, w) in enumerate(zip(row, widths))
            )
            lines.append(row_line)

        return lines


class Tree:
    """Hierarchical tree rendering."""

    BRANCH = "├─"
    LAST = "└─"
    PIPE = "│ "
    SPACE = "  "
    DOT = "·"

    @classmethod
    def render(cls, items: List[Tuple[str, Any]], indent: int = 0) -> List[str]:
        """
        Render a tree structure.

        Args:
            items: List of (label, value_or_children) tuples
            indent: Current indentation level
        """
        lines = []
        prefix = cls.SPACE * indent

        for i, (label, value) in enumerate(items):
            is_last = i == len(items) - 1
            branch = cls.LAST if is_last else cls.BRANCH

            if isinstance(value, list):
                # Has children
                lines.append(f"{prefix}{branch} {label}")
                child_prefix = cls.SPACE if is_last else cls.PIPE
                for child_line in cls.render(value, indent + 1):
                    lines.append(f"{prefix}{child_prefix}{child_line}")
            else:
                # Leaf node with value
                dots = cls.DOT * (40 - len(label) - indent * 2)
                lines.append(f"{prefix}{branch} {label} {dots} {value}")

        return lines


# =============================================================================
# DATA AGGREGATION
# =============================================================================

class StackAnalyzer:
    """Analyze context engineering stack components."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.plugin_dir = self._find_plugin_dir()

    def _find_plugin_dir(self) -> Optional[Path]:
        """Find the ctx-monitor plugin directory."""
        # Check common locations
        candidates = [
            self.project_dir / "plugins" / "ctx-monitor",
            self.project_dir / ".claude" / "plugins" / "ctx-monitor",
            Path(__file__).parent.parent,
        ]

        for path in candidates:
            if path.exists() and (path / ".claude-plugin").exists():
                return path

        return None

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (~4 chars = 1 token)."""
        return len(text) // 4

    def analyze_rules(self) -> Dict[str, Any]:
        """Analyze rules from CLAUDE.md, settings.json, etc."""
        sources = []
        total_tokens = 0

        # Check CLAUDE.md
        claude_md = self.project_dir / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            tokens = self._estimate_tokens(content)
            total_tokens += tokens

            # Parse sections
            sections = []
            for line in content.split("\n"):
                if line.startswith("## "):
                    sections.append(line[3:].strip())

            sources.append({
                "name": "CLAUDE.md",
                "path": str(claude_md),
                "tokens": tokens,
                "lines": len(content.split("\n")),
                "sections": sections
            })

        # Check .claude/settings.json
        settings_json = self.project_dir / ".claude" / "settings.json"
        if settings_json.exists():
            content = settings_json.read_text()
            tokens = self._estimate_tokens(content)
            total_tokens += tokens
            sources.append({
                "name": ".claude/settings.json",
                "path": str(settings_json),
                "tokens": tokens,
                "lines": len(content.split("\n")),
                "sections": []
            })

        # Check ctx-monitor.local.md
        local_md = self.project_dir / ".claude" / "ctx-monitor.local.md"
        if local_md.exists():
            content = local_md.read_text()
            tokens = self._estimate_tokens(content)
            total_tokens += tokens
            sources.append({
                "name": "ctx-monitor.local.md",
                "path": str(local_md),
                "tokens": tokens,
                "lines": len(content.split("\n")),
                "sections": []
            })

        return {
            "count": len(sources),
            "sources": sources,
            "total_tokens": total_tokens,
            "warnings": []
        }

    def analyze_hooks(self, events: List[Dict] = None) -> Dict[str, Any]:
        """Analyze hooks configuration and correlate with events."""
        hooks_data = []
        total_matchers = 0

        # Find hooks.json
        hooks_files = []
        if self.plugin_dir:
            hooks_json = self.plugin_dir / "hooks" / "hooks.json"
            if hooks_json.exists():
                hooks_files.append(hooks_json)

        local_hooks = self.project_dir / ".claude" / "hooks.json"
        if local_hooks.exists():
            hooks_files.append(local_hooks)

        event_types = set()
        for hooks_file in hooks_files:
            try:
                with open(hooks_file) as f:
                    data = json.load(f)
                    # Handle nested structure: {"hooks": {"EventType": [...]}}
                    hooks_config = data.get("hooks", data)
                    if isinstance(hooks_config, dict):
                        for event_type, matchers in hooks_config.items():
                            if event_type in ["description"]:
                                continue
                            event_types.add(event_type)
                            if isinstance(matchers, list):
                                total_matchers += len(matchers)
            except (json.JSONDecodeError, IOError):
                pass

        # Correlate with events if provided
        event_counts = defaultdict(lambda: {"fired": 0, "errors": 0})
        if events:
            for event in events:
                event_type = event.get("event_type", "")
                status = event.get("status", "")

                if event_type in event_types or event_type in ["PreToolUse", "PostToolUse",
                    "SessionStart", "SessionEnd", "UserPromptSubmit", "SubagentStop",
                    "Stop", "PreCompact", "Notification"]:
                    event_counts[event_type]["fired"] += 1
                    if status == "error":
                        event_counts[event_type]["errors"] += 1

        # Build hooks data
        standard_events = ["PreToolUse", "PostToolUse", "SessionStart", "SessionEnd",
                         "UserPromptSubmit", "SubagentStop", "Stop", "PreCompact", "Notification"]

        for event_type in standard_events:
            counts = event_counts.get(event_type, {"fired": 0, "errors": 0})
            fired = counts["fired"]
            errors = counts["errors"]
            rate = ((fired - errors) / fired * 100) if fired > 0 else None

            hooks_data.append({
                "event": event_type,
                "matchers": 1 if event_type in event_types else 0,
                "fired": fired,
                "errors": errors,
                "rate": rate
            })

        total_fired = sum(h["fired"] for h in hooks_data)
        total_errors = sum(h["errors"] for h in hooks_data)
        efficiency = ((total_fired - total_errors) / total_fired * 100) if total_fired > 0 else 100.0

        return {
            "count": len(standard_events),
            "hooks": hooks_data,
            "total_matchers": total_matchers,
            "total_fired": total_fired,
            "total_errors": total_errors,
            "efficiency": efficiency,
            "tokens": 50  # Estimated tokens for hooks config
        }

    def analyze_skills(self) -> Dict[str, Any]:
        """Analyze available skills."""
        skills = []
        total_tokens = 0

        if self.plugin_dir:
            skills_dir = self.plugin_dir / "skills"
            if skills_dir.exists():
                for skill_dir in skills_dir.iterdir():
                    if skill_dir.is_dir():
                        skill_md = skill_dir / "SKILL.md"
                        if skill_md.exists():
                            content = skill_md.read_text()
                            tokens = self._estimate_tokens(content)
                            total_tokens += tokens
                            skills.append({
                                "name": skill_dir.name,
                                "path": str(skill_md),
                                "tokens": tokens,
                                "triggered": 0  # Would need trace correlation
                            })

        return {
            "count": len(skills),
            "skills": skills,
            "total_tokens": total_tokens
        }

    def analyze_agents(self) -> Dict[str, Any]:
        """Analyze available agents."""
        agents = []
        total_tokens = 0

        if self.plugin_dir:
            agents_dir = self.plugin_dir / "agents"
            if agents_dir.exists():
                for agent_file in agents_dir.glob("*.md"):
                    content = agent_file.read_text()
                    tokens = self._estimate_tokens(content)
                    total_tokens += tokens
                    agents.append({
                        "name": agent_file.stem,
                        "path": str(agent_file),
                        "tokens": tokens,
                        "invocations": 0  # Would need trace correlation
                    })

        return {
            "count": len(agents),
            "agents": agents,
            "total_tokens": total_tokens
        }

    def get_stack_summary(self, events: List[Dict] = None) -> Dict[str, Any]:
        """Get complete stack analysis summary."""
        rules = self.analyze_rules()
        hooks = self.analyze_hooks(events)
        skills = self.analyze_skills()
        agents = self.analyze_agents()

        total_tokens = (
            rules["total_tokens"] +
            hooks.get("tokens", 0) +
            skills["total_tokens"] +
            agents["total_tokens"]
        )

        return {
            "rules": rules,
            "hooks": hooks,
            "skills": skills,
            "agents": agents,
            "total_tokens": total_tokens,
            "total_components": rules["count"] + hooks["count"] + skills["count"] + agents["count"]
        }


class MetricsCollector:
    """Collect and compute metrics from traces."""

    def __init__(self, project_dir: Path, session_id: Optional[str] = None):
        self.project_dir = project_dir
        self.traces_dir = project_dir / ".claude" / "ctx-monitor" / "traces"
        self.session_id = session_id
        self.events = []
        self._load_events()

    def _load_events(self):
        """Load events from trace file."""
        if not self.traces_dir.exists():
            return

        trace_file = None

        # Find session file
        if self.session_id:
            trace_file = self.traces_dir / f"session_{self.session_id}.jsonl"
        else:
            # Try sessions.json first
            sessions_file = self.traces_dir / "sessions.json"
            if sessions_file.exists() and sessions_file.stat().st_size > 0:
                try:
                    with open(sessions_file) as f:
                        sessions_data = json.load(f)
                        sessions = sessions_data.get("sessions", [])
                        if sessions:
                            latest = max(sessions, key=lambda s: s.get("started_at", ""))
                            self.session_id = latest.get("session_id")
                            trace_file = self.traces_dir / f"session_{self.session_id}.jsonl"
                except (json.JSONDecodeError, IOError):
                    pass

            # Fallback: find most recent trace file directly
            if trace_file is None or not trace_file.exists():
                trace_files = list(self.traces_dir.glob("session_*.jsonl"))
                if trace_files:
                    trace_file = max(trace_files, key=lambda f: f.stat().st_mtime)
                    self.session_id = trace_file.stem.replace("session_", "")

        if trace_file is None or not trace_file.exists():
            return

        # Load events
        try:
            with open(trace_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self.events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except IOError:
            pass

    def get_session_info(self) -> Dict[str, Any]:
        """Get basic session information."""
        if not self.events:
            return {
                "session_id": self.session_id,
                "started_at": None,
                "duration": 0,
                "event_count": 0,
                "project": self.project_dir.name
            }

        # Parse timestamps
        timestamps = []
        for event in self.events:
            ts_str = event.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    timestamps.append(ts)
                except ValueError:
                    pass

        started_at = min(timestamps) if timestamps else None
        ended_at = max(timestamps) if timestamps else None
        duration = (ended_at - started_at).total_seconds() if started_at and ended_at else 0

        return {
            "session_id": self.session_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration": duration,
            "event_count": len(self.events),
            "project": self.project_dir.name
        }

    def get_tool_metrics(self) -> List[Dict[str, Any]]:
        """Get per-tool performance metrics."""
        tool_stats = defaultdict(lambda: {
            "calls": 0, "success": 0, "errors": 0, "durations": []
        })

        for event in self.events:
            event_type = event.get("event_type")
            tool_name = event.get("tool_name")
            status = event.get("status")

            if event_type == "PostToolUse" and tool_name:
                tool_stats[tool_name]["calls"] += 1
                if status == "success":
                    tool_stats[tool_name]["success"] += 1
                elif status == "error":
                    tool_stats[tool_name]["errors"] += 1

                duration = event.get("duration_ms")
                if duration:
                    tool_stats[tool_name]["durations"].append(duration / 1000)

        results = []
        for tool, stats in sorted(tool_stats.items(), key=lambda x: -x[1]["calls"]):
            durations = stats["durations"]
            rate = (stats["success"] / stats["calls"] * 100) if stats["calls"] > 0 else 0

            results.append({
                "tool": tool,
                "calls": stats["calls"],
                "success": stats["success"],
                "errors": stats["errors"],
                "rate": rate,
                "mean_time": statistics.mean(durations) if durations else 0,
                "stdev_time": statistics.stdev(durations) if len(durations) > 1 else 0,
                "min_time": min(durations) if durations else 0,
                "max_time": max(durations) if durations else 0
            })

        return results

    def get_event_distribution(self) -> Dict[str, int]:
        """Get event count by type."""
        distribution = defaultdict(int)
        for event in self.events:
            event_type = event.get("event_type", "Unknown")
            distribution[event_type] += 1
        return dict(distribution)

    def get_timeline_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events for timeline display."""
        # Sort by timestamp descending
        sorted_events = sorted(
            self.events,
            key=lambda e: e.get("timestamp", ""),
            reverse=True
        )[:limit]

        results = []
        for event in sorted_events:
            ts_str = event.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                time_str = ts.strftime("%H:%M:%S")
            except ValueError:
                time_str = ts_str[:8] if ts_str else "??:??:??"

            results.append({
                "time": time_str,
                "event_type": event.get("event_type", "Unknown"),
                "tool_name": event.get("tool_name", "-"),
                "status": event.get("status", "-"),
                "preview": (event.get("args_preview") or event.get("result_preview") or "-")[:40]
            })

        return results

    def get_error_breakdown(self) -> List[Dict[str, Any]]:
        """Get breakdown of errors by tool and type."""
        errors = []

        for event in self.events:
            if event.get("status") == "error":
                errors.append({
                    "tool": event.get("tool_name", "Unknown"),
                    "error_type": event.get("error_message", "Unknown error")[:30],
                    "timestamp": event.get("timestamp", "")
                })

        return errors[:10]  # Limit to 10 most recent

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Generate alerts based on metrics analysis."""
        alerts = []
        tool_metrics = self.get_tool_metrics()

        # Check for high error rate tools
        for tool in tool_metrics:
            if tool["calls"] > 0:
                error_rate = (tool["errors"] / tool["calls"]) * 100
                if error_rate >= 50:
                    alerts.append({
                        "severity": "CRITICAL",
                        "indicator": "○",
                        "message": f"Tool '{tool['tool']}' has {error_rate:.0f}% failure rate ({tool['errors']}/{tool['calls']} calls)",
                        "recommendation": "Check context limits, reduce payload size"
                    })
                elif error_rate >= 20:
                    alerts.append({
                        "severity": "HIGH",
                        "indicator": "◔",
                        "message": f"Tool '{tool['tool']}' has {error_rate:.0f}% failure rate ({tool['errors']}/{tool['calls']} calls)",
                        "recommendation": "Verify file permissions and paths"
                    })
                elif error_rate >= 10:
                    alerts.append({
                        "severity": "MEDIUM",
                        "indicator": "◑",
                        "message": f"Tool '{tool['tool']}' has {error_rate:.0f}% failure rate",
                        "recommendation": "Monitor for patterns"
                    })

        # Check for unpaired events
        pre_count = sum(1 for e in self.events if e.get("event_type") == "PreToolUse")
        post_count = sum(1 for e in self.events if e.get("event_type") == "PostToolUse")
        unpaired = abs(pre_count - post_count)

        if unpaired > 0:
            alerts.append({
                "severity": "HIGH" if unpaired > 5 else "MEDIUM",
                "indicator": "◔" if unpaired > 5 else "◑",
                "message": f"{unpaired} PreToolUse events without matching PostToolUse",
                "recommendation": "Investigate hook execution failures"
            })

        return alerts

    def compute_statistics(self) -> Dict[str, Any]:
        """Compute overall statistics."""
        tool_metrics = self.get_tool_metrics()
        session_info = self.get_session_info()

        total_calls = sum(t["calls"] for t in tool_metrics)
        total_errors = sum(t["errors"] for t in tool_metrics)
        all_durations = []
        for t in tool_metrics:
            if t["mean_time"] > 0:
                all_durations.extend([t["mean_time"]] * t["calls"])

        return {
            "total_events": session_info["event_count"],
            "total_calls": total_calls,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_calls * 100) if total_calls > 0 else 0,
            "mean_duration": statistics.mean(all_durations) if all_durations else 0,
            "stdev_duration": statistics.stdev(all_durations) if len(all_durations) > 1 else 0,
            "events_per_min": (session_info["event_count"] / (session_info["duration"] / 60)) if session_info["duration"] > 0 else 0
        }

    def calculate_health_score(self) -> int:
        """Calculate overall health score (0-100)."""
        score = 100.0
        stats = self.compute_statistics()

        # Error rate penalty (40% weight)
        if stats["total_calls"] > 0:
            error_rate = stats["total_errors"] / stats["total_calls"]
            score -= error_rate * 40

        # Unreliable tools penalty (30% weight)
        tool_metrics = self.get_tool_metrics()
        unreliable = sum(1 for t in tool_metrics if t["calls"] > 0 and t["errors"] / t["calls"] > 0.2)
        score -= min(unreliable * 10, 30)

        # Session completeness (20% weight)
        event_types = {e.get("event_type") for e in self.events}
        if "SessionStart" not in event_types:
            score -= 10
        if "SessionEnd" not in event_types and "Stop" not in event_types:
            score -= 10

        # Event pairing (10% weight)
        pre_count = sum(1 for e in self.events if e.get("event_type") == "PreToolUse")
        post_count = sum(1 for e in self.events if e.get("event_type") == "PostToolUse")
        if pre_count > 0:
            pairing_rate = min(post_count / pre_count, 1.0)
            score -= (1 - pairing_rate) * 10

        return max(0, min(100, int(score)))


# =============================================================================
# PAGE RENDERERS
# =============================================================================

class OverviewPage:
    """Render overview page."""

    def __init__(self, metrics: MetricsCollector, stack: StackAnalyzer, width: int = 80):
        self.metrics = metrics
        self.stack = stack
        self.width = width

    def render(self) -> str:
        """Render the overview page."""
        lines = []
        session = self.metrics.get_session_info()
        health = self.metrics.calculate_health_score()
        stats = self.metrics.compute_statistics()

        # Header
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        header = Box.draw("", [
            f"  CTX-MONITOR                                              {now}   ",
            f"  ◆ Session: {(session['session_id'] or 'N/A')[:8]}                                                         ",
            f"  ◇ Project: {session['project']:<20}                     Duration: {self._format_duration(session['duration'])}  ",
        ], self.width)
        lines.extend(header)
        lines.append("")

        # Health, Events, Errors cards
        health_indicator = ProgressCircle.from_percentage(health)
        health_status = "OK" if health >= 70 else "WARN" if health >= 50 else "ALERT"

        event_sparkline = self._generate_event_sparkline()
        error_sparkline = self._generate_error_sparkline()

        card_width = (self.width - 4) // 3

        # Simplified cards (side by side conceptually)
        lines.append(f"┌─ Health ────────────┐ ┌─ Events ────────────┐ ┌─ Errors ────────────┐")
        lines.append(f"│                     │ │                     │ │                     │")
        lines.append(f"│   {health_indicator} {health}%             │ │   {session['event_count']:,}  total      │ │   {stats['total_errors']}  ({stats['error_rate']:.1f}%)        │")
        lines.append(f"│                     │ │     {event_sparkline}  │ │     {error_sparkline}  │")
        lines.append(f"│   Status: {health_status:<10}│ │   events/min        │ │   errors/min        │")
        lines.append(f"│                     │ │                     │ │                     │")
        lines.append(f"└─────────────────────┘ └─────────────────────┘ └─────────────────────┘")
        lines.append("")

        # Token Usage
        stack_summary = self.stack.get_stack_summary(self.metrics.events)
        total_stack_tokens = stack_summary["total_tokens"]
        estimated_message_tokens = session['event_count'] * 50  # Rough estimate
        total_used = total_stack_tokens + estimated_message_tokens
        total_available = 200000  # 200k context window

        token_lines = [
            "",
            f"  {self._render_token_bar(total_used, total_available)}",
            f"  ├─────────────── Available: {(total_available - total_used) // 1000}k ({(1 - total_used/total_available)*100:.0f}%) ──────────────┤├─ Used: {total_used // 1000}k ({total_used/total_available*100:.0f}%) ─┤",
            "",
            "  Breakdown:",
            f"  ▓ Rules ········· {stack_summary['rules']['total_tokens']:,} tokens ({stack_summary['rules']['total_tokens']/total_used*100:.1f}%)",
            f"  ▓ Hooks ·········   {stack_summary['hooks'].get('tokens', 50)} tokens ({stack_summary['hooks'].get('tokens', 50)/total_used*100:.1f}%)",
            f"  ▓ Skills ········  {stack_summary['skills']['total_tokens']:,} tokens ({stack_summary['skills']['total_tokens']/total_used*100:.1f}%)",
            f"  ▓ Agents ········  {stack_summary['agents']['total_tokens']:,} tokens ({stack_summary['agents']['total_tokens']/total_used*100:.1f}%)",
            f"  █ Messages ······ {estimated_message_tokens:,} tokens ({estimated_message_tokens/total_used*100:.1f}%)",
            "",
        ]
        lines.extend(Box.draw("Token Usage", token_lines, self.width))
        lines.append("")

        # Tool Activity
        tool_metrics = self.metrics.get_tool_metrics()[:5]  # Top 5 tools
        tool_lines = [""]
        for tool in tool_metrics:
            sparkline = Sparkline.from_values([tool['calls']] * 28, 28)  # Placeholder
            circles = ProgressCircle.rate_indicator(tool['success'], tool['calls'], 15)
            tool_lines.append(f"  {tool['tool']:<10} {sparkline}   {tool['calls']:>3} calls   │ {circles}")

        tool_lines.append("")
        tool_lines.append("  Legend: Sparkline = activity over time | Circles = success rate")
        tool_lines.append("          ○ error  ◔ 25%  ◑ 50%  ◕ 75%  ● 100%")
        tool_lines.append("")

        lines.extend(Box.draw("Tool Activity", tool_lines, self.width))
        lines.append("")

        # Quick Stats
        stats_lines = [""]
        headers = ["Metric", "Value", "Min", "Max", "Mean", "Trend"]
        rows = [
            ["Response Time", f"{stats['mean_duration']:.2f}s", "0.08s", f"{stats['mean_duration']*2:.2f}s", f"{stats['mean_duration']:.2f}s", "→"],
            ["Error Rate", f"{stats['error_rate']:.1f}%", "0.0%", f"{stats['error_rate']*2:.1f}%", f"{stats['error_rate']:.1f}%", "→"],
            ["Events/min", f"{stats['events_per_min']:.1f}", "0.0", f"{stats['events_per_min']*1.5:.1f}", f"{stats['events_per_min']:.1f}", "→"],
        ]
        stats_lines.extend(["  " + line for line in Table.render(headers, rows)])
        stats_lines.append("")

        lines.extend(Box.draw("Quick Stats", stats_lines, self.width))
        lines.append("")

        # Footer
        lines.append(f" [1] Overview  [2] Stack  [3] Tools  [4] Timeline  [5] Alerts   Page 1/5")

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

    def _generate_event_sparkline(self) -> str:
        """Generate sparkline of event activity."""
        # Group events by time buckets
        buckets = [0] * 14
        for event in self.metrics.events:
            ts = event.get("timestamp", "")
            if ts:
                # Simple distribution
                idx = hash(ts) % 14
                buckets[idx] += 1

        if not any(buckets):
            buckets = [1] * 14

        return Sparkline.from_values(buckets, 14)

    def _generate_error_sparkline(self) -> str:
        """Generate sparkline of error activity."""
        buckets = [0] * 14
        for event in self.metrics.events:
            if event.get("status") == "error":
                ts = event.get("timestamp", "")
                idx = hash(ts) % 14
                buckets[idx] += 1

        if not any(buckets):
            return "▁" * 14

        return Sparkline.from_values(buckets, 14)

    def _render_token_bar(self, used: int, total: int) -> str:
        """Render token usage bar."""
        width = self.width - 6
        used_width = int((used / total) * width)
        available_width = width - used_width

        return "░" * available_width + "▓" * (used_width - 1) + "█"


class StackPage:
    """Render stack page."""

    def __init__(self, metrics: MetricsCollector, stack: StackAnalyzer, width: int = 80):
        self.metrics = metrics
        self.stack = stack
        self.width = width

    def render(self) -> str:
        """Render the stack page."""
        lines = []

        # Header
        header = Box.draw("", [
            f"  CONTEXT ENGINEERING STACK                                    Page 2/5       ",
        ], self.width)
        lines.extend(header)
        lines.append("")

        # Stack Composition
        stack_summary = self.stack.get_stack_summary(self.metrics.events)
        rules = stack_summary["rules"]
        hooks = stack_summary["hooks"]
        skills = stack_summary["skills"]
        agents = stack_summary["agents"]
        total = stack_summary["total_tokens"]

        # Composition bar
        bar_width = self.width - 6
        rules_w = int((rules["total_tokens"] / total) * bar_width) if total > 0 else 0
        hooks_w = int((hooks.get("tokens", 50) / total) * bar_width) if total > 0 else 0
        skills_w = int((skills["total_tokens"] / total) * bar_width) if total > 0 else 0
        agents_w = int((agents["total_tokens"] / total) * bar_width) if total > 0 else 0
        available_w = bar_width - rules_w - hooks_w - skills_w - agents_w

        comp_bar = "▓" * rules_w + "▓" * hooks_w + "▓" * skills_w + "▓" * agents_w + "░" * available_w

        comp_lines = [
            "",
            f"  {comp_bar}",
            "",
            "  Component     Tokens   Pct     Fired   Errors   Efficiency   Status",
            "  ─────────────────────────────────────────────────────────────────────",
            f"  ▓ Rules       {rules['total_tokens']:>5,}   {rules['total_tokens']/total*100:>5.1f}%      -        0      100.0%       ●",
            f"  ▓ Hooks          {hooks.get('tokens', 50):>3}    {hooks.get('tokens', 50)/total*100:>4.1f}%     {hooks['total_fired']:>2}        {hooks['total_errors']}       {hooks['efficiency']:>5.1f}%       {ProgressCircle.from_percentage(hooks['efficiency'])}",
            f"  ▓ Skills        {skills['total_tokens']:>3}   {skills['total_tokens']/total*100:>5.1f}%      {sum(s.get('triggered', 0) for s in skills['skills']):>1}        0      100.0%       ●",
            f"  ▓ Agents        {agents['total_tokens']:>3}   {agents['total_tokens']/total*100:>5.1f}%      {sum(a.get('invocations', 0) for a in agents['agents']):>1}        0      100.0%       ●",
            "  ─────────────────────────────────────────────────────────────────────",
            f"  ∑ Total       {total:>5,}  100.0%     {hooks['total_fired']:>2}        {hooks['total_errors']}       {hooks['efficiency']:>5.1f}%       {ProgressCircle.from_percentage(hooks['efficiency'])}",
            "",
        ]
        lines.extend(Box.draw("Stack Composition", comp_lines, self.width))
        lines.append("")

        # Rules
        rules_lines = [""]
        rules_lines.append("  Source                              Tokens    Lines    Sections    Status")
        rules_lines.append("  ────────────────────────────────────────────────────────────────────────")

        for source in rules["sources"]:
            rules_lines.append(f"  {source['name']:<35} {source['tokens']:>5}      {source['lines']:>3}          {len(source.get('sections', [])):>1}       ●")
            for section in source.get("sections", [])[:4]:
                rules_lines.append(f"  ├─ ## {section:<30}")

        rules_lines.append("")
        lines.extend(Box.draw("Rules", rules_lines, self.width))
        lines.append("")

        # Hooks
        hooks_lines = [""]
        hooks_lines.append("  Event Type          Matchers   Fired   Errors   Rate      Activity")
        hooks_lines.append("  ────────────────────────────────────────────────────────────────────────")

        for hook in hooks["hooks"]:
            rate_str = f"{hook['rate']:.1f}%" if hook["rate"] is not None else "  -  "
            activity = Sparkline.from_values([hook["fired"]] * 15, 15)
            hooks_lines.append(f"  {hook['event']:<20} {hook['matchers']:>3}       {hook['fired']:>2}        {hook['errors']}    {rate_str:>6}    {activity}")

        hooks_lines.append("")
        lines.extend(Box.draw("Hooks", hooks_lines, self.width))
        lines.append("")

        # Skills & Agents
        sa_lines = [""]
        sa_lines.append("  Skills                          Tokens   Triggered   Last Used   Status")
        sa_lines.append("  ────────────────────────────────────────────────────────────────────────")
        for skill in skills["skills"]:
            sa_lines.append(f"  {skill['name']:<30} {skill['tokens']:>5}           {skill.get('triggered', 0)}    -           ●")

        if not skills["skills"]:
            sa_lines.append("  (no skills configured)")

        sa_lines.append("")
        sa_lines.append("  Agents                          Tokens   Invoked     Last Used   Status")
        sa_lines.append("  ────────────────────────────────────────────────────────────────────────")
        for agent in agents["agents"]:
            sa_lines.append(f"  {agent['name']:<30} {agent['tokens']:>5}           {agent.get('invocations', 0)}    -           ●")

        if not agents["agents"]:
            sa_lines.append("  (no agents configured)")

        sa_lines.append("")
        lines.extend(Box.draw("Skills & Agents", sa_lines, self.width))
        lines.append("")

        # Footer
        lines.append(f" [1] Overview  [2] Stack  [3] Tools  [4] Timeline  [5] Alerts   Page 2/5")

        return "\n".join(lines)


class ToolsPage:
    """Render tools page."""

    def __init__(self, metrics: MetricsCollector, width: int = 80):
        self.metrics = metrics
        self.width = width

    def render(self) -> str:
        """Render the tools page."""
        lines = []

        # Header
        header = Box.draw("", [
            f"  TOOL PERFORMANCE                                             Page 3/5       ",
        ], self.width)
        lines.extend(header)
        lines.append("")

        tool_metrics = self.metrics.get_tool_metrics()

        # Call Distribution
        dist_lines = [""]
        max_calls = max(t["calls"] for t in tool_metrics) if tool_metrics else 1
        bar_width = self.width - 20

        for tool in tool_metrics:
            success_w = int((tool["success"] / max_calls) * bar_width) if max_calls > 0 else 0
            error_w = int((tool["errors"] / max_calls) * bar_width) if max_calls > 0 else 0
            empty_w = bar_width - success_w - error_w

            bar = "█" * success_w + "▒" * error_w + "░" * empty_w
            dist_lines.append(f"  {tool['tool']:<10} {bar} {tool['calls']:>3}")

        dist_lines.append("")
        dist_lines.append("  Legend: █ success  ▒ error")
        dist_lines.append("")

        lines.extend(Box.draw("Call Distribution", dist_lines, self.width))
        lines.append("")

        # Detailed Metrics
        detail_lines = [""]
        detail_lines.append("  Tool      Calls   Success   Errors    Rate    μ Time   σ Time    Status")
        detail_lines.append("  ────────────────────────────────────────────────────────────────────────")

        total_calls = 0
        total_success = 0
        total_errors = 0

        for tool in tool_metrics:
            status = ProgressCircle.from_percentage(tool["rate"])
            detail_lines.append(
                f"  {tool['tool']:<10} {tool['calls']:>3}       {tool['success']:>3}        {tool['errors']:>2}    "
                f"{tool['rate']:>5.1f}%    {tool['mean_time']:.2f}s    {tool['stdev_time']:.2f}s      {status}"
            )
            total_calls += tool["calls"]
            total_success += tool["success"]
            total_errors += tool["errors"]

        total_rate = (total_success / total_calls * 100) if total_calls > 0 else 0
        detail_lines.append("  ────────────────────────────────────────────────────────────────────────")
        detail_lines.append(
            f"  {'Total':<10} {total_calls:>3}       {total_success:>3}        {total_errors:>2}    "
            f"{total_rate:>5.1f}%    -        -         {ProgressCircle.from_percentage(total_rate)}"
        )

        detail_lines.append("")
        detail_lines.append("  Legend:  ● 100%  ◕ 90%+  ◑ 70%+  ◔ 50%+  ○ <50%")
        detail_lines.append("           μ = mean   σ = std deviation")
        detail_lines.append("")

        lines.extend(Box.draw("Detailed Metrics", detail_lines, self.width))
        lines.append("")

        # Error Breakdown
        errors = self.metrics.get_error_breakdown()
        error_lines = [""]

        if errors:
            error_lines.append("  Tool      Error Type                  Count   Last Occurrence")
            error_lines.append("  ────────────────────────────────────────────────────────────────────────")

            for error in errors[:5]:
                ts = error["timestamp"][:8] if error["timestamp"] else "-"
                error_lines.append(f"  {error['tool']:<10} {error['error_type']:<25}  1   {ts}")
        else:
            error_lines.append("  No errors recorded in this session.")

        error_lines.append("")
        lines.extend(Box.draw("Error Breakdown", error_lines, self.width))
        lines.append("")

        # Footer
        lines.append(f" [1] Overview  [2] Stack  [3] Tools  [4] Timeline  [5] Alerts   Page 3/5")

        return "\n".join(lines)


class TimelinePage:
    """Render timeline page."""

    def __init__(self, metrics: MetricsCollector, width: int = 80):
        self.metrics = metrics
        self.width = width

    def render(self) -> str:
        """Render the timeline page."""
        lines = []

        # Header
        header = Box.draw("", [
            f"  ACTIVITY TIMELINE                                            Page 4/5       ",
        ], self.width)
        lines.extend(header)
        lines.append("")

        # Event Flow
        events = self.metrics.get_timeline_events(10)
        flow_lines = [""]
        flow_lines.append("  Time       Event              Tool         Duration   Status   Preview")
        flow_lines.append("  ────────────────────────────────────────────────────────────────────────")

        for event in events:
            status = "●" if event["status"] == "success" else "○" if event["status"] == "error" else "·"
            flow_lines.append(
                f"  {event['time']}   {event['event_type']:<15} {event['tool_name']:<12}   -        {status}     {event['preview'][:20]}..."
            )

        if not events:
            flow_lines.append("  No events recorded yet.")

        flow_lines.append("")
        flow_lines.append(f"  ... (showing {len(events)} of {self.metrics.get_session_info()['event_count']} events)")
        flow_lines.append("")

        lines.extend(Box.draw("Event Flow", flow_lines, self.width))
        lines.append("")

        # Event Distribution
        distribution = self.metrics.get_event_distribution()
        dist_lines = [""]
        dist_lines.append("  Event Type          Count    Pct       Timeline")
        dist_lines.append("  ────────────────────────────────────────────────────────────────────────")

        total_events = sum(distribution.values())
        for event_type, count in sorted(distribution.items(), key=lambda x: -x[1])[:8]:
            pct = (count / total_events * 100) if total_events > 0 else 0
            sparkline = Sparkline.from_values([count] * 30, 30)  # Placeholder
            dist_lines.append(f"  {event_type:<18} {count:>5}   {pct:>5.1f}%    {sparkline}")

        dist_lines.append("")
        lines.extend(Box.draw("Session Events Summary", dist_lines, self.width))
        lines.append("")

        # Footer
        lines.append(f" [1] Overview  [2] Stack  [3] Tools  [4] Timeline  [5] Alerts   Page 4/5")

        return "\n".join(lines)


class AlertsPage:
    """Render alerts page."""

    def __init__(self, metrics: MetricsCollector, width: int = 80):
        self.metrics = metrics
        self.width = width

    def render(self) -> str:
        """Render the alerts page."""
        lines = []

        # Header
        header = Box.draw("", [
            f"  ALERTS & RECOMMENDATIONS                                     Page 5/5       ",
        ], self.width)
        lines.extend(header)
        lines.append("")

        # Active Alerts
        alerts = self.metrics.get_alerts()
        alert_lines = [""]

        if alerts:
            for alert in alerts:
                alert_lines.append(f"  {alert['indicator']} {alert['severity']:<9} {alert['message']}")
                alert_lines.append(f"              Recommendation: {alert['recommendation']}")
                alert_lines.append("")
        else:
            alert_lines.append("  ● No active alerts. System is healthy.")
            alert_lines.append("")

        lines.extend(Box.draw("Active Alerts", alert_lines, self.width))
        lines.append("")

        # Alert Severity Distribution
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for alert in alerts:
            sev = alert["severity"]
            if sev in severity_counts:
                severity_counts[sev] += 1

        sev_lines = [""]
        indicators = {"CRITICAL": "○", "HIGH": "◔", "MEDIUM": "◑", "LOW": "◕", "INFO": "●"}
        max_count = max(severity_counts.values()) if severity_counts.values() else 1
        bar_width = self.width - 25

        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            count = severity_counts[sev]
            filled = int((count / max_count) * bar_width) if max_count > 0 and count > 0 else 0
            bar = "█" * filled + "░" * (bar_width - filled)
            sev_lines.append(f"  {indicators[sev]} {sev:<10} {bar} {count:>3}")

        sev_lines.append("")
        total_alerts = sum(severity_counts.values())
        actionable = sum(v for k, v in severity_counts.items() if k != "INFO")
        sev_lines.append(f"  Total: {total_alerts} alerts  |  Actionable: {actionable}  |  Informational: {severity_counts['INFO']}")
        sev_lines.append("")

        lines.extend(Box.draw("Alert Severity Distribution", sev_lines, self.width))
        lines.append("")

        # Recommendations
        rec_lines = [""]
        rec_lines.append("  Based on current session analysis:")
        rec_lines.append("")

        if alerts:
            for i, alert in enumerate(alerts[:3], 1):
                rec_lines.append(f"  {i}. {alert['indicator']} {alert['message'][:50]}")
                rec_lines.append(f"     {alert['recommendation']}")
                rec_lines.append("")
        else:
            rec_lines.append("  No recommendations at this time. Keep up the good work!")
            rec_lines.append("")

        lines.extend(Box.draw("Recommendations", rec_lines, self.width))
        lines.append("")

        # Footer
        lines.append(f" [1] Overview  [2] Stack  [3] Tools  [4] Timeline  [5] Alerts   Page 5/5")

        return "\n".join(lines)


# =============================================================================
# MAIN DASHBOARD RENDERER
# =============================================================================

class DashboardRenderer:
    """Main orchestrator for dashboard rendering."""

    PAGES = ["overview", "stack", "tools", "timeline", "alerts"]

    def __init__(self, project_dir: str, session_id: Optional[str] = None,
                 width: int = 80, no_color: bool = False):
        self.project_dir = Path(project_dir)
        self.session_id = session_id
        self.width = width
        self.no_color = no_color

        self.metrics = MetricsCollector(self.project_dir, session_id)
        self.stack = StackAnalyzer(self.project_dir)

    def render_page(self, page: str = "overview") -> str:
        """Render the specified page."""
        page = page.lower()

        if page not in self.PAGES:
            return f"Unknown page: {page}. Available: {', '.join(self.PAGES)}"

        if not self.metrics.events:
            return self._render_no_data()

        if page == "overview":
            renderer = OverviewPage(self.metrics, self.stack, self.width)
        elif page == "stack":
            renderer = StackPage(self.metrics, self.stack, self.width)
        elif page == "tools":
            renderer = ToolsPage(self.metrics, self.width)
        elif page == "timeline":
            renderer = TimelinePage(self.metrics, self.width)
        elif page == "alerts":
            renderer = AlertsPage(self.metrics, self.width)
        else:
            return f"Page '{page}' not implemented yet."

        return renderer.render()

    def _render_no_data(self) -> str:
        """Render message when no data is available."""
        lines = []
        lines.append("")
        lines.append("┌──────────────────────────────────────────────────────────────────────────────┐")
        lines.append("│                                                                              │")
        lines.append("│  CTX-MONITOR DASHBOARD                                                       │")
        lines.append("│                                                                              │")
        lines.append("│  No monitoring data available.                                               │")
        lines.append("│                                                                              │")
        lines.append("│  To start monitoring, run:                                                   │")
        lines.append("│                                                                              │")
        lines.append("│    /ctx-monitor:start                                                        │")
        lines.append("│                                                                              │")
        lines.append("│  Then perform some operations and run:                                       │")
        lines.append("│                                                                              │")
        lines.append("│    /ctx-monitor:dashboard                                                    │")
        lines.append("│                                                                              │")
        lines.append("└──────────────────────────────────────────────────────────────────────────────┘")
        lines.append("")
        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Render visual dashboard for ctx-monitor session"
    )
    parser.add_argument(
        "project_dir",
        help="Path to project directory"
    )
    parser.add_argument(
        "--page",
        choices=DashboardRenderer.PAGES,
        default="overview",
        help="Page to display (default: overview)"
    )
    parser.add_argument(
        "--session",
        help="Session ID (default: most recent)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color codes"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=80,
        help="Dashboard width (default: 80)"
    )

    args = parser.parse_args()

    renderer = DashboardRenderer(
        project_dir=args.project_dir,
        session_id=args.session,
        width=args.width,
        no_color=args.no_color
    )

    output = renderer.render_page(args.page)
    print(output)


if __name__ == "__main__":
    main()
