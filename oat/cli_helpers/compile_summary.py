"""Compile summary generation utilities."""

from pathlib import Path

from oat.compiler import CompileOptions
from oat.config import (
    get_skills_from_config,
    get_personas_from_config,
    get_teams_from_config,
)


def find_file_in_locations(
    file_path: str, personal_overlay, org_root: Path, repo_root: Path
) -> tuple:
    """
    Find a file in the correct precedence order: personal -> org -> project.

    Args:
        file_path: Relative path from .agent (e.g., "skills/db.md")
        personal_overlay: Path to personal overlay (already the .agent directory, e.g., ~/.agent)
        org_root: Path to organization root
        repo_root: Path to repository root

    Returns:
        Tuple of (found_path, locations_found_list)
        found_path is None if not found anywhere
        locations_found_list contains all locations where file exists
    """
    locations_found = []
    found_path = None

    # 1. Check personal overlay (highest precedence)
    if personal_overlay:
        personal_path = personal_overlay / file_path
        if personal_path.exists():
            locations_found.append(("personal", personal_path))
            found_path = personal_path

    # 2. Check org root
    org_path = org_root / ".agent" / file_path
    if org_path.exists():
        locations_found.append(("org", org_path))
        if found_path is None:
            found_path = org_path

    # 3. Check project repo (lowest precedence)
    project_path = repo_root / ".agent" / file_path
    if project_path.exists():
        locations_found.append(("project", project_path))
        if found_path is None:
            found_path = project_path

    return found_path, locations_found


def generate_compile_summary(
    repo_root: Path,
    org_root: Path,
    personal_overlay,
    inherits_config: dict,
    options: CompileOptions,
    output_path: Path,
    target=None,
) -> str:
    """
    Generate a summary of what will be compiled, including file locations and missing files.
    Files are searched in order: personal -> org -> project.

    Args:
        repo_root: Path to repository root
        org_root: Path to organization root
        personal_overlay: Path to personal overlay (optional)
        inherits_config: Parsed inherits.yaml configuration
        options: Compile options
        output_path: Path where output will be written
        target: Target IDE name (optional)

    Returns:
        Formatted summary string
    """

    lines = []
    missing_count = 0
    warnings = []

    # Get configuration
    skills_config = get_skills_from_config(inherits_config)
    personas_list = get_personas_from_config(inherits_config)
    teams_list = get_teams_from_config(inherits_config)

    # Apply filters
    universal_skills = skills_config.get("universal", []).copy()
    for skill in options.exclude_skills:
        if skill in universal_skills:
            universal_skills.remove(skill)
    for skill in options.include_skills:
        if skill not in universal_skills:
            universal_skills.append(skill)

    personas = personas_list.copy()
    for persona in options.exclude_personas:
        if persona in personas:
            personas.remove(persona)
    for persona in options.include_personas:
        if persona not in personas:
            personas.append(persona)

    # Entry Point
    agents_md_path = repo_root / "AGENTS.md"
    if agents_md_path.exists():
        lines.append(f"✓ Entry Point: {agents_md_path}")
    else:
        lines.append(f"○ Entry Point: {agents_md_path} (optional, not found)")

    # Org Memory
    lines.append("\nOrg Memory:")
    constitution_path = org_root / ".agent" / "memory" / "constitution.md"
    if constitution_path.exists():
        lines.append(f"  ✓ Constitution: {constitution_path}")
    else:
        lines.append(f"  ❌ MISSING: Constitution: {constitution_path}")
        missing_count += 1

    general_context_path = org_root / ".agent" / "memory" / "general-context.md"
    if general_context_path.exists():
        lines.append(f"  ✓ General Context: {general_context_path}")
    else:
        lines.append(f"  ○ General Context: {general_context_path} (optional)")

    # Teams (from inherits.yaml or personal overlay)
    teams_to_check = teams_list.copy()
    
    # Check personal overlay for team context if not specified in inherits.yaml
    if not teams_to_check and not options.no_personal and personal_overlay:
        me_path = personal_overlay / "personas" / "me.md"
        if me_path.exists():
            try:
                me_content = me_path.read_text(encoding="utf-8")
                # Try to extract team from me.md (format: "team: [TEAM_NAME]")
                for line in me_content.split("\n"):
                    if line.strip().startswith("team:"):
                        team_name = line.split(":", 1)[1].strip().strip("[]")
                        if team_name:
                            teams_to_check = [team_name]
                            break
            except Exception:
                pass  # Ignore errors reading me.md in summary
    
    # Teams
    if teams_to_check:
        lines.append("\nTeams:")
        for team_name in teams_to_check:
            file_path = f"memory/teams/{team_name}.md"
            found_path, locations = find_file_in_locations(
                file_path, personal_overlay, org_root, repo_root
            )
            if found_path:
                location_names = [loc[0] for loc in locations]
                primary_loc = locations[0][0]
                if len(locations) > 1:
                    warnings.append(
                        f"Team '{team_name}' found in multiple locations: {', '.join(location_names)}. Using {primary_loc}."
                    )
                lines.append(f"  ✓ {team_name}: {found_path} [{primary_loc}]")
            else:
                lines.append(f"  ❌ MISSING: {team_name}")
                missing_count += 1

    # Universal Skills
    if universal_skills:
        lines.append("\nUniversal Skills:")
        for skill_name in universal_skills:
            file_path = f"skills/{skill_name}.md"
            found_path, locations = find_file_in_locations(
                file_path, personal_overlay, org_root, repo_root
            )
            if found_path:
                location_names = [loc[0] for loc in locations]
                primary_loc = locations[0][0]
                if len(locations) > 1:
                    warnings.append(
                        f"Skill '{skill_name}' found in multiple locations: {', '.join(location_names)}. Using {primary_loc}."
                    )
                lines.append(f"  ✓ {skill_name}: {found_path} [{primary_loc}]")
            else:
                lines.append(f"  ❌ MISSING: {skill_name}")
                missing_count += 1

    # Language Skills
    lang_skills_raw: dict = skills_config.get("languages", {})
    language_skills = lang_skills_raw if isinstance(lang_skills_raw, dict) else {}
    if language_skills:
        lines.append("\nLanguage Skills:")
        for lang, lang_skill_list in language_skills.items():
            for skill_name in lang_skill_list:
                file_path = f"skills/{lang}/{skill_name}.md"
                found_path, locations = find_file_in_locations(
                    file_path, personal_overlay, org_root, repo_root
                )
                if found_path:
                    location_names = [loc[0] for loc in locations]
                    primary_loc = locations[0][0]
                    if len(locations) > 1:
                        warnings.append(
                            f"Skill '{lang}/{skill_name}' found in multiple locations: {', '.join(location_names)}. Using {primary_loc}."
                        )
                    lines.append(
                        f"  ✓ {lang}/{skill_name}: {found_path} [{primary_loc}]"
                    )
                else:
                    lines.append(f"  ❌ MISSING: {lang}/{skill_name}")
                    missing_count += 1

    # Personas
    if personas:
        lines.append("\nPersonas:")
        for persona_name in personas:
            file_path = f"personas/{persona_name}.md"
            found_path, locations = find_file_in_locations(
                file_path, personal_overlay, org_root, repo_root
            )
            if found_path:
                location_names = [loc[0] for loc in locations]
                primary_loc = locations[0][0]
                if len(locations) > 1:
                    warnings.append(
                        f"Persona '{persona_name}' found in multiple locations: {', '.join(location_names)}. Using {primary_loc}."
                    )
                lines.append(f"  ✓ {persona_name}: {found_path} [{primary_loc}]")
            else:
                lines.append(f"  ❌ MISSING: {persona_name}")
                missing_count += 1

    # Project Rules
    lines.append("\nProject Rules:")
    project_md_path = repo_root / ".agent" / "project.md"
    if project_md_path.exists():
        lines.append(f"  ✓ Project Rules: {project_md_path}")
    else:
        lines.append(f"  ○ Project Rules: {project_md_path} (optional)")

    # Personal Overlay
    if not options.no_personal and personal_overlay:
        lines.append("\nPersonal Overlay:")
        lines.append(f"  ✓ Personal Overlay: {personal_overlay}")
        personal_memory_path = personal_overlay / "memory" / "personal-context.md"
        if personal_memory_path.exists():
            lines.append(f"    ✓ Personal Memory: {personal_memory_path}")
        me_path = personal_overlay / "personas" / "me.md"
        if me_path.exists():
            lines.append(f"    ✓ Personal Persona: {me_path}")
    elif not options.no_personal:
        lines.append("\nPersonal Overlay:")
        lines.append("  ○ Personal Overlay: Not found (optional)")

    # Output path
    lines.append("\nOutput:")
    if target:
        lines.append(f"  → {output_path} (target: {target})")
    else:
        lines.append(f"  → {output_path}")

    if warnings:
        lines.append("\n⚠️  Warnings (non-blocking):")
        for warning in warnings:
            lines.append(f"  ⚠ {warning}")

    if missing_count > 0:
        lines.append(f"\n❌ Error: {missing_count} file(s) are missing!")

    return "\n".join(lines)
