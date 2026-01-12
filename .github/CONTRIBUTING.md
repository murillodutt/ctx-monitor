# Contributing to ctx-monitor

Thank you for your interest in contributing! This guide will help you get started.

## Project Philosophy
- **Clean Root**: Keep the repository root organized. Supporting documentation belongs in `.github/` or `docs/`.
- **Transparency**: Technical decisions are demand-driven and publicly recorded.
- **Security**: Never include sensitive data in traces or tests.

## Getting Started
1. **Environment**:
   - Python 3.7+
   - Node.js (if working on UI tools)
   - Claude Code CLI installed.
2. **Development**:
   - Create a branch for your changes: `git checkout -b feature/my-improvement`.
   - Follow the Semantic Commits standard (e.g., `feat:`, `fix:`, `docs:`).

## Code Standards
- **Bash**: Use `ShellCheck` for scripts in `plugins/ctx-monitor/scripts/`.
- **Python**: Use `Ruff` for linting and formatting.
- **Documentation**: Use English for all global documentation and code comments.

## Pull Request Process
1. Ensure the PR passes all local tests.
2. Update `README.md` or relevant docs if necessary.
3. Request a review from one of the maintainers.
