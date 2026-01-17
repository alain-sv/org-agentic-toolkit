"""Root discovery module for finding repo root, org root, and personal overlay."""

import os
from pathlib import Path
from typing import Optional


def find_repo_root(
    cwd: Optional[Path] = None, explicit_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Find the repository root by walking up from the current working directory.

    Looks for any of:
    - A `.git/` directory
    - A `.agent/inherits.yaml` file
    - A `.oat-root` marker file

    Args:
        cwd: Current working directory (defaults to os.getcwd())
        explicit_path: Explicit repo root path (overrides discovery)

    Returns:
        Path to repo root, or None if not found
    """
    if explicit_path:
        explicit_path = Path(explicit_path).resolve()
        if explicit_path.exists():
            return explicit_path
        return None

    if cwd is None:
        cwd = Path.cwd()
    else:
        cwd = Path(cwd).resolve()

    current = cwd

    # Walk up the directory tree
    while current != current.parent:
        # Check for .git directory
        if (current / ".git").exists() and (current / ".git").is_dir():
            return current

        # Check for .agent/inherits.yaml
        if (current / ".agent" / "inherits.yaml").exists():
            return current

        # Check for .oat-root file
        if (current / ".oat-root").exists():
            return current

        current = current.parent

    # Check root directory as well
    if (current / ".git").exists() and (current / ".git").is_dir():
        return current
    if (current / ".agent" / "inherits.yaml").exists():
        return current
    if (current / ".oat-root").exists():
        return current

    return None


def find_org_root_by_walking(start_path: Path) -> Optional[Path]:
    """
    Find the organization root by walking up the directory tree looking for .oat-root.

    Args:
        start_path: Path to start searching from

    Returns:
        Path to org root, or None if not found
    """
    current = Path(start_path).resolve()

    # Walk up the directory tree
    while current != current.parent:
        # Check for .oat-root marker (primary indicator)
        if (current / ".oat-root").exists():
            return current

        # Check for .agent/memory/constitution.md (fallback)
        if (current / ".agent" / "memory" / "constitution.md").exists():
            return current

        current = current.parent

    # Check root directory as well
    if (current / ".oat-root").exists():
        return current
    if (current / ".agent" / "memory" / "constitution.md").exists():
        return current

    return None


def find_org_root(repo_root: Path, inherits_config: dict) -> Optional[Path]:
    """
    Find the organization root from the inherits.yaml configuration or by walking up.

    Args:
        repo_root: Path to the repository root
        inherits_config: Parsed inherits.yaml configuration dict

    Returns:
        Path to org root, or None if not found
    """
    # Check for explicit OAT_ROOT environment variable
    oat_root = os.environ.get("OAT_ROOT")
    if oat_root:
        org_root = Path(oat_root).expanduser().resolve()
        if org_root.exists() and _is_org_root(org_root):
            return org_root

    # Try to get org_root from inherits.yaml
    org_root_rel = inherits_config.get("org_root")
    if org_root_rel:
        # Absolute paths are forbidden
        if not Path(org_root_rel).is_absolute():
            # Resolve relative path from repo root
            org_root = (repo_root / org_root_rel).resolve()
            # Verify it's actually an org root
            if _is_org_root(org_root):
                return org_root

    # Fallback: walk up from repo_root looking for .oat-root
    return find_org_root_by_walking(repo_root)


def _is_org_root(path: Path) -> bool:
    """
    Check if a path is a valid org root.

    Primary indicator: .oat-root marker file
    Fallback indicator: .agent/memory/constitution.md

    Args:
        path: Path to check

    Returns:
        True if path is a valid org root
    """
    if not path.exists() or not path.is_dir():
        return False

    # Check for .oat-root marker (primary indicator)
    if (path / ".oat-root").exists():
        return True

    # Check for .agent/memory/constitution.md (fallback)
    if (path / ".agent" / "memory" / "constitution.md").exists():
        return True

    return False


def find_personal_overlay() -> Optional[Path]:
    """
    Find the personal overlay directory.

    Checks:
    1. $AGENT_PERSONAL_FOLDER environment variable
    2. ~/.agent (default)

    Returns:
        Path to personal overlay directory, or None if not found
    """
    # Check environment variable
    personal_folder = os.environ.get("AGENT_PERSONAL_FOLDER")
    if personal_folder:
        personal_path = Path(personal_folder).expanduser().resolve()
        if personal_path.exists() and personal_path.is_dir():
            return personal_path

    # Default to ~/.agent
    default_path = Path.home() / ".agent"
    if default_path.exists() and default_path.is_dir():
        return default_path

    return None


def get_org_root_name() -> str:
    """
    Get the expected org root directory name pattern.

    Checks ORG_AGENTIC_TOOLKIT_ROOT_NAME environment variable.
    If ORGNAME is set and ORG_AGENTIC_TOOLKIT_ROOT_NAME is not, uses $ORGNAME-agentic-toolkit.

    Returns:
        Directory name pattern
    """
    root_name = os.environ.get("ORG_AGENTIC_TOOLKIT_ROOT_NAME")
    if root_name:
        return root_name

    orgname = os.environ.get("ORGNAME")
    if orgname:
        return f"{orgname}-agentic-toolkit"

    # Default fallback (will use actual directory name)
    return "org-agentic-toolkit"
