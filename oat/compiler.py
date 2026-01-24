"""Compilation engine for merging agent rules from multiple sources."""

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from oat.discovery import find_personal_overlay
from oat.config import (
    load_inherits_yaml,
    load_memory_manifest,
    get_skills_from_config,
    get_personas_from_config,
    get_skills_from_config,
    get_personas_from_config,
    get_teams_from_config,
    get_target_agents_from_config,
)


@dataclass
class CompileOptions:
    """Options for compilation."""
    include_skills: List[str] = None
    exclude_skills: List[str] = None
    include_personas: List[str] = None
    exclude_personas: List[str] = None
    no_personal: bool = False
    include_hash: bool = False
    
    def __post_init__(self):
        if self.include_skills is None:
            self.include_skills = []
        if self.exclude_skills is None:
            self.exclude_skills = []
        if self.include_personas is None:
            self.include_personas = []
        if self.exclude_personas is None:
            self.exclude_personas = []


class CompileError(Exception):
    """Base exception for compilation errors."""
    pass


def _find_file_in_locations(
    file_path: str, personal_overlay: Optional[Path], org_root: Path, repo_root: Path
) -> Optional[Path]:
    """
    Find a file in the correct precedence order: personal -> org -> project.
    
    Args:
        file_path: Relative path from .agent (e.g., "skills/db.md")
        personal_overlay: Path to personal overlay (already the .agent directory, e.g., ~/.agent)
        org_root: Path to organization root
        repo_root: Path to repository root
        
    Returns:
        Path to the file if found, None otherwise
    """
    # 1. Check personal overlay (highest precedence)
    if personal_overlay:
        personal_path = personal_overlay / file_path
        if personal_path.exists():
            return personal_path
    
    # 2. Check org root
    org_path = org_root / ".agent" / file_path
    if org_path.exists():
        return org_path
    
    # 3. Check project repo (lowest precedence)
    project_path = repo_root / ".agent" / file_path
    if project_path.exists():
        return project_path
    
    return None


def compile_document(
    repo_root: Path,
    org_root: Path,
    personal_overlay: Optional[Path],
    options: CompileOptions
) -> Tuple[str, Dict[str, Any]]:
    """
    Compile the complete agent instruction document.
    
    Args:
        repo_root: Path to repository root
        org_root: Path to organization root
        personal_overlay: Path to personal overlay (optional)
        options: Compilation options
    
    Returns:
        Tuple of (compiled markdown, metadata dict)
    """
    # Load inherits.yaml
    inherits_path = repo_root / ".agent" / "inherits.yaml"
    inherits_config = load_inherits_yaml(inherits_path)
    
    # Get configuration
    skills_config = get_skills_from_config(inherits_config)
    personas_list = get_personas_from_config(inherits_config)
    skills_config = get_skills_from_config(inherits_config)
    personas_list = get_personas_from_config(inherits_config)
    teams_list = get_teams_from_config(inherits_config)
    target_agents = get_target_agents_from_config(inherits_config)
    
    # Apply include/exclude filters
    universal_skills = _apply_filters(
        skills_config["universal"],
        options.include_skills,
        options.exclude_skills
    )
    personas = _apply_filters(
        personas_list,
        options.include_personas,
        options.exclude_personas
    )
    
    # Load memory manifest
    memory_manifest = load_memory_manifest(org_root / ".agent" / "memory" / "manifest.yaml")
    
    # Build compilation sources in order
    sources = []
    metadata = {
        "repo_root": str(repo_root),
        "org_root": str(org_root),
        "entry_point": None,
        "constitution_version": None,
        "memory_files": [],
        "universal_skills": [],
        "language_skills": {},
        "personas": [],
        "teams": [],
        "target_agents": target_agents,
        "project_rules": None,
        "personal_overlay": None,
    }
    
    # 1. Entry point (AGENTS.md from repo)
    agents_md_path = repo_root / "AGENTS.md"
    if agents_md_path.exists():
        content = _read_file(agents_md_path)
        sources.append(("Entry Point", agents_md_path, content))
        metadata["entry_point"] = str(agents_md_path)
    
    # 2. Org Memory
    # Constitution (required)
    constitution_path = org_root / ".agent" / "memory" / "constitution.md"
    if not constitution_path.exists():
        raise CompileError(f"Constitution not found: {constitution_path}")
    
    constitution_content = _read_file(constitution_path)
    sources.append(("Org Constitution", constitution_path, constitution_content))
    metadata["memory_files"].append("constitution.md")
    
    # Extract version from constitution if present
    version = _extract_version(constitution_content)
    if version:
        metadata["constitution_version"] = version
    
    # General context (optional)
    general_context_path = org_root / ".agent" / "memory" / "general-context.md"
    if general_context_path.exists():
        content = _read_file(general_context_path)
        sources.append(("Org General Context", general_context_path, content))
        metadata["memory_files"].append("general-context.md")
    
    # Teams (from inherits.yaml or personal overlay)
    teams_to_load = teams_list
    
    # Check personal overlay for team context if not specified in inherits.yaml
    if not teams_to_load and not options.no_personal and personal_overlay:
        me_path = personal_overlay / "personas" / "me.md"
        if me_path.exists():
            me_content = _read_file(me_path)
            # Try to extract team from me.md (format: "team: [TEAM_NAME]")
            for line in me_content.split("\n"):
                if line.strip().startswith("team:"):
                    team_name = line.split(":", 1)[1].strip().strip("[]")
                    if team_name:
                        teams_to_load = [team_name]
                        break
    
    for team_name in teams_to_load:
        team_path = _find_file_in_locations(
            f"memory/teams/{team_name}.md", personal_overlay, org_root, repo_root
        )
        if team_path:
            content = _read_file(team_path)
            sources.append((f"Team: {team_name}", team_path, content))
            metadata["teams"].append(team_name)
        else:
            raise CompileError(f"Team not found: {team_name}")
    
    # 3. Universal Skills
    for skill_name in universal_skills:
        skill_path = _find_file_in_locations(
            f"skills/{skill_name}.md", personal_overlay, org_root, repo_root
        )
        if not skill_path:
            raise CompileError(f"Universal skill not found: {skill_name}")
        content = _read_file(skill_path)
        sources.append((f"Skill: {skill_name}", skill_path, content))
        metadata["universal_skills"].append(skill_name)
    
    # 4. Language/Stack Specific Skills
    language_skills = skills_config.get("languages", {})
    for lang, lang_skills in language_skills.items():
        lang_skill_list = []
        for skill_name in lang_skills:
            skill_path = _find_file_in_locations(
                f"skills/{lang}/{skill_name}.md", personal_overlay, org_root, repo_root
            )
            if not skill_path:
                raise CompileError(f"Language skill not found: {lang}/{skill_name}")
            content = _read_file(skill_path)
            sources.append((f"Skill: {lang}/{skill_name}", skill_path, content))
            lang_skill_list.append(skill_name)
        if lang_skill_list:
            metadata["language_skills"][lang] = lang_skill_list
    
    # 5. Personas
    for persona_name in personas:
        persona_path = _find_file_in_locations(
            f"personas/{persona_name}.md", personal_overlay, org_root, repo_root
        )
        if not persona_path:
            raise CompileError(f"Persona not found: {persona_name}")
        content = _read_file(persona_path)
        sources.append((f"Persona: {persona_name}", persona_path, content))
        metadata["personas"].append(persona_name)
    
    # 6. Project Rules
    project_md_path = repo_root / ".agent" / "project.md"
    if project_md_path.exists():
        content = _read_file(project_md_path)
        sources.append(("Project Rules", project_md_path, content))
        metadata["project_rules"] = str(project_md_path)
    
    # 7. Personal Overlay (optional, lowest precedence)
    if not options.no_personal and personal_overlay:
        # Personal memory
        personal_memory_path = personal_overlay / "memory" / "personal-context.md"
        if personal_memory_path.exists():
            content = _read_file(personal_memory_path)
            sources.append(("Personal Memory", personal_memory_path, content))
        
        # Personal skills
        personal_skills_dir = personal_overlay / "skills"
        if personal_skills_dir.exists():
            for skill_file in sorted(personal_skills_dir.glob("*.md")):
                content = _read_file(skill_file)
                sources.append((f"Personal Skill: {skill_file.stem}", skill_file, content))
        
        # Personal personas
        personal_personas_dir = personal_overlay / "personas"
        if personal_personas_dir.exists():
            for persona_file in sorted(personal_personas_dir.glob("*.md")):
                # Skip me.md as it's used for team context, not compilation
                if persona_file.name == "me.md":
                    continue
                content = _read_file(persona_file)
                sources.append((f"Personal Persona: {persona_file.stem}", persona_file, content))
        
        metadata["personal_overlay"] = str(personal_overlay)
    
    # Merge all sources
    compiled = merge_markdown(sources, repo_root, personal_overlay)
    
    # Add traceability header
    header = _build_traceability_header(metadata, repo_root, options.include_hash)
    compiled = header + "\n\n" + compiled
    
    # Compute hash if requested
    if options.include_hash:
        content_hash = _compute_hash(compiled)
        metadata["content_hash"] = content_hash
    
    return compiled, metadata


def merge_markdown(sources: List[Tuple[str, Path, str]], repo_root: Path, personal_overlay: Optional[Path]) -> str:
    """
    Merge multiple markdown files with clear section headers.
    
    Args:
        sources: List of (section_name, file_path, content) tuples
        repo_root: Path to repository root for relative path calculation
        personal_overlay: Path to personal overlay (to skip source lines for personal files)
    
    Returns:
        Merged markdown string
    """
    sections = []
    
    for section_name, file_path, content in sources:
        # Add section header
        sections.append(f"## {section_name}")
        
        # Skip source line for personal overlay files (they would break for other users)
        # Only show source for files within repo_root or org_root
        if personal_overlay and file_path.is_relative_to(personal_overlay):
            # Don't show source for personal overlay files
            pass
        else:
            # Convert to relative path from repo_root
            try:
                if file_path.is_relative_to(repo_root):
                    rel_path = file_path.relative_to(repo_root)
                else:
                    # For files outside repo (like org_root), calculate relative path
                    rel_path = os.path.relpath(str(file_path), str(repo_root))
                sections.append(f"*Source: {rel_path}*")
            except ValueError:
                # Path is not relative to repo_root, calculate using os.path.relpath
                try:
                    rel_path = os.path.relpath(str(file_path), str(repo_root))
                    sections.append(f"*Source: {rel_path}*")
                except ValueError:
                    # Can't calculate relative path, skip source line
                    pass
        
        sections.append("")
        sections.append(content)
        sections.append("")
        sections.append("---")
        sections.append("")
    
    return "\n".join(sections)


def _read_file(path: Path) -> str:
    """Read a file and return its content."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise CompileError(f"Error reading file {path}: {e}")


def _extract_version(content: str) -> Optional[str]:
    """Extract SemVer version from constitution content."""
    # Look for version in YAML frontmatter or header comment
    lines = content.split("\n")
    for line in lines[:20]:  # Check first 20 lines
        if "version:" in line.lower():
            parts = line.split(":", 1)
            if len(parts) == 2:
                version = parts[1].strip().strip('"\'')
                # Remove HTML comment suffix if present
                if "-->" in version:
                    version = version.split("-->")[0].strip()
                
                # Basic SemVer validation
                if _is_semver(version):
                    return version
    return None


def _is_semver(version: str) -> bool:
    """Check if a string is a valid SemVer version."""
    import re
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?(\+[a-zA-Z0-9]+)?$'
    return bool(re.match(pattern, version))


def _apply_filters(items: List[str], include: List[str], exclude: List[str]) -> List[str]:
    """Apply include/exclude filters to a list."""
    result = list(items)
    
    # Apply includes
    if include:
        result.extend([item for item in include if item not in result])
    
    # Apply excludes
    if exclude:
        result = [item for item in result if item not in exclude]
    
    return result


def _build_traceability_header(metadata: Dict[str, Any], repo_root: Path, include_hash: bool) -> str:
    """Build the traceability header for compiled output."""
    repo_root_path = Path(metadata['repo_root'])
    org_root_path = Path(metadata['org_root'])
    
    # Convert paths to relative
    repo_root_rel = "."
    
    # Calculate org_root relative path
    try:
        # If org_root is a parent of repo_root, calculate relative path
        if repo_root_path.is_relative_to(org_root_path):
            # Count how many levels up we need to go
            rel_parts = repo_root_path.relative_to(org_root_path).parts
            org_root_rel = "/".join([".."] * len(rel_parts))
        else:
            # Try the other direction
            org_root_rel = str(org_root_path.relative_to(repo_root_path))
    except ValueError:
        # Paths don't share a common structure, use os.path.relpath
        org_root_rel = os.path.relpath(str(org_root_path), str(repo_root_path))
    
    lines = [
        "# Compiled Agent Instructions",
        "",
        "## Traceability",
        "",
        f"- **Repo Root**: `{repo_root_rel}`",
        f"- **Org Root**: `{org_root_rel}`",
    ]
    
    if metadata.get("entry_point"):
        entry_point_path = Path(metadata['entry_point'])
        try:
            entry_point_rel = str(entry_point_path.relative_to(repo_root_path))
        except ValueError:
            entry_point_rel = os.path.relpath(str(entry_point_path), str(repo_root_path))
        lines.append(f"- **Entry Point**: `{entry_point_rel}`")
    
    if metadata.get("constitution_version"):
        lines.append(f"- **Constitution Version**: {metadata['constitution_version']}")
    
    if metadata.get("memory_files"):
        lines.append(f"- **Memory Files**: {', '.join(metadata['memory_files'])}")
    
    if metadata.get("universal_skills"):
        lines.append(f"- **Universal Skills**: {', '.join(metadata['universal_skills'])}")
    
    if metadata.get("language_skills"):
        lang_skills_str = ", ".join([
            f"{lang}: {', '.join(skills)}"
            for lang, skills in metadata["language_skills"].items()
        ])
        lines.append(f"- **Language Skills**: {lang_skills_str}")
    
    if metadata.get("personas"):
        lines.append(f"- **Personas**: {', '.join(metadata['personas'])}")
    
    if metadata.get("teams"):
        lines.append(f"- **Teams**: {', '.join(metadata['teams'])}")
        
    if metadata.get("target_agents"):
        lines.append(f"- **Target Agents**: {', '.join(metadata['target_agents'])}")
    
    if metadata.get("project_rules"):
        project_rules_path = Path(metadata['project_rules'])
        try:
            project_rules_rel = str(project_rules_path.relative_to(repo_root_path))
        except ValueError:
            project_rules_rel = os.path.relpath(str(project_rules_path), str(repo_root_path))
        lines.append(f"- **Project Rules**: `{project_rules_rel}`")
    
    # Personal overlay removed - would break for other users
    
    if include_hash and metadata.get("content_hash"):
        lines.append(f"- **Content Hash**: `{metadata['content_hash']}`")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)


def _compute_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
