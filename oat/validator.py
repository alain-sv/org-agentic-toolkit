"""Validation module for checking repository and configuration correctness."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from oat.discovery import find_org_root
from oat.config import (
    load_inherits_yaml,
    load_memory_manifest,
    validate_inherits_structure,
    get_skills_from_config,
    get_personas_from_config,
    get_teams_from_config,
    ConfigError,
)


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    level: str  # "error" or "warning"
    message: str
    file: Optional[Path] = None
    line: Optional[int] = None


class ValidationResult:
    """Result of validation with errors and warnings."""
    
    def __init__(self):
        self.errors: List[ValidationIssue] = []
        self.warnings: List[ValidationIssue] = []
    
    def add_error(self, message: str, file: Optional[Path] = None, line: Optional[int] = None):
        """Add an error."""
        self.errors.append(ValidationIssue("error", message, file, line))
    
    def add_warning(self, message: str, file: Optional[Path] = None, line: Optional[int] = None):
        """Add a warning."""
        self.warnings.append(ValidationIssue("warning", message, file, line))
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "valid": self.is_valid(),
            "errors": [
                {
                    "level": e.level,
                    "message": e.message,
                    "file": str(e.file) if e.file else None,
                    "line": e.line,
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "level": w.level,
                    "message": w.message,
                    "file": str(w.file) if w.file else None,
                    "line": w.line,
                }
                for w in self.warnings
            ],
        }


def validate_repo(repo_root: Path, strict: bool = False) -> ValidationResult:
    """
    Validate a repository's agentic toolkit configuration.
    
    Args:
        repo_root: Path to repository root
        strict: If True, treat warnings as errors
    
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()
    
    # Check AGENTS.md exists (warning if missing)
    agents_md_path = repo_root / "AGENTS.md"
    if not agents_md_path.exists():
        result.add_warning("AGENTS.md not found in repo root (recommended but not required)", agents_md_path)
    
    # Check .agent/inherits.yaml exists (error if missing)
    inherits_path = repo_root / ".agent" / "inherits.yaml"
    if not inherits_path.exists():
        result.add_error(".agent/inherits.yaml not found (required)", inherits_path)
        return result  # Can't continue without inherits.yaml
    
    # Load and validate inherits.yaml structure
    try:
        inherits_config = load_inherits_yaml(inherits_path)
    except ConfigError as e:
        result.add_error(str(e), inherits_path)
        return result  # Can't continue with invalid inherits.yaml
    
    # Validate structure
    structure_errors = validate_inherits_structure(inherits_config)
    for error_msg in structure_errors:
        result.add_error(error_msg, inherits_path)
    
    if not result.is_valid():
        return result  # Can't continue with invalid structure
    
    # Check skills and personas sections exist
    if "skills" not in inherits_config:
        result.add_error("Missing required field: skills", inherits_path)
    if "personas" not in inherits_config:
        result.add_error("Missing required field: personas", inherits_path)
    
    if not result.is_valid():
        return result
    
    # Validate org_root resolves
    org_root = find_org_root(repo_root, inherits_config)
    if not org_root:
        result.add_error("org_root does not resolve to a valid org root", inherits_path)
        return result
    
    # Check constitution exists
    constitution_path = org_root / ".agent" / "memory" / "constitution.md"
    if not constitution_path.exists():
        result.add_error(f"Constitution not found: {constitution_path}", constitution_path)
    
    # Validate skills
    skills_config = get_skills_from_config(inherits_config)
    
    # Universal skills
    universal_skills = skills_config.get("universal", [])
    for skill_name in universal_skills:
        skill_path = org_root / ".agent" / "skills" / f"{skill_name}.md"
        if not skill_path.exists():
            result.add_error(f"Universal skill not found: {skill_path}", skill_path)
    
    # Language/stack specific skills
    language_skills = skills_config.get("languages", {})
    for lang, lang_skills in language_skills.items():
        for skill_name in lang_skills:
            skill_path = org_root / ".agent" / "skills" / lang / f"{skill_name}.md"
            if not skill_path.exists():
                result.add_error(f"Language skill not found: {skill_path}", skill_path)
    
    # Validate personas
    personas_list = get_personas_from_config(inherits_config)
    for persona_name in personas_list:
        persona_path = org_root / ".agent" / "personas" / f"{persona_name}.md"
        if not persona_path.exists():
            result.add_error(f"Persona not found: {persona_path}", persona_path)
    
    # Validate teams (if specified)
    teams_list = get_teams_from_config(inherits_config)
    for team_name in teams_list:
        team_path = org_root / ".agent" / "memory" / "teams" / f"{team_name}.md"
        if not team_path.exists():
            result.add_error(f"Team file not found: {team_path}", team_path)
    
    # Check project.md (error in strict mode, warning otherwise)
    project_md_path = repo_root / ".agent" / "project.md"
    if not project_md_path.exists():
        if strict:
            result.add_error(".agent/project.md not found (required in strict mode)", project_md_path)
        else:
            result.add_warning(".agent/project.md not found (recommended)", project_md_path)
    
    # Validate markdown files are readable
    _validate_markdown_files(result, org_root, inherits_config)
    
    # Validate SemVer if version metadata present in constitution
    if constitution_path.exists():
        _validate_constitution_version(result, constitution_path)
    
    # Check for forbidden constructs
    _check_forbidden_constructs(result, inherits_config, inherits_path)
    
    # If strict mode, convert warnings to errors
    if strict:
        for warning in result.warnings:
            result.add_error(warning.message, warning.file, warning.line)
        result.warnings = []
    
    return result


def _validate_markdown_files(result: ValidationResult, org_root: Path, inherits_config: dict):
    """Validate that all referenced markdown files are readable."""
    skills_config = get_skills_from_config(inherits_config)
    personas_list = get_personas_from_config(inherits_config)
    teams_list = get_teams_from_config(inherits_config)
    
    # Check universal skills
    for skill_name in skills_config.get("universal", []):
        skill_path = org_root / ".agent" / "skills" / f"{skill_name}.md"
        if skill_path.exists():
            try:
                with open(skill_path, "r", encoding="utf-8") as f:
                    f.read()
            except Exception as e:
                result.add_error(f"Skill file not readable: {e}", skill_path)
    
    # Check language skills
    for lang, lang_skills in skills_config.get("languages", {}).items():
        for skill_name in lang_skills:
            skill_path = org_root / ".agent" / "skills" / lang / f"{skill_name}.md"
            if skill_path.exists():
                try:
                    with open(skill_path, "r", encoding="utf-8") as f:
                        f.read()
                except Exception as e:
                    result.add_error(f"Language skill file not readable: {e}", skill_path)
    
    # Check personas
    for persona_name in personas_list:
        persona_path = org_root / ".agent" / "personas" / f"{persona_name}.md"
        if persona_path.exists():
            try:
                with open(persona_path, "r", encoding="utf-8") as f:
                    f.read()
            except Exception as e:
                result.add_error(f"Persona file not readable: {e}", persona_path)
    
    # Check teams
    for team_name in teams_list:
        team_path = org_root / ".agent" / "memory" / "teams" / f"{team_name}.md"
        if team_path.exists():
            try:
                with open(team_path, "r", encoding="utf-8") as f:
                    f.read()
            except Exception as e:
                result.add_error(f"Team file not readable: {e}", team_path)


def _validate_constitution_version(result: ValidationResult, constitution_path: Path):
    """Validate SemVer compliance if version metadata present."""
    try:
        with open(constitution_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for version in first 20 lines
        lines = content.split("\n")[:20]
        for line in lines:
            if "version:" in line.lower():
                parts = line.split(":", 1)
                if len(parts) == 2:
                    version = parts[1].strip().strip('"\'')
                    if not _is_semver(version):
                        result.add_warning(
                            f"Constitution version does not follow SemVer: {version}",
                            constitution_path
                        )
                break
    except Exception:
        pass  # Ignore errors in version extraction


def _is_semver(version: str) -> bool:
    """Check if a string is a valid SemVer version."""
    import re
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?(\+[a-zA-Z0-9]+)?$'
    return bool(re.match(pattern, version))


def _check_forbidden_constructs(result: ValidationResult, inherits_config: dict, inherits_path: Path):
    """Check for forbidden constructs in inherits.yaml."""
    # Absolute paths are forbidden
    org_root = inherits_config.get("org_root")
    if org_root and Path(org_root).is_absolute():
        result.add_error("org_root must be a relative path (absolute paths are forbidden)", inherits_path)
    
    # Check for other forbidden patterns
    # (Add more checks as needed)

def validate_org_root(org_root: Path, strict: bool = False) -> ValidationResult:
    """
    Validate an organization root directory.
    
    Args:
        org_root: Path to org root
        strict: If True, treat warnings as errors
    
    Returns:
        ValidationResult
    """
    result = ValidationResult()
    
    # Check marker file (recommended)
    if not (org_root / ".oat-root").exists():
        result.add_warning(".oat-root marker file missing", org_root / ".oat-root")
    
    # Check constitution (required)
    constitution_path = org_root / ".agent" / "memory" / "constitution.md"
    if not constitution_path.exists():
        result.add_error("Constitution not found (required)", constitution_path)
    else:
        # Validate version if present
        _validate_constitution_version(result, constitution_path)
    
    # Check general context (recommended)
    gen_context_path = org_root / ".agent" / "memory" / "general-context.md"
    if not gen_context_path.exists():
        result.add_warning("General context not found", gen_context_path)
    
    # Check manifest (recommended)
    manifest_path = org_root / ".agent" / "memory" / "manifest.yaml"
    if not manifest_path.exists():
        result.add_warning("Memory manifest not found", manifest_path)
    else:
        # Validate manifest syntax
        manifest = load_memory_manifest(manifest_path)
        if manifest is None:
            result.add_error("Invalid memory manifest", manifest_path)
    
    # Check directories
    skills_dir = org_root / ".agent" / "skills"
    if not skills_dir.exists():
        result.add_warning("Skills directory not found", skills_dir)
    
    personas_dir = org_root / ".agent" / "personas"
    if not personas_dir.exists():
        result.add_warning("Personas directory not found", personas_dir)
        
    # Validate markdown files readability
    if skills_dir.exists():
        for f in skills_dir.glob("**/*.md"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    file.read()
            except Exception as e:
                result.add_error(f"Skill file not readable: {e}", f)
    
    if personas_dir.exists():
        for f in personas_dir.glob("*.md"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    file.read()
            except Exception as e:
                result.add_error(f"Persona file not readable: {e}", f)

    # Convert warnings if strict
    if strict:
        for warning in result.warnings:
            result.add_error(warning.message, warning.file, warning.line)
        result.warnings = []
    
    return result


def validate_personal_overlay(personal_path: Path, strict: bool = False) -> ValidationResult:
    """
    Validate personal overlay directory.
    
    Args:
        personal_path: Path to personal overlay
        strict: If True, treat warnings as errors
    
    Returns:
        ValidationResult
    """
    result = ValidationResult()
    
    # Check if directory exists
    if not personal_path.exists():
        result.add_error(f"Personal overlay directory does not exist: {personal_path}", personal_path)
        return result
        
    # Check personal context (recommended)
    context_path = personal_path / "memory" / "personal-context.md"
    if not context_path.exists():
        result.add_warning("Personal context not found", context_path)
        
    # Check me.md (recommended for team context)
    me_path = personal_path / "personas" / "me.md"
    if not me_path.exists():
        result.add_warning("me.md identity file not found", me_path)
        
    # Validate markdown files
    for f in personal_path.glob("**/*.md"):
        try:
            with open(f, "r", encoding="utf-8") as file:
                file.read()
        except Exception as e:
            result.add_error(f"File not readable: {e}", f)
            
    # Convert warnings if strict
    if strict:
        for warning in result.warnings:
            result.add_error(warning.message, warning.file, warning.line)
        result.warnings = []
            
    return result
