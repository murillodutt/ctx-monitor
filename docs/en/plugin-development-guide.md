# Claude Code Plugin Development Guide

Complete manual for developing plugins for Claude Code CLI.

**Based on:** claude-plugins-official (Anthropic) + official plugin-dev
**Version:** 0.3.5
**Last updated:** 2026-01-12

---

## Table of Contents

1. [Directory Architecture](#1-directory-architecture)
2. [Marketplace Structure (GitHub)](#2-marketplace-structure-github)
3. [Plugin Structure](#3-plugin-structure)
4. [Commands (Slash Commands)](#4-commands-slash-commands)
5. [Agents](#5-agents)
6. [Skills](#6-skills)
7. [Hooks](#7-hooks)
8. [MCP Servers](#8-mcp-servers)
9. [Local Configuration Files](#9-local-configuration-files)
10. [Installation Process](#10-installation-process)
11. [Progressive Disclosure](#11-progressive-disclosure)
12. [Best Practices](#12-best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [Checklist](#14-checklist)

---

## 1. Directory Architecture

Claude Code uses three main directories to manage plugins:

```
~/.claude/plugins/
├── known_marketplaces.json    # Marketplace registry
├── installed_plugins.json     # Installed plugins registry
├── marketplaces/              # Cloned repositories
│   ├── claude-plugins-official/
│   └── your-marketplace/
└── cache/                     # Extracted plugins (used at runtime)
    ├── claude-plugins-official/
    │   ├── hookify/<commit-sha>/
    │   └── plugin-dev/<commit-sha>/
    └── your-marketplace/
        └── your-plugin/<commit-sha>/
```

### Installation Flow

1. **Marketplace is registered** in `known_marketplaces.json`
2. **Repository is cloned** to `marketplaces/<name>/`
3. **Plugin is extracted** to `cache/<marketplace>/<plugin>/<version>/`
4. **Plugin is registered** in `installed_plugins.json`

---

## 2. Marketplace Structure (GitHub)

A marketplace is a GitHub repository that contains multiple plugins.

### Official Structure

```
marketplace-name/
├── .claude-plugin/
│   └── marketplace.json       # ONLY this file here!
├── plugins/                   # Internal plugins
│   ├── plugin-a/
│   └── plugin-b/
├── external_plugins/          # Third-party plugins (optional)
├── LICENSE
└── README.md
```

### IMPORTANT: Marketplace Root

In the `.claude-plugin/` folder at the **repository root**:
- marketplace.json - MUST exist
- plugin.json - MUST NOT exist here!

### marketplace.json

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "your-marketplace",
  "description": "Marketplace description",
  "owner": {
    "name": "Your Name",
    "email": "email@example.com"
  },
  "plugins": [
    {
      "name": "your-plugin",
      "description": "Plugin description",
      "version": "1.0.0",
      "author": {
        "name": "Your Name",
        "email": "email@example.com"
      },
      "source": "./plugins/your-plugin",
      "category": "development",
      "homepage": "https://github.com/user/repo",
      "tags": ["community-managed"]
    }
  ]
}
```

### marketplace.json Field Reference

#### Root Level Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `$schema` | No | string | JSON schema URL for validation |
| `name` | **Yes** | string | Unique marketplace identifier |
| `description` | **Yes** | string | Brief marketplace description |
| `owner` | **Yes** | object | Marketplace owner information |
| `plugins` | **Yes** | array | List of plugin definitions |

#### Owner Object

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | **Yes** | string | Owner/organization name |
| `email` | **Yes** | string | Contact email |

#### Plugin Entry Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | **Yes** | string | Plugin identifier (kebab-case) |
| `description` | **Yes** | string | Plugin functionality overview |
| `author` | **Yes** | object | Plugin creator (name, email) |
| `source` | **Yes** | string/object | Plugin location (path or URL object) |
| `category` | **Yes** | string | Classification category |
| `version` | No | string | Semantic version (e.g., "1.0.0") |
| `homepage` | No | string | Project homepage/repository URL |
| `tags` | No | array | Labels (e.g., "community-managed") |
| `strict` | No | boolean | Strictness enforcement flag |
| `lspServers` | No | object | Language Server Protocol config |

#### Available Categories

- `development` - Development tools and workflows
- `productivity` - Productivity enhancements
- `security` - Security tools and guidance
- `learning` - Educational resources
- `testing` - Testing utilities
- `database` - Database tools
- `design` - Design utilities
- `deployment` - Deployment automation
- `monitoring` - Monitoring and observability

#### Source Formats

**Path reference (recommended for internal plugins):**
```json
"source": "./plugins/your-plugin"
```

**URL object (for external repositories):**
```json
"source": {
  "source": "url",
  "url": "https://github.com/user/repo.git"
}
```

#### LSP Server Configuration (Optional)

For plugins that provide Language Server Protocol integration:

```json
"lspServers": {
  "server-name": {
    "command": "executable-name",
    "args": ["--arg1", "--arg2"],
    "extensionToLanguage": {
      ".ext": "language-id"
    },
    "startupTimeout": 5000
  }
}
```

---

## 3. Plugin Structure

Based on the official example-plugin and plugin-dev from Anthropic.

### Complete Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        # Plugin metadata (REQUIRED)
├── .mcp.json              # MCP server configuration (optional)
├── commands/              # Slash commands (optional)
│   └── command-name.md
├── agents/                # Agent definitions (optional)
│   └── agent-name.md
├── skills/                # Skill definitions (optional)
│   └── skill-name/
│       ├── SKILL.md       # Required for each skill
│       ├── references/    # Detailed documentation
│       ├── examples/      # Working examples
│       └── scripts/       # Utility scripts
├── hooks/                 # Hook definitions (optional)
│   ├── hooks.json
│   └── scripts/
├── scripts/               # Shared utilities
└── README.md              # Documentation (REQUIRED)
```

### Critical Rules

1. **Manifest location**: `plugin.json` MUST be in `.claude-plugin/`
2. **Component location**: All directories (commands, agents, skills, hooks) MUST be at the plugin root, NOT inside `.claude-plugin/`
3. **Optional components**: Create only directories for components the plugin uses
4. **Naming convention**: Use kebab-case for all directories and files

### plugin.json

Location: `.claude-plugin/plugin.json`

#### Minimal Example (Official Anthropic Pattern)

```json
{
  "name": "your-plugin",
  "description": "Plugin description",
  "author": {
    "name": "Your Name",
    "email": "email@example.com"
  }
}
```

#### Extended Example (With Optional Fields)

```json
{
  "name": "your-plugin",
  "description": "Plugin description",
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "email@example.com"
  }
}
```

### plugin.json Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | **Yes** | string | Plugin identifier (kebab-case). Defines command namespace. |
| `description` | **Yes** | string | Brief plugin functionality description |
| `author` | **Yes** | object | Plugin creator information |
| `version` | No | string | Semantic version (e.g., "1.0.0") |

#### Author Object

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | **Yes** | string | Author/organization name |
| `email` | **Yes** | string | Contact email |

> **Note:** Official Anthropic plugins use only `name`, `description`, and `author`. The `version` field is optional but recommended for tracking releases.

### Namespace Behavior

The `name` field defines the **namespace** of commands:
- `name: "ctx-monitor"` -> commands appear as `/ctx-monitor:*`

---

## 4. Commands (Slash Commands)

Location: `commands/*.md`

### CRITICAL: Commands are Instructions FOR Claude

**Commands are written for agent consumption, not for humans.**

When a user invokes `/command-name`, the command content becomes Claude's instructions. Write commands as directives FOR Claude about what to do.

**Correct approach (instructions for Claude):**
```markdown
Review this code for security vulnerabilities including:
- SQL injection
- XSS attacks
- Authentication issues

Provide specific line numbers and severity ratings.
```

**Incorrect approach (messages for user):**
```markdown
This command will review your code for security issues.
You will receive a report with vulnerability details.
```

### Official Format

```yaml
---
description: Short description for /help
argument-hint: <required-arg> [optional-arg]
allowed-tools: [Read, Glob, Grep, Bash]
model: sonnet
---
```

### Frontmatter Options

| Field | Description |
|-------|-------------|
| `description` | Short description shown in /help |
| `argument-hint` | Argument hints shown to user |
| `allowed-tools` | Pre-approved tools (reduces permission prompts) |
| `model` | Model override: "haiku", "sonnet", "opus" |
| `disable-model-invocation` | Prevent programmatic invocation |

### CRITICAL: DO NOT Use `name` Field

```yaml
# WRONG - overrides automatic namespace
---
name: start
description: Start monitoring
---
# Result: /start (no namespace!)

# CORRECT - uses plugin.json namespace
---
description: Start monitoring
---
# Result: /your-plugin:start
```

### Dynamic Arguments

#### Using $ARGUMENTS

```markdown
---
description: Fix issue by number
argument-hint: [issue-number]
---

Fix issue #$ARGUMENTS following our coding standards.
```

**Usage:** `/fix-issue 123` -> "Fix issue #123 following..."

#### Using Positional Arguments

```markdown
---
description: Review PR with priority and assignee
argument-hint: [pr-number] [priority] [assignee]
---

Review pull request #$1 with priority level $2.
After review, assign to $3 for follow-up.
```

**Usage:** `/review-pr 123 high alice`

### File References

```markdown
---
description: Review specific file
argument-hint: [file-path]
---

Review @$1 for:
- Code quality
- Best practices
- Potential bugs
```

**Usage:** `/review-file src/api/users.ts`

### Bash Execution in Commands

```markdown
---
description: Review code changes
allowed-tools: Read, Bash(git:*)
---

Files changed: !`git diff --name-only`

Review each file for code quality.
```

### ${CLAUDE_PLUGIN_ROOT}

Use to reference plugin files in a portable way:

```markdown
---
description: Analyze using plugin script
allowed-tools: Bash(node:*)
---

Run analysis: !`node ${CLAUDE_PLUGIN_ROOT}/scripts/analyze.js $1`
```

---

## 5. Agents

Location: `agents/*.md`

Agents are autonomous subprocesses that handle complex, multi-step tasks independently.

### Complete Format

```markdown
---
name: agent-identifier
description: Use this agent when [triggering conditions]. Examples:

<example>
Context: [Situation description]
user: "[User request]"
assistant: "[How assistant should respond and use this agent]"
<commentary>
[Why this agent should be triggered]
</commentary>
</example>

model: inherit
color: blue
tools: ["Read", "Write", "Grep"]
---

You are [agent role description]...

**Your Core Responsibilities:**
1. [Responsibility 1]
2. [Responsibility 2]

**Analysis Process:**
[Step-by-step workflow]

**Output Format:**
[What to return]
```

### Frontmatter Fields

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| name | Yes | lowercase-hyphens (3-50 chars) | code-reviewer |
| description | Yes | Text + examples | Use when... <example>... |
| model | Yes | inherit/sonnet/opus/haiku | inherit |
| color | Yes | Color name | blue, cyan, green, yellow, magenta, red |
| tools | No | Array of tool names | ["Read", "Grep"] |

### Identifier Validation

```
Valid: code-reviewer, test-gen, api-analyzer-v2
Invalid: ag (too short), -start (starts with hyphen), my_agent (underscore)
```

**Rules:**
- 3-50 characters
- Only lowercase letters, numbers, hyphens
- Must start and end with alphanumeric

### Colors and Usage

| Color | Recommended Use |
|-------|-----------------|
| blue/cyan | Analysis, review |
| green | Success-oriented tasks |
| yellow | Caution, validation |
| red | Critical, security |
| magenta | Creative, generation |

### System Prompt Design

**DO:**
- Write in second person ("You are...", "You will...")
- Be specific about responsibilities
- Provide step-by-step process
- Define output format
- Include quality standards
- Keep below 10,000 characters

**DON'T:**
- Write in first person ("I am...", "I will...")
- Be vague or generic
- Omit process steps
- Leave output format undefined

---

## 6. Skills

Location: `skills/<name>/SKILL.md`

Skills are modular, self-contained packages that extend Claude's capabilities by providing specialized knowledge.

### Skill Anatomy

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation to load as needed
    ├── examples/         - Working examples
    └── assets/           - Files for output (templates, icons, fonts)
```

### Skill Frontmatter

```yaml
---
name: Skill Name
description: This skill should be used when the user asks to "specific phrase 1", "specific phrase 2", or mentions "keyword". Include exact phrases users would say.
version: 1.0.0
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | **Yes** | Skill identifier |
| `description` | **Yes** | Activation conditions - when Claude should use it |
| `version` | No | Semantic version |

### Writing Effective Descriptions

The description is crucial - it tells Claude when to invoke the skill.

**Good example:**
```yaml
description: This skill should be used when the user asks to "create a hook", "add a PreToolUse hook", "validate tool use", or mentions hook events (PreToolUse, PostToolUse, Stop).
```

**Bad example:**
```yaml
description: Use this skill when working with hooks.  # Wrong person, vague
description: Provides hook guidance.  # No trigger phrases
```

**Important:** Use third person ("This skill should be used when...") and include specific phrases users would say.

### Bundled Resources

#### scripts/
Executable code for tasks requiring deterministic reliability.

**When to include:** When the same code is rewritten repeatedly or deterministic reliability is needed.

#### references/
Documentation and reference material to load as needed into context.

**When to include:** For documentation Claude should reference while working.
**Best practice:** If files are large (>10k words), include grep search patterns in SKILL.md.

#### examples/
Working code examples that users can copy and adapt.

#### assets/
Files not intended to load into context, but used in output (templates, images, boilerplate).

### Writing Style

**SKILL.md body:** Write using **imperative/infinitive form** (verb-first instructions), not second person.

**Correct (imperative):**
```
To create a hook, define the event type.
Configure the MCP server with authentication.
Validate settings before use.
```

**Incorrect (second person):**
```
You should create a hook by defining the event type.
You need to configure the MCP server.
```

---

## 7. Hooks

Location: `hooks/hooks.json`

Hooks are event-driven automation scripts that execute in response to Claude Code events.

### Hook Types

#### Prompt-Based Hooks (Recommended)

Uses LLM-driven decision making for context-aware validation:

```json
{
  "type": "prompt",
  "prompt": "Evaluate if this tool use is appropriate: $TOOL_INPUT",
  "timeout": 30
}
```

**Supported events:** Stop, SubagentStop, UserPromptSubmit, PreToolUse

#### Command Hooks

Executes bash commands for deterministic checks:

```json
{
  "type": "command",
  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh",
  "timeout": 60
}
```

### hooks.json Format for Plugins

**IMPORTANT:** For plugin hooks in `hooks/hooks.json`, use wrapper format:

```json
{
  "description": "Validation hooks for code quality",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/validate.sh"
          }
        ]
      }
    ]
  }
}
```

**Key points:**
- `description` field is optional
- `hooks` field is required wrapper containing the events
- This is the **plugin-specific** format

### Available Events

| Event | When | Use |
|-------|------|-----|
| PreToolUse | Before tool | Validation, modification |
| PostToolUse | After tool | Feedback, logging |
| UserPromptSubmit | User input | Context, validation |
| Stop | Agent stopping | Completeness check |
| SubagentStop | Subagent finished | Task validation |
| SessionStart | Session starts | Context loading |
| SessionEnd | Session ends | Cleanup, logging |
| PreCompact | Before compact | Preserve context |
| Notification | User notified | Logging, reactions |

### Matchers

```json
// Exact match
"matcher": "Write"

// Multiple tools
"matcher": "Read|Write|Edit"

// Wildcard (all tools)
"matcher": "*"

// Regex patterns
"matcher": "mcp__.*__delete.*"  // All MCP delete tools
```

### Environment Variables

Available in all command hooks:

- `$CLAUDE_PROJECT_DIR` - Project root path
- `$CLAUDE_PLUGIN_ROOT` - Plugin directory (use for portable paths)
- `$CLAUDE_ENV_FILE` - SessionStart only: persist env vars here
- `$CLAUDE_CODE_REMOTE` - Defined if running in remote context

### Exit Codes

- `0` - Success (stdout shown in transcript)
- `2` - Blocking error (stderr sent to Claude)
- Other - Non-blocking error

### Output for PreToolUse

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow|deny|ask",
    "updatedInput": {"field": "modified_value"}
  },
  "systemMessage": "Explanation for Claude"
}
```

### IMPORTANT: Hooks Load at Session Start

Changes to hook configuration require restarting Claude Code.

---

## 8. MCP Servers

Location: `.mcp.json` at plugin root

### Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/servers/server.js"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### MCP Server Types

| Type | Use |
|------|-----|
| stdio | Local, subprocess |
| http | REST endpoint |
| sse | Server-Sent Events (OAuth) |
| websocket | Real-time |

### Alternative Format

```json
{
  "server-name": {
    "type": "http",
    "url": "https://mcp.example.com/api"
  }
}
```

---

## 9. Local Configuration Files

### known_marketplaces.json

Location: `~/.claude/plugins/known_marketplaces.json`

```json
{
  "claude-plugins-official": {
    "source": {
      "source": "github",
      "repo": "anthropics/claude-plugins-official"
    },
    "installLocation": "/Users/user/.claude/plugins/marketplaces/claude-plugins-official",
    "lastUpdated": "2026-01-12T00:00:00.000Z"
  }
}
```

### Source Types

**GitHub (uses SSH by default):**
```json
"source": {
  "source": "github",
  "repo": "user/repo"
}
```

**HTTPS URL (avoids SSH issues):**
```json
"source": {
  "source": "url",
  "url": "https://github.com/user/repo.git"
}
```

### installed_plugins.json

Managed automatically by Claude Code.

---

## 10. Installation Process

### Via Interface

```
/plugin > Discover > Select plugin
```

### Via Command

```
/plugin install plugin-name@marketplace-name
```

### Add Marketplace

```
/plugin > Marketplaces > Add Marketplace
Enter: user/repo
```

### Local Testing

```bash
# Test with --plugin-dir
cc --plugin-dir /path/to/plugin

# Debug mode
claude --debug
```

---

## 11. Progressive Disclosure

Skills use a three-level loading system to manage context efficiently:

### Levels

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill is activated (<5k words)
3. **Bundled resources** - As needed (Unlimited*)

*Unlimited because scripts can execute without loading into context window.

### What Goes in SKILL.md

**Include (always loaded when skill active):**
- Core concepts and overview
- Essential procedures and workflows
- Quick reference tables
- Pointers to references/examples/scripts
- Most common use cases

**Keep below 3,000 words, ideally 1,500-2,000 words**

### What Goes in references/

**Move to references/ (loaded as needed):**
- Detailed patterns and advanced techniques
- Comprehensive API documentation
- Migration guides
- Edge cases and troubleshooting

---

## 12. Best Practices

### Organization

1. **Logical grouping**: Group related components
2. **Minimal manifest**: Keep `plugin.json` lean
3. **Documentation**: Include README files

### Naming

1. **Consistency**: Use consistent naming across components
2. **Clarity**: Use descriptive names that indicate purpose
3. **Format**: Use kebab-case for everything

### Portability

1. **Always use ${CLAUDE_PLUGIN_ROOT}**: Never hardcode paths
2. **Test on multiple systems**: Verify on macOS, Linux, Windows
3. **Document dependencies**: List required tools and versions
4. **Avoid system-specific features**: Use portable bash/Python constructs

### Hook Security

1. **Validate all inputs**: Never trust user input
2. **Quote all variables**: `"$file_path"` not `$file_path`
3. **Set appropriate timeouts**: Default: command (60s), prompt (30s)
4. **Check path traversal**: Block `..` in paths

### Documentation

1. **README in plugin**: General purpose and usage
2. **README in directories**: Specific guidance
3. **Comments in scripts**: Usage and requirements

---

## 13. Troubleshooting

### Commands Without Namespace

**Symptom:** `/start` instead of `/plugin:start`

**Cause:** `name` field in command frontmatter

**Solution:** Remove `name:` from all commands

### Permission denied (publickey)

**Symptom:** SSH error when installing

**Cause:** `source: "github"` uses SSH

**Solution:** Edit `known_marketplaces.json`:
```json
"source": {
  "source": "url",
  "url": "https://github.com/user/repo.git"
}
```

### Invalid schema

**Symptom:** Schema error when loading marketplace

**Cause:** Incorrect format or extra files

**Solution:**
- Verify `marketplace.json` follows official pattern
- Remove `plugin.json` from marketplace root

### Plugin Not Appearing

**Solutions:**
1. Restart Claude Code
2. Check `installed_plugins.json`
3. Verify `.claude-plugin/plugin.json` exists in plugin
4. Verify plugin is in `plugins/<name>/`

### Component not loading

- Check file is in correct directory with correct extension
- Check YAML frontmatter syntax
- Ensure skill has `SKILL.md` (not `README.md`)
- Confirm plugin is enabled in settings

### Path resolution errors

- Replace all hardcoded paths with `${CLAUDE_PLUGIN_ROOT}`
- Verify paths are relative and start with `./` in manifest
- Test with `echo $CLAUDE_PLUGIN_ROOT` in hook scripts

### Auto-discovery not working

- Confirm directories are at plugin root (not in `.claude-plugin/`)
- Check file naming follows conventions (kebab-case, correct extensions)
- Restart Claude Code to reload configuration

### Hooks not executing

- Verify `hooks/hooks.json` uses correct wrapper format
- Check scripts are executable (`chmod +x`)
- Use `claude --debug` to see logs
- Remember: changes require session restart

---

## 14. Checklist

### Marketplace (repository root)

- [ ] `.claude-plugin/marketplace.json` exists
- [ ] `.claude-plugin/plugin.json` **DOES NOT** exist
- [ ] `README.md` at root
- [ ] `LICENSE` at root
- [ ] Plugins in `plugins/` or `external_plugins/`

### Each Plugin

- [ ] In `plugins/<name>/`
- [ ] `.claude-plugin/plugin.json` exists (name, description, author)
- [ ] `README.md` in plugin
- [ ] Commands **WITHOUT** `name` field in frontmatter
- [ ] Commands **WITH** `description` field
- [ ] Skills with `name` and `description` in frontmatter (third person)
- [ ] Agents with `name`, `description`, `model`, `color`
- [ ] Hooks use wrapper format `{"hooks": {...}}`

### Skills

- [ ] SKILL.md exists with valid frontmatter
- [ ] Description uses third person ("This skill should be used when...")
- [ ] Description includes specific trigger phrases
- [ ] Body uses imperative/infinitive form
- [ ] Body is concise (1,500-2,000 words)
- [ ] Detailed content in references/
- [ ] Resources referenced in SKILL.md

### Agents

- [ ] Identifier 3-50 chars, lowercase, hyphens
- [ ] Description includes 2-4 <example> blocks
- [ ] Model specified (inherit recommended)
- [ ] Color specified
- [ ] System prompt in second person ("You are...")
- [ ] System prompt < 10,000 characters

### Hooks

- [ ] hooks.json uses correct wrapper format
- [ ] Scripts use ${CLAUDE_PLUGIN_ROOT}
- [ ] Scripts are executable
- [ ] Inputs are validated
- [ ] Variables are quoted
- [ ] Appropriate timeouts set

### Testing

- [ ] Clone via HTTPS works
- [ ] Installation via `/plugin install` works
- [ ] Commands appear with correct namespace (`/plugin:command`)
- [ ] Skills activate on expected triggers
- [ ] Agents are invoked correctly
- [ ] Hooks execute on correct events
- [ ] Restart Claude Code and verify

---

## Official References

- **Documentation:** https://docs.claude.com/en/docs/claude-code/plugins
- **Hooks Documentation:** https://docs.claude.com/en/docs/claude-code/hooks
- **Official Repository:** https://github.com/anthropics/claude-plugins-official
- **Plugin-Dev:** `/plugins/plugin-dev` in official repository
- **Example Plugin:** `/plugins/example-plugin` in official repository

---

## Recommended Development Workflow

```
┌─────────────────────────┐
│   Design Structure      │  → Define required components
│   (manifest, layout)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Create Plugin Base    │  → Create directories and plugin.json
│   (directories)         │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Commands          │  → User-facing slash commands
│   (user-facing)         │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Skills            │  → Specialized knowledge
│   (domain knowledge)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Agents            │  → Complex autonomous tasks
│   (autonomous tasks)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Hooks             │  → Event-driven automation
│   (event automation)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Integrate MCP         │  → External services
│   (external services)   │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Test & Validate       │  → claude --debug
│                         │     cc --plugin-dir
└──────────┬──────────────┘
           │
┌──────────▼──────────────┘
│   Document & Publish    │  → README, marketplace
└─────────────────────────┘
```

---

**Author:** Murillo Dutt - Dutt Yeshua Technology Ltd
**License:** MIT
