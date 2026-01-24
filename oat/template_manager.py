"""Template management module for project initialization."""

import importlib.resources
from pathlib import Path
from typing import Optional

# Constants for template file names
TEMPLATE_FILES = {
    "AGENTS_MD": "AGENTS.md",
    "AGENTS_ORG_MD": "AGENTS_ORG.md",
    "INHERITS_YAML": "inherits.yaml",
    "PROJECT_MD": "project.md",
    "CONSTITUTION_MD": "memory/constitution.md",
    "GENERAL_CONTEXT_MD": "memory/general-context.md",
    "MANIFEST_YAML": "memory/manifest.yaml",
    "TEAM_MD": "teams/_template.md",
    "PERSONAL_CONTEXT_MD": "memory/personal-context.md",
    "ME_MD": "personas/me.md",
}


def _read_template(filename: str) -> str:
    """Read a template file from the package resources."""
    try:
        # Use importlib.resources to read files from the oat.templates package
        # For nested files (like memory/constitution.md), we need to handle paths
        # importlib.resources.files() returned a Traversable that works like Path
        template_path = importlib.resources.files("oat.templates").joinpath(filename)
        return template_path.read_text(encoding="utf-8")
    except Exception as e:
        # Fallback for development/editable installs where structure might confuse importlib
        # or if the file is missing
        raise FileNotFoundError(f"Could not load template {filename}: {e}")


def get_agents_md_template() -> str:
    """Get the template for AGENTS.md (project version)."""
    return _read_template(TEMPLATE_FILES["AGENTS_MD"])


def get_agents_org_md_template() -> str:
    """Get the template for AGENTS.md (org root version)."""
    return _read_template("toolkit/templates/AGENTS.md.template")


def get_inherits_yaml_template() -> str:
    """Get the template for inherits.yaml."""
    return _read_template(TEMPLATE_FILES["INHERITS_YAML"])


def get_project_md_template() -> str:
    """Get the template for project.md."""
    return _read_template(TEMPLATE_FILES["PROJECT_MD"])


def get_constitution_md_template() -> str:
    """Get the template for constitution.md."""
    return _read_template(TEMPLATE_FILES["CONSTITUTION_MD"])


def get_general_context_md_template() -> str:
    """Get the template for general-context.md."""
    return _read_template(TEMPLATE_FILES["GENERAL_CONTEXT_MD"])


def get_manifest_yaml_template(org_name: str = "My Org") -> str:
    """Get the template for manifest.yaml."""
    content = _read_template(TEMPLATE_FILES["MANIFEST_YAML"])
    return content.format(org_name=org_name)


def get_team_md_template(team_name: str) -> str:
    """Get the template for a team md file."""
    content = _read_template(TEMPLATE_FILES["TEAM_MD"])
    return content.format(team_name=team_name)


def get_personal_context_md_template() -> str:
    """Get the template for personal-context.md."""
    return _read_template(TEMPLATE_FILES["PERSONAL_CONTEXT_MD"])


def get_me_md_template() -> str:
    """Get the template for me.md."""
    return _read_template(TEMPLATE_FILES["ME_MD"])
