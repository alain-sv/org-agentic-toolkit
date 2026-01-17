"""Org Agentic Toolkit (OAT) - Governance infrastructure for organization-level agent rules."""

__version__ = "1.0.0"
__author__ = "Alain Prasquier [alain-sv](https://github.com/alain-sv/)"

from oat.discovery import find_repo_root, find_org_root, find_personal_overlay
from oat.config import load_inherits_yaml, load_memory_manifest, load_targets_yaml
from oat.compiler import compile_document
from oat.validator import validate_repo

__all__ = [
    "__version__",
    "find_repo_root",
    "find_org_root",
    "find_personal_overlay",
    "load_inherits_yaml",
    "load_memory_manifest",
    "load_targets_yaml",
    "compile_document",
    "validate_repo",
]
