"""Template generation module for project initialization."""

AGENTS_MD_TEMPLATE = """# Agent Instructions

> CRITICAL: Read AGENTS.md first.

This project follows the organization's agentic toolkit standards.

## Usage

Reference specific sub-agents when requesting work:
- "As a **backend-developer**, implement feature X"
- "As a **frontend-developer**, implement feature Y"
- "As a **tech-lead**, review my changes"
"""

INHERITS_YAML_TEMPLATE = """org_root: ../..
# Required: Explicitly declare which skills are relevant for this project
skills:
  universal:
    - git
    - test
    - db
    - review-checklist
  languages:
    python:
      - django
      - fastapi
      - pytest
    javascript:
      - react
      - nodejs
      - jest
# Required: Explicitly declare which sub-agents are relevant for this project
sub_agents:
  - backend-developer
  - frontend-developer
  - tech-lead
# Optional: Declare which teams are relevant (for team-specific memory)
teams:
  - platform
"""

PROJECT_MD_TEMPLATE = """# Project Rules

## Overview

[1-2 paragraphs describing the project]

## Local Glossary / Terminology

- **Term 1**: Definition
- **Term 2**: Definition

## Data Sensitivity Notes

[Any data sensitivity or security considerations]

## Allowed / Forbidden Actions

### Allowed
- Action 1
- Action 2

### Forbidden
- Action 1 (with rationale)
- Action 2 (with rationale)

## Exceptions to Org Defaults

[Any exceptions to org defaults with explicit rationale and ticket reference]

## Team Context

[Which team owns this project]

## Language/Stack Context

[Which languages/frameworks are used, if not fully declared in inherits.yaml]
"""


def get_agents_md_template() -> str:
    """Get the template for AGENTS.md."""
    return AGENTS_MD_TEMPLATE


def get_inherits_yaml_template() -> str:
    """Get the template for inherits.yaml."""
    return INHERITS_YAML_TEMPLATE


def get_project_md_template() -> str:
    """Get the template for project.md."""
    return PROJECT_MD_TEMPLATE
