# Org Agentic Toolkit (OAT)

Governance infrastructure that compiles and validates **organization-level agent rules** for all projects in an org.

## Overview

The Org Agentic Toolkit (OAT) defines, compiles, and distributes the authoritative agent rules for all projects within an organization. It ensures every project inherits org rules by construction, allows optional personal overlays without weakening org authority, and produces deterministic, auditable agent instructions.

---

> **Inspiration:**  
> This project is partly inspired by [nAItmare](https://github.com/ivanlucky22/nAItmare), an open-source repository for centralizing multi-agent standards.

---

## Features

- **Single org-wide agentic constitution**: Enforce consistent rules across all projects
- **Explicit inheritance**: Projects explicitly declare which skills and personas they use
- **Personal overlays**: Optional developer-specific preferences (lowest precedence)
- **Deterministic compilation**: Same inputs produce same output byte-for-byte
- **IDE integration**: Output to IDE-specific configuration files (Cursor, Windsurf, etc.)
- **Validation**: Comprehensive validation of configuration and referenced files

## Installation

### From Source (with uv and pyproject)

```bash
git clone <repository-url>
cd org_agentic_toolkit

# Install in editable mode using uv, based on pyproject.toml with dev dependencies
uv pip install -e ".[dev]"
```

> This uses [uv](https://github.com/astral-sh/uv) following dependencies declared in `pyproject.toml`, with the package installed as a [development-only dependency](https://packaging.python.org/en/latest/specifications/declaring-project-metadata/#optional-dependencies).

## Quick Start

### 1. Initialize Organization Root

First, create your organization's constitution documents:

```bash
mkdir my-org
cd my-org
oat init org
```

This creates the full structure for an organization's agent rules, including:
- `.oat-root` - Discovery marker file
- `.agent/memory/constitution.md` - Organization constitution
- `.agent/memory/general-context.md` - General context
- `.agent/memory/manifest.yaml` - Memory manifest
- Directory structure for skills, personas, and teams

### 2. Initialize Projects

Then, initialize each project to reference the organization:

```bash
cd your-project
oat init project --org-root ../my-org
```

If the org root is in a parent directory, OAT will auto-detect it:

```bash
cd your-project
oat init project
```

This creates:
- `AGENTS.md` - Entry point for agents
- `.agent/inherits.yaml` - Project configuration (references org root)
- `.agent/project.md` - Project-specific rules

**Organization Root Discovery:**

- OAT automatically discovers org roots by walking up the directory tree looking for `.oat-root`
- If `.oat-root` is not found, it falls back to checking for `.agent/memory/constitution.md`
- You can also specify the org root path in `.agent/inherits.yaml` or via the `OAT_ROOT` environment variable

### 3. Configure Your Project

Edit `.agent/inherits.yaml` to specify which skills and personas your project uses:

```yaml
org_root: ../my-org
skills:
  universal:
    - git
    - test
    - db
  languages:
    python:
      - django
      - pytest
personas:
  - backend-developer
  - tech-lead
target_agents:
  - cursor
  - windsurf
```

### 4. Compile Agent Instructions

```bash
oat compile
```

This produces `AGENTS.compiled.md` with all rules merged in the correct precedence order.

### 5. Validate Configuration

```bash
oat validate
```

Checks that all referenced files exist and configuration is valid.

### Optional: Personal Preferences

To create a personal overlay for your own preferences:

```bash
oat init personal
```

Personal overlays have the lowest precedence and cannot override org rules.

## CLI Commands

### `oat compile`

Compile agent instructions from org rules, project rules, and personal overlay.

**Options:**

- `--out <path>`: Override output path (default: `AGENTS.compiled.md`)
- `--target <name>`: Compile for specific IDE (e.g., `cursor`, `windsurf`)
- `--no-personal`: Ignore personal overlay
- `--print`: Print compiled content to stdout
- `--hash`: Include content hash in output
- `--diff`: Show changes since last compilation
- `--include-skill <name>`: Additionally include a skill
- `--exclude-skill <name>`: Exclude a skill from manifest
- `--include-persona <name>`: Additionally include a persona
- `--exclude-persona <name>`: Exclude a persona from manifest
- `--repo <path>`: Explicit repo root path

**Examples:**

```bash
# Basic compilation
oat compile

# Compile for Cursor IDE
oat compile --target cursor

# Compile with hash
oat compile --hash

# Print to stdout
oat compile --print
```

### `oat validate`

Validate repository configuration and referenced files.

**Options:**

- `--repo <path>`: Explicit repo root path
- `--strict`: Treat warnings as errors
- `--json`: Output JSON format

**Examples:**

```bash
# Basic validation
oat validate

# Strict validation
oat validate --strict

# JSON output
oat validate --json
```

### `oat doctor`

Show diagnostic information about the current repository configuration.

**Options:**

- `--json`: Output JSON format

**Example:**

```bash
oat doctor
```

Output includes:

- Repo root and org root paths
- Entry point location
- Constitution version
- Memory files loaded
- Skills and personas from manifest
- Teams referenced
- Project rules location
- Personal overlay status
- Available but not included items

### `oat init project`

Initialize a project repository with agentic toolkit configuration.

**Options:**

- `--org-root <path>`: Explicit org root path
- `--force`: Overwrite existing files
- `--suggest`: Suggest skills/personas based on project files

**Examples:**

```bash
# Basic initialization
oat init project

# With suggestions
oat init project --suggest

# With explicit org root
oat init project --org-root ../org-agentic-toolkit
```

### `oat init org`

Initialize an organization root repository.

**Options:**

- `--name <name>`: Organization name (default: "My Org")
- `--force`: Overwrite existing files

### `oat init personal`

Initialize personal overlay directory.

**Options:**

- `--path <path>`: Override personal folder path
- `--force`: Overwrite existing files

## Project Structure

### Org Root

```
org-agentic-toolkit/
├── .oat-root                 # Discovery marker
├── AGENTS.md                 # Entry point
├── .agent/
│   ├── memory/
│   │   ├── constitution.md   # Immutable org rules
│   │   ├── general-context.md
│   │   ├── manifest.yaml
│   │   └── teams/           # Team-specific context
│   ├── skills/              # Atomic knowledge modules
│   │   ├── git.md
│   │   ├── test.md
│   │   └── [language]/      # Language-specific skills
│   ├── personas/            # Specialized personas
│   └── toolkit/             # Toolkit implementation
└── repos/                    # Project repositories
```

### Project Repo

```
project-repo/
├── AGENTS.md                 # Entry point (optional)
└── .agent/
    ├── inherits.yaml         # Project configuration (required)
    └── project.md            # Project-specific rules (required)
```

## Compilation Order

The compiled document follows strict precedence (highest to lowest):

1. **Entry Point** (`AGENTS.md` from repo)
2. **Org Memory** (constitution, general-context, teams)
3. **Universal Skills** (from `inherits.yaml`, in order)
4. **Language/Stack Skills** (grouped by language, in order)
5. **Org Personas** (from `inherits.yaml`, in order)
6. **Project Rules** (`project.md`)
7. **Personal Overlay** (optional, lowest authority)

## Environment Variables

- `OAT_ROOT`: Explicitly set the org root path
- `ORG_AGENTIC_TOOLKIT_ROOT_NAME`: Control org root directory naming pattern
- `AGENT_PERSONAL_FOLDER`: Path to personal overlay directory (default: `~/.agent`)

## IDE Integration

The toolkit supports outputting to IDE-specific configuration files via the `--target` option:

```bash
oat compile --target cursor    # Outputs to .cursorrules
oat compile --target windsurf   # Outputs to .windsurfrules
```

Supported targets are defined in `.agent/toolkit/targets.yaml`.

## Personal Overlay

Developers can maintain personal preferences in `~/.agent/` (or path specified by `AGENT_PERSONAL_FOLDER`):

```
~/.agent/
├── memory/
│   └── personal-context.md
├── skills/
│   └── personal-git.md
└── personas/
    └── me.md  # Team membership (gitignored)
```

Personal overlay has the lowest precedence and cannot override org rules.

## Validation Rules

The validator checks:

- `AGENTS.md` exists (warning if missing)
- `.agent/inherits.yaml` exists and is valid (error if missing)
- `skills` and `personas` sections exist (error if missing)
- `org_root` resolves and contains constitution
- All referenced skills exist
- All referenced personas exist
- All referenced teams exist
- `.agent/project.md` exists (error in strict mode, warning otherwise)
- `.agent/project.md` exists (error in strict mode, warning otherwise)
- No forbidden constructs (absolute paths, etc.)

Validation automatically detects the context:

- **Org Root**: Checks `.oat-root`, constitution, manifest, etc.
- **Personal Overlay**: Checks personal context, me.md
- **Project Repo**: Checks inherits.yaml and inheritance

## Examples

### Example: Python Django Project

`.agent/inherits.yaml`:

```yaml
org_root: ../..
skills:
  universal:
    - git
    - test
    - db
    - review-checklist
  languages:
    python:
      - django
      - pytest
personas:
  - backend-developer
  - tech-lead
teams:
  - platform
target_agents:
  - cursor
```

### Example: Full-Stack JavaScript Project

`.agent/inherits.yaml`:

```yaml
org_root: ../..
skills:
  universal:
    - git
    - test
  languages:
    javascript:
      - react
      - nodejs
      - jest
personas:
  - frontend-developer
  - backend-developer
  - tech-lead
```

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
org_agentic_toolkit/
├── oat/                 # Main package
│   ├── cli.py           # CLI commands
│   ├── discovery.py     # Root discovery
│   ├── config.py        # YAML loading
│   ├── compiler.py      # Compilation engine
│   ├── validator.py     # Validation logic
│   ├── template_manager.py # Template manager
│   └── templates/       # Template files (package data)
├── tests/               # Test suite
├── pyproject.toml       # Package config
└── MANIFEST.in          # Package data config
```

## License

MIT

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute, including:

- Development setup and installation
- Code style and testing guidelines
- How to submit pull requests
- Project structure and workflow

We appreciate all contributions, whether they're bug fixes, new features, documentation improvements, or other enhancements.
