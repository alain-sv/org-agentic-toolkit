---
name: Multi-level OAT with persona rename
overview: Implement three-level OAT system (org, project, personal) with scaffold/validate at each level, compilation at project level, target agents in project manifest, and rename "sub-agent" to "persona" throughout the codebase.
todos:
  - id: rename_persona
    content: Rename 'sub-agent' to 'persona' throughout codebase (config, cli, compiler, validator, templates, tests, schemas, directory structure)
    status: in_progress
  - id: target_agents
    content: Add target_agents field to project manifest (inherits.yaml) with config loading, validation, and metadata support
    status: pending
  - id: init_org
    content: Implement oat init org command to scaffold full org root structure with all templates
    status: pending
  - id: init_personal
    content: Implement oat init personal command to scaffold personal overlay structure
    status: pending
  - id: multi_level_validate
    content: Enhance oat validate to work at org, project, and personal levels with auto-detection
    status: pending
  - id: update_docs
    content: Update README.md and all documentation with persona terminology, new commands, and target agents
    status: pending
  - id: update_tests
    content: Update all tests to use persona terminology and add tests for new init commands and multi-level validation
    status: pending
---

# Multi-Level OAT Implementation Plan

## Overview

Transform OAT to support three distinct levels (org, project, personal) with scaffold creation and validation at each level. At the project level, add compilation capability that collects rules from all three levels. Add target agent specification in project manifest. Rename "sub-agent" to "persona" throughout the codebase.

## Installation and Usage Model

### Tool Installation

- **OAT tool** is installed globally via `uv tool install` (or similar) to be available anywhere
- The tool itself is a standalone CLI that can be run from any directory
- Installation: `uv tool install org-agentic-toolkit` (or from git URL)

### Org Root Repository

- **Org root** (`org-agentic-toolkit/` or similar) is a **git repository** that should be committed
- This repository contains the organization's agentic constitution, skills, personas, and toolkit structure
- The org root is typically cloned/shared across the organization
- Projects reference the org root via relative paths in `.agent/inherits.yaml`

### Usage Flow

1. Install OAT tool globally: `uv tool install org-agentic-toolkit`
2. Create/initialize org root: `oat init org` (creates git repository structure)
3. Commit org root to git: `git init && git add . && git commit`
4. In project repos: `oat init project --org-root ../org-agentic-toolkit`
5. Use OAT commands from any directory: `oat compile`, `oat validate`, etc.

## Architecture Changes

### Three-Level System

```
Org Level (org-agentic-toolkit/)
├── .oat-root
├── AGENTS.md
└── .agent/
    ├── memory/ (constitution, general-context, manifest.yaml, teams/)
    ├── skills/ (universal + language-specific)
    ├── personas/ (renamed from sub-agents/)
    └── toolkit/

Project Level (project-repo/)
├── AGENTS.md
└── .agent/
    ├── inherits.yaml (includes target_agents field)
    └── project.md

Personal Level (~/.agent/)
├── memory/
├── skills/
└── personas/
```

### Commands Structure

- `oat init org` - Scaffold org root structure (safe: never overwrites existing files by default)
- `oat init project` - Scaffold project structure (existing, enhanced, safe by default)
- `oat init personal` - Scaffold personal overlay structure (safe: never overwrites existing files by default)
- `oat validate` - Works at all three levels (detects context)
- `oat compile` - Only at project level (collects org + project + personal)

## Implementation Tasks

### Safety Requirement

**Critical**: All `init` commands must implement safe-by-default behavior:

- Check existence of each file/directory before creation
- Skip existing files with informative message (unless `--force`)
- Only create missing files/directories
- Report summary: created vs skipped files
- `--force` flag must show clear warning before overwriting

### 1. Rename "sub-agent" to "persona"

**Files to update:**

- `oat/config.py`: `get_sub_agents_from_config()` → `get_personas_from_config()`, `sub_agents` → `personas`
- `oat/cli.py`: All `sub_agent`/`sub-agent` references → `persona`
- `oat/compiler.py`: `sub_agents` → `personas`, directory `.agent/sub-agents/` → `.agent/personas/`
- `oat/validator.py`: `sub_agents` → `personas`
- `oat/templates.py`: Template content updates
- `README.md`: Documentation updates
- All test files: `test_*.py`
- Schema files: `.agent/toolkit/schemas/inherits.schema.json`
- Template files: `.agent/toolkit/templates/**/*.yaml`, `*.md.template`
- Directory structure: `.agent/sub-agents/` → `.agent/personas/`

**Key changes:**

- Function names: `get_sub_agents_from_config()` → `get_personas_from_config()`
- CLI options: `--include-sub-agent` → `--include-persona`, `--exclude-sub-agent` → `--exclude-persona`
- YAML keys: `sub_agents:` → `personas:`
- Directory paths: `.agent/sub-agents/` → `.agent/personas/`
- Variable names: `sub_agents_list` → `personas_list`, etc.

### 2. Add Target Agents to Project Manifest

**File: `oat/config.py`**

- Add `get_target_agents_from_config()` function
- Update `validate_inherits_structure()` to validate `target_agents` field (optional list)

**File: `.agent/toolkit/schemas/inherits.schema.json`**

- Add `target_agents` field (optional array of strings)

**File: `oat/templates.py`**

- Update `INHERITS_YAML_TEMPLATE` to include `target_agents:` section with examples

**File: `oat/compiler.py`**

- Add `target_agents` to metadata
- Include in traceability header

**File: `oat/cli.py`**

- Update `doctor` command to show target agents
- Update `compile` command to respect target agents (future: filter output per target)

### 3. Implement `oat init org`

**File: `oat/cli.py`**

- Add `@init.command("org")` handler
- **Safety: Never overwrite existing files by default**
- For each file/directory, check if it exists:
  - If exists and `--force` not set: Skip with informative message
  - If exists and `--force` set: Overwrite (with warning)
  - If not exists: Create from template
- Create full org root structure (only missing items):
  - `.oat-root` marker file
  - `AGENTS.md` from template
  - `.agent/memory/constitution.md` (template)
  - `.agent/memory/general-context.md` (template)
  - `.agent/memory/manifest.yaml` (template)
  - `.agent/memory/teams/` directory with `_template.md`
  - `.agent/skills/` directory structure (create directory only, don't populate with skill files)
  - `.agent/personas/` directory (renamed from sub-agents, create directory only)
  - `.agent/toolkit/` with `targets.yaml`, schemas, templates (only if missing)
- **Note**: Org root is intended to be a git repository - suggest `git init` after creation (optional message)

**File: `oat/templates.py`**

- Add `get_org_root_templates()` function
- Templates for: `constitution.md`, `general-context.md`, `manifest.yaml`, `AGENTS.md` (org version)

**Options:**

- `--name <org-name>`: Set org name in manifest (only if creating new manifest.yaml)
- `--force`: Overwrite existing files (use with caution, shows warning)

**Behavior:**

- Default: Safe mode - only creates missing files/directories
- Reports which files were created, which were skipped
- `--force`: Explicitly required to overwrite existing content
- After successful init, optionally suggest: "Org root initialized. Consider running: git init && git add . && git commit"

### 4. Implement `oat init personal`

**File: `oat/cli.py`**

- Add `@init.command("personal")` handler
- **Safety: Never overwrite existing files by default**
- For each file/directory, check if it exists:
  - If exists and `--force` not set: Skip with informative message
  - If exists and `--force` set: Overwrite (with warning)
  - If not exists: Create from template
- Create personal overlay structure in `~/.agent/` (or `AGENT_PERSONAL_FOLDER`):
  - `.agent/memory/personal-context.md` (template)
  - `.agent/skills/` directory (create directory only, don't populate)
  - `.agent/personas/` directory with `me.md` template (only if missing)

**File: `oat/templates.py`**

- Add `get_personal_templates()` function
- Templates for: `personal-context.md`, `me.md`

**Options:**

- `--path <path>`: Override personal folder path
- `--force`: Overwrite existing files (use with caution, shows warning)

**Behavior:**

- Default: Safe mode - only creates missing files/directories
- Reports which files were created, which were skipped
- `--force`: Explicitly required to overwrite existing content

### 5. Enhance `oat validate` for Multi-Level

**File: `oat/validator.py`**

- Add `validate_org_root(org_root: Path)` function
- Add `validate_personal_overlay(personal_path: Path)` function
- Update `validate_repo()` to detect context and call appropriate validator
- Org validation checks:
  - `.oat-root` exists
  - `constitution.md` exists
  - `manifest.yaml` is valid
  - Directory structure is correct
- Personal validation checks:
  - Directory structure is correct
  - Files are valid markdown

**File: `oat/cli.py`**

- Update `validate` command to auto-detect level or accept `--level org|project|personal`
- Show appropriate validation results per level

### 6. Update Compilation for Target Agents

**File: `oat/compiler.py`**

- Load `target_agents` from inherits.yaml
- Add to metadata
- Include in traceability header
- Future: Filter/transform output per target (not in this phase, just capture the data)

### 7. Update Documentation

**File: `README.md`**

- Update all "sub-agent" references to "persona"
- **Add Installation section:**
  - Installation via `uv tool install org-agentic-toolkit` (or git URL)
  - Clarify that OAT tool is installed globally, org root is a git repository
  - Usage flow: install tool → init org → commit org root → init projects
- Add sections for:
  - `oat init org` command (with note about git repository)
  - `oat init personal` command
  - Multi-level validation
  - Target agents in project manifest
- Update structure diagrams to show `personas/` instead of `sub-agents/`
- Update examples in `inherits.yaml` to use `personas:` and include `target_agents:`
- Update "Quick Start" to reflect installation method

### 8. Update Tests

**Files: `tests/test_*.py`**

- Rename all `sub_agent`/`sub-agent` references to `persona`
- Update directory paths: `sub-agents/` → `personas/`
- Add tests for:
  - `oat init org`
  - `oat init personal`
  - Multi-level validation
  - Target agents loading

### 9. Update Discovery Logic

**File: `oat/discovery.py`**

- Update `find_org_root()` to look for `.agent/personas/` instead of `.agent/sub-agents/`
- Ensure personal overlay discovery works with new structure

## File Changes Summary

**Core files to modify:**

- `oat/config.py` - Rename functions, add target_agents support
- `oat/cli.py` - Add init org/personal, update all persona references, add target_agents display
- `oat/compiler.py` - Rename sub_agents to personas, add target_agents to metadata
- `oat/validator.py` - Rename references, add org/personal validation
- `oat/templates.py` - Update templates, add org/personal templates
- `oat/discovery.py` - Update directory references

**Package configuration:**

- `pyproject.toml` - Already configured correctly for `uv tool install`
  - Entry point: `oat = "oat.cli:main"` (already present)
  - Ensure package is installable via: `uv tool install org-agentic-toolkit` or `uv tool install git+https://...`

**Documentation:**

- `README.md` - Comprehensive updates

**Tests:**

- All `tests/test_*.py` files - Update references

**Templates and schemas:**

- `.agent/toolkit/schemas/inherits.schema.json` - Add target_agents, rename sub_agents
- `.agent/toolkit/templates/**/*` - Update all templates
- Directory rename: `.agent/sub-agents/` → `.agent/personas/`

## Migration Notes

- Existing projects using `sub_agents:` in `inherits.yaml` will need manual update (or add backward compatibility)
- Existing org roots with `.agent/sub-agents/` directory need manual rename
- Consider adding migration helper or backward compatibility layer

## Installation and Distribution

- **OAT tool**: Install globally via `uv tool install org-agentic-toolkit` (or from git URL)
- **Org root**: Created via `oat init org`, should be committed to git as a repository
- The tool and org root are separate: tool is global CLI, org root is versioned repository
- Users can have multiple org roots (different organizations) but one global tool installation% 