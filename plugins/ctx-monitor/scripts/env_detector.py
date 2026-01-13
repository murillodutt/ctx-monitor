#!/usr/bin/env python3
"""
env_detector.py - Cross-platform environment detection for ctx-monitor

Detects OS, Python command, shell, and other environment details to ensure
100% compatibility across macOS, Windows, and Linux systems.

Usage:
    python env_detector.py [--save <path>] [--json]
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class EnvironmentDetector:
    """Detect and configure environment for cross-platform compatibility."""

    def __init__(self):
        self.os_type = self._detect_os()
        self.python_cmd = self._detect_python()
        self.shell = self._detect_shell()
        self.path_separator = ";" if self.os_type == "windows" else ":"

    def _detect_os(self) -> str:
        """Detect operating system type."""
        import platform
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        return "unknown"

    def _detect_python(self) -> str:
        """Detect the correct Python command for this system."""
        candidates = ["python3", "python", "py"]

        for cmd in candidates:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_str = result.stdout.strip() or result.stderr.strip()
                    if "Python 3" in version_str:
                        return cmd
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                continue

        # Fallback based on OS
        return "python" if self.os_type == "windows" else "python3"

    def _detect_shell(self) -> str:
        """Detect the user's shell."""
        if self.os_type == "windows":
            return os.environ.get("COMSPEC", "cmd.exe")
        shell = os.environ.get("SHELL", "/bin/bash")
        return Path(shell).name

    def get_env_info(self) -> Dict[str, str]:
        """Get complete environment information."""
        import platform
        return {
            "os_type": self.os_type,
            "os_name": {"macos": "macOS", "windows": "Windows", "linux": "Linux"}.get(self.os_type, "Unknown"),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "python_cmd": self.python_cmd,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_path": sys.executable,
            "shell": self.shell,
            "home_dir": str(Path.home()),
            "path_separator": self.path_separator,
            "architecture": platform.machine(),
            "detected_at": datetime.now().isoformat(),
        }

    def verify_python(self) -> tuple:
        """Verify Python is working correctly. Returns (success, message)."""
        try:
            result = subprocess.run(
                [self.python_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                return True, f"{self.python_cmd} ({version})"
            return False, f"Command '{self.python_cmd}' failed"
        except Exception as e:
            return False, f"Cannot execute Python: {e}"

    def save_config(self, config_path: Path) -> bool:
        """Save environment configuration to file."""
        try:
            config_path.write_text(json.dumps(self.get_env_info(), indent=2))
            return True
        except Exception:
            return False

    @staticmethod
    def load_config(config_path: Path) -> Optional[Dict[str, str]]:
        """Load saved environment configuration."""
        try:
            if config_path.exists():
                return json.loads(config_path.read_text())
        except Exception:
            pass
        return None

    def print_report(self):
        """Print environment report to console."""
        info = self.get_env_info()

        print()
        print("=" * 60)
        print("  CTX-MONITOR ENVIRONMENT DETECTION")
        print("=" * 60)
        print()
        print(f"  Operating System:  {info['os_name']}")
        print(f"  OS Version:        {info['os_release']}")
        print(f"  Architecture:      {info['architecture']}")
        print()
        print(f"  Python Command:    {info['python_cmd']}")
        print(f"  Python Version:    {info['python_version']}")
        print(f"  Python Path:       {info['python_path']}")
        print()
        print(f"  Shell:             {info['shell']}")
        print(f"  Home Directory:    {info['home_dir']}")
        print()
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect environment for ctx-monitor")
    parser.add_argument("--save", help="Save config to specified path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    detector = EnvironmentDetector()

    if args.json:
        print(json.dumps(detector.get_env_info(), indent=2))
    else:
        detector.print_report()

    if args.save:
        save_path = Path(args.save)
        if detector.save_config(save_path):
            print(f"\nConfiguration saved to: {save_path}")
        else:
            print(f"\nFailed to save configuration to: {save_path}")
            sys.exit(1)


if __name__ == "__main__":
    main()
