# Project Rules

## Overview

The Org Agentic Toolkit (OAT) is a governance infrastructure that compiles and validates organization-level agent rules for all projects in an organization. It ensures every project inherits org rules by construction, allows optional personal overlays without weakening org authority, and produces deterministic, auditable agent instructions.

This project is the toolkit implementation itself, providing CLI commands for initializing org roots and projects, compiling agent instructions, and validating configurations.

## Local Glossary / Terminology

- **Org Root**: The organization-level repository containing the constitution, skills, personas, and team context
- **Project Repo**: A project repository that inherits from an org root via `.agent/inherits.yaml`
- **Compilation**: The process of merging org rules, skills, personas, and project rules into a single deterministic output
- **Inherits.yaml**: Project configuration file that declares which skills, personas, and teams the project uses
- **Constitution**: The immutable organization-level rules (`.agent/memory/constitution.md`)
- **Personal Overlay**: Optional developer-specific preferences stored in `~/.agent/` with lowest precedence

## Data Sensitivity Notes

No sensitive data. This is a tooling project that processes markdown and YAML configuration files. All content is version-controlled and public.

## Allowed / Forbidden Actions

### Allowed

- Creating and modifying template files in `oat/templates/`
- Adding new CLI commands in `oat/cli.py`
- Extending validation logic in `oat/validator.py`
- Running tests with `pytest`
- Compiling agent instructions with `oat compile`

### Forbidden

- Committing to git or staging files without explicit user confirmation
- Running Django migrations (not applicable, but explicitly forbidden per user rules)
- Modifying org root constitution files (this project is a consumer, not the org root itself)

## Exceptions to Org Defaults

None currently. This project follows all org defaults.

## Team Context

This is the toolkit implementation project. It may be owned by a platform/infrastructure team, but team context should be specified if applicable.

## Language/Stack Context

- **Python 3.12+**: Core implementation language
- **pytest**: Testing framework
- **click**: CLI framework
- **pyyaml**: YAML parsing
- **questionary**: Interactive prompts
- **jsonschema**: Validation (dev dependency)
- **watchdog**: File watching (dev dependency)
