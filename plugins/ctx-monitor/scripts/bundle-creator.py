#!/usr/bin/env python3
"""
bundle-creator.py - Create diagnostic bundles for sharing/support

Usage:
    python bundle-creator.py --project-dir <dir> [--output <bundle.zip>] [--anonymize] [--include-config]
"""

import json
import sys
import os
import argparse
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess


def get_session_summary(traces_dir: Path) -> List[Dict[str, Any]]:
    """Get summary of all sessions."""
    sessions_file = traces_dir / "sessions.json"
    if sessions_file.exists():
        try:
            content = sessions_file.read_text().strip()
            if not content:
                return []
            data = json.loads(content)
            return data.get("sessions", [])
        except (json.JSONDecodeError, KeyError):
            return []
    return []


def collect_traces(traces_dir: Path, max_sessions: int = 10) -> List[Path]:
    """Collect recent trace files."""
    trace_files = list(traces_dir.glob("session_*.jsonl"))
    trace_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return trace_files[:max_sessions]


def collect_config(project_dir: Path, anonymize: bool = True) -> Dict[str, Any]:
    """Collect Claude Code configuration (with optional anonymization)."""
    config = {
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "files": {}
    }

    # Files to collect
    config_files = [
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".claude/ctx-monitor.local.md",
        "CLAUDE.md",
        ".claudeignore"
    ]

    for config_file in config_files:
        file_path = project_dir / config_file
        if file_path.exists():
            try:
                content = file_path.read_text()

                if anonymize:
                    # Basic anonymization for config files
                    import re
                    # Redact API keys
                    content = re.sub(r'(api[_-]?key\s*[=:]\s*)["\']?[\w\-]+["\']?',
                                   r'\1[REDACTED]', content, flags=re.IGNORECASE)
                    # Redact tokens
                    content = re.sub(r'(token\s*[=:]\s*)["\']?[\w\-]+["\']?',
                                   r'\1[REDACTED]', content, flags=re.IGNORECASE)
                    # Redact passwords
                    content = re.sub(r'(password\s*[=:]\s*)["\']?[^\s"\']+["\']?',
                                   r'\1[REDACTED]', content, flags=re.IGNORECASE)
                    # Redact secrets
                    content = re.sub(r'(secret\s*[=:]\s*)["\']?[\w\-]+["\']?',
                                   r'\1[REDACTED]', content, flags=re.IGNORECASE)

                config["files"][config_file] = content
            except Exception as e:
                config["files"][config_file] = f"[Error reading: {e}]"

    return config


def get_environment_info() -> Dict[str, Any]:
    """Collect environment information (non-sensitive)."""
    import platform

    env_info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "python_version": platform.python_version(),
        "cwd": os.getcwd()
    }

    # Check for common tools
    tools = ["claude", "node", "npm", "python3", "git"]
    env_info["installed_tools"] = {}

    for tool in tools:
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0][:100]  # First line, max 100 chars
                env_info["installed_tools"][tool] = version
        except:
            pass

    return env_info


def generate_report(traces_dir: Path, sessions: List[Dict[str, Any]]) -> str:
    """Generate a summary report."""
    lines = []
    lines.append("# CTX-Monitor Diagnostic Bundle Report")
    lines.append(f"\nGenerated: {datetime.utcnow().isoformat()}Z\n")

    lines.append("## Sessions Summary\n")
    lines.append(f"Total sessions found: {len(sessions)}\n")

    if sessions:
        lines.append("| Session ID | Started | Events |")
        lines.append("|------------|---------|--------|")
        for session in sessions[:10]:
            lines.append(f"| {session.get('session_id', 'N/A')[:20]}... | "
                        f"{session.get('started_at', 'N/A')[:19]} | "
                        f"{session.get('event_count', 0)} |")

    lines.append("\n## Quick Analysis\n")

    # Analyze recent traces
    trace_files = list(traces_dir.glob("session_*.jsonl"))
    if trace_files:
        total_events = 0
        total_errors = 0

        for trace_file in trace_files[:5]:
            try:
                with open(trace_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            event = json.loads(line)
                            total_events += 1
                            if event.get("status") == "error":
                                total_errors += 1
            except:
                pass

        error_rate = (total_errors / total_events * 100) if total_events > 0 else 0
        lines.append(f"- Recent events analyzed: {total_events}")
        lines.append(f"- Errors found: {total_errors}")
        lines.append(f"- Error rate: {error_rate:.1f}%")
    else:
        lines.append("- No trace files found")

    lines.append("\n## Bundle Contents\n")
    lines.append("- `traces/` - Session trace files (JSONL)")
    lines.append("- `config.json` - Configuration snapshot (anonymized)")
    lines.append("- `environment.json` - Environment information")
    lines.append("- `report.md` - This summary report")

    return "\n".join(lines)


def create_bundle(
    project_dir: str,
    output_path: Optional[str] = None,
    anonymize: bool = True,
    include_config: bool = True,
    max_sessions: int = 10
) -> str:
    """Create the diagnostic bundle."""
    project_path = Path(project_dir)
    traces_dir = project_path / ".claude" / "ctx-monitor" / "traces"

    if not traces_dir.exists():
        raise ValueError(f"Traces directory not found: {traces_dir}")

    # Create temp directory for bundle contents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        bundle_dir = temp_path / "ctx-monitor-bundle"
        bundle_dir.mkdir()

        # 1. Copy traces
        traces_bundle_dir = bundle_dir / "traces"
        traces_bundle_dir.mkdir()

        trace_files = collect_traces(traces_dir, max_sessions)
        for trace_file in trace_files:
            if anonymize:
                # Anonymize trace content
                try:
                    result = subprocess.run(
                        ["python3", str(Path(__file__).parent / "anonymizer.py"), str(trace_file)],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        (traces_bundle_dir / trace_file.name).write_text(result.stdout)
                    else:
                        shutil.copy(trace_file, traces_bundle_dir / trace_file.name)
                except:
                    shutil.copy(trace_file, traces_bundle_dir / trace_file.name)
            else:
                shutil.copy(trace_file, traces_bundle_dir / trace_file.name)

        # Copy sessions index
        sessions_file = traces_dir / "sessions.json"
        if sessions_file.exists():
            shutil.copy(sessions_file, traces_bundle_dir / "sessions.json")

        # 2. Collect config (if requested)
        if include_config:
            config = collect_config(project_path, anonymize=anonymize)
            (bundle_dir / "config.json").write_text(json.dumps(config, indent=2))

        # 3. Environment info
        env_info = get_environment_info()
        (bundle_dir / "environment.json").write_text(json.dumps(env_info, indent=2))

        # 4. Generate report
        sessions = get_session_summary(traces_dir)
        report = generate_report(traces_dir, sessions)
        (bundle_dir / "report.md").write_text(report)

        # 5. Create zip
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"ctx-monitor-bundle_{timestamp}.zip"

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in bundle_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(bundle_dir)
                    zipf.write(file_path, arcname)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Create ctx-monitor diagnostic bundle")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--output", "-o", help="Output zip file path")
    parser.add_argument("--anonymize", action="store_true", default=True,
                        help="Anonymize sensitive data (default: true)")
    parser.add_argument("--no-anonymize", action="store_true",
                        help="Disable anonymization")
    parser.add_argument("--include-config", action="store_true", default=True,
                        help="Include configuration files")
    parser.add_argument("--no-config", action="store_true",
                        help="Exclude configuration files")
    parser.add_argument("--max-sessions", type=int, default=10,
                        help="Maximum number of sessions to include")
    args = parser.parse_args()

    anonymize = not args.no_anonymize
    include_config = not args.no_config

    try:
        output = create_bundle(
            project_dir=args.project_dir,
            output_path=args.output,
            anonymize=anonymize,
            include_config=include_config,
            max_sessions=args.max_sessions
        )
        print(f"Bundle created: {output}")
    except Exception as e:
        print(f"Error creating bundle: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
