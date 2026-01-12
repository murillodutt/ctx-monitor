#!/usr/bin/env python3
"""
anonymizer.py - Anonymize sensitive data in ctx-monitor traces

Usage:
    python anonymizer.py <input_file.jsonl> [--output <output_file.jsonl>] [--patterns <patterns.json>]
"""

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Pattern
import hashlib


# Default patterns to anonymize
DEFAULT_PATTERNS = [
    # API keys and tokens
    r'(api[_-]?key\s*[=:]\s*)["\']?[\w\-]{20,}["\']?',
    r'(token\s*[=:]\s*)["\']?[\w\-]{20,}["\']?',
    r'(bearer\s+)[\w\-\.]+',
    r'(authorization\s*[=:]\s*)["\']?[\w\-\.]+["\']?',

    # Passwords and secrets
    r'(password\s*[=:]\s*)["\']?[^\s"\']+["\']?',
    r'(secret\s*[=:]\s*)["\']?[\w\-]{10,}["\']?',
    r'(private[_-]?key\s*[=:]\s*)["\']?[\w\-]+["\']?',

    # AWS credentials
    r'AKIA[0-9A-Z]{16}',
    r'(aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*)["\']?[\w/+=]+["\']?',

    # Database connection strings
    r'(mongodb(\+srv)?://)[^@]+@',
    r'(postgres(ql)?://)[^@]+@',
    r'(mysql://)[^@]+@',
    r'(redis://)[^@]+@',

    # Email addresses (optional - can be noisy)
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',

    # IP addresses (internal)
    r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
    r'\b(172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3})\b',
    r'\b(192\.168\.\d{1,3}\.\d{1,3})\b',

    # File paths with usernames
    r'/Users/[^/\s]+',
    r'/home/[^/\s]+',
    r'C:\\Users\\[^\\]+',
]


def compile_patterns(patterns: List[str]) -> List[Pattern]:
    """Compile regex patterns."""
    compiled = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.IGNORECASE))
        except re.error as e:
            print(f"Warning: Invalid pattern '{pattern}': {e}", file=sys.stderr)
    return compiled


def hash_value(value: str) -> str:
    """Generate a consistent short hash for a value."""
    return hashlib.sha256(value.encode()).hexdigest()[:8]


def anonymize_string(text: str, patterns: List[Pattern], preserve_structure: bool = True) -> str:
    """Anonymize sensitive data in a string."""
    if not text:
        return text

    result = text

    for pattern in patterns:
        def replace_match(match):
            full_match = match.group(0)
            # If pattern has groups, preserve prefix
            if match.lastindex:
                prefix = match.group(1)
                sensitive_part = full_match[len(prefix):]
                if preserve_structure:
                    return f"{prefix}[REDACTED:{hash_value(sensitive_part)}]"
                return f"{prefix}[REDACTED]"
            else:
                if preserve_structure:
                    return f"[REDACTED:{hash_value(full_match)}]"
                return "[REDACTED]"

        result = pattern.sub(replace_match, result)

    return result


def anonymize_value(value: Any, patterns: List[Pattern]) -> Any:
    """Recursively anonymize values in a data structure."""
    if isinstance(value, str):
        return anonymize_string(value, patterns)
    elif isinstance(value, dict):
        return {k: anonymize_value(v, patterns) for k, v in value.items()}
    elif isinstance(value, list):
        return [anonymize_value(item, patterns) for item in value]
    else:
        return value


def anonymize_event(event: Dict[str, Any], patterns: List[Pattern]) -> Dict[str, Any]:
    """Anonymize a single event."""
    # Fields to anonymize
    sensitive_fields = [
        'args_preview',
        'result_preview',
        'error_message',
        'tool_input',
        'tool_result',
        'cwd'
    ]

    anonymized = event.copy()

    for field in sensitive_fields:
        if field in anonymized:
            anonymized[field] = anonymize_value(anonymized[field], patterns)

    return anonymized


def load_custom_patterns(patterns_file: str) -> List[str]:
    """Load custom patterns from a JSON file."""
    with open(patterns_file, 'r') as f:
        data = json.load(f)
        return data.get('patterns', [])


def main():
    parser = argparse.ArgumentParser(description="Anonymize sensitive data in ctx-monitor traces")
    parser.add_argument("input", help="Input JSONL file")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--patterns", "-p", help="Custom patterns JSON file")
    parser.add_argument("--no-default-patterns", action="store_true", help="Don't use default patterns")
    parser.add_argument("--preserve-structure", action="store_true", default=True,
                        help="Preserve structure with hashed placeholders")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Build pattern list
    patterns = []
    if not args.no_default_patterns:
        patterns.extend(DEFAULT_PATTERNS)

    if args.patterns:
        try:
            custom = load_custom_patterns(args.patterns)
            patterns.extend(custom)
        except Exception as e:
            print(f"Warning: Could not load custom patterns: {e}", file=sys.stderr)

    compiled_patterns = compile_patterns(patterns)

    # Process input file
    output_lines = []
    with open(args.input, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    event = json.loads(line)
                    anonymized = anonymize_event(event, compiled_patterns)
                    output_lines.append(json.dumps(anonymized))
                except json.JSONDecodeError:
                    # Keep non-JSON lines as-is but anonymize
                    output_lines.append(anonymize_string(line, compiled_patterns))

    # Output
    output_text = "\n".join(output_lines)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
        print(f"Anonymized output written to: {args.output}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == "__main__":
    main()
