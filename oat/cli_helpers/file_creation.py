"""File creation and missing file handling utilities."""

import sys
from pathlib import Path
from typing import Tuple

import click

from oat.cli_helpers.output import error
from oat.template_manager import (
    get_team_md_template,
    get_constitution_md_template,
    get_general_context_md_template,
    get_project_md_template,
    get_personal_context_md_template,
    get_me_md_template,
)


def parse_missing_file(missing_line: str) -> dict:
    """
    Parse missing file information from summary line.

    Args:
        missing_line: Line like "❌ MISSING: {name}" or "❌ MISSING: {type}: {path}"

    Returns:
        Dict with file_type, name, and relative_path
    """
    # Remove the ❌ MISSING: prefix
    content = missing_line.replace("❌ MISSING:", "").strip()

    # Check for different patterns
    if "/" in content and not content.startswith("/") and ":" not in content:
        # Language skill: "python/django" (not a path, just language/skill)
        parts = content.split("/", 1)
        return {
            "file_type": "language_skill",
            "name": parts[1],
            "language": parts[0],
            "relative_path": f"skills/{parts[0]}/{parts[1]}/skill.md",
        }
    elif content.startswith("Constitution:"):
        # Constitution: /path/to/constitution.md
        return {
            "file_type": "constitution",
            "name": "constitution",
            "relative_path": "memory/constitution.md",
        }
    else:
        # Extract name - remove path if present
        if ":" in content:
            # Format: "Type: /path/to/file" or just "name"
            parts = content.split(":", 1)
            name = parts[-1].strip()
            # Remove path if it's a full path
            if "/" in name:
                # Extract just the filename without extension
                name = Path(name).stem
        else:
            name = content.strip()

        # Determine type based on where it appears in summary
        if name.lower() in ["constitution", "constitution.md"]:
            return {
                "file_type": "constitution",
                "name": "constitution",
                "relative_path": "memory/constitution.md",
            }
        else:
            # Default: assume it's a team, skill, or persona
            # We'll need to check all possible locations
            return {
                "file_type": "unknown",
                "name": name,
                "relative_path": None,  # Will be determined by checking all locations
            }


def determine_file_type_and_path(
    name: str,
    repo_root: Path,
    org_root: Path,
    personal_overlay,
    teams_list: list,
    skills_list: list,
    personas_list: list,
) -> dict:
    """
    Determine file type and relative path for a missing file.

    Returns:
        Dict with file_type and relative_path
    """
    # Check if it's a team
    if name in teams_list:
        return {"file_type": "team", "relative_path": f"memory/teams/{name}.md"}

    # Check if it's a universal skill
    if name in skills_list:
        return {
            "file_type": "universal_skill",
            "relative_path": f"skills/{name}/skill.md",
        }

    # Check if it's a persona
    if name in personas_list:
        return {"file_type": "persona", "relative_path": f"personas/{name}.md"}

    # Default: assume team (most common case)
    return {"file_type": "team", "relative_path": f"memory/teams/{name}.md"}


def get_template_content(
    file_type: str, name: str = None, language: str = None
) -> Tuple[str, bool]:
    """
    Get template content for a file type, or return placeholder.

    Args:
        file_type: Type of file (team, skill, persona, etc.)
        name: Name of the file (for teams, personas)
        language: Language for language skills

    Returns:
        Tuple of (content, is_placeholder)
    """
    try:
        if file_type == "team" and name:
            return get_team_md_template(name), False
        elif file_type == "constitution":
            return get_constitution_md_template(), False
        elif file_type == "general_context":
            return get_general_context_md_template(), False
        elif file_type == "project":
            return get_project_md_template(), False
        elif file_type == "personal_context":
            return get_personal_context_md_template(), False
        elif file_type == "me":
            return get_me_md_template(), False
        else:
            # Create placeholder
            if file_type == "team" and name:
                placeholder = f"# Team: {name}\n\n## Mission\n\n[Describe the team's mission]\n\n## Responsibilities\n\n- [Responsibility 1]\n- [Responsibility 2]\n\n## Key Contacts\n\n- Tech Lead: [Name]\n- Product Owner: [Name]\n"
            elif file_type == "universal_skill" and name:
                placeholder = f"---\nname: {name}\ndescription: [Describe the {name} skill and when to use it]\n---\n\n# Skill: {name}\n\n[Describe the {name} skill and how it should be used]\n"
            elif file_type == "language_skill" and name and language:
                placeholder = f"---\nname: {language}/{name}\ndescription: [Describe the {name} skill for {language}]\n---\n\n# Skill: {language}/{name}\n\n[Describe the {name} skill for {language}]\n"
            elif file_type == "persona" and name:
                placeholder = f"# Persona: {name}\n\n[Describe the {name} persona]\n"
            else:
                placeholder = f"# {name or 'File'}\n\n[Add content here]\n"
            return placeholder, True
    except Exception:
        # Template not found, create placeholder
        if file_type == "team" and name:
            placeholder = f"# Team: {name}\n\n## Mission\n\n[Describe the team's mission]\n\n## Responsibilities\n\n- [Responsibility 1]\n- [Responsibility 2]\n\n## Key Contacts\n\n- Tech Lead: [Name]\n- Product Owner: [Name]\n"
        elif file_type == "universal_skill" and name:
            placeholder = f"---\nname: {name}\ndescription: [Describe the {name} skill and when to use it]\n---\n\n# Skill: {name}\n\n[Describe the {name} skill and how it should be used]\n"
        elif file_type == "language_skill" and name and language:
            placeholder = f"---\nname: {language}/{name}\ndescription: [Describe the {name} skill for {language}]\n---\n\n# Skill: {language}/{name}\n\n[Describe the {name} skill for {language}]\n"
        elif file_type == "persona" and name:
            placeholder = f"# Persona: {name}\n\n[Describe the {name} persona]\n"
        else:
            placeholder = f"# {name or 'File'}\n\n[Add content here]\n"
        return placeholder, True


def create_missing_file(
    file_info: dict,
    location: str,
    repo_root: Path,
    org_root: Path,
    personal_overlay,
    teams_list: list,
    skills_list: list,
    personas_list: list,
    ctx,
) -> Path:
    """
    Create a missing file at the specified location.

    Args:
        file_info: Parsed file information
        location: "PERSONAL", "ORG", or "PROJECT"
        repo_root: Repository root path
        org_root: Organization root path
        personal_overlay: Personal overlay path
        teams_list: List of teams
        skills_list: List of skills
        personas_list: List of personas
        ctx: Click context

    Returns:
        Path to created file
    """
    # Determine file type and path if not already determined
    if file_info.get("relative_path") is None:
        file_info.update(
            determine_file_type_and_path(
                file_info["name"],
                repo_root,
                org_root,
                personal_overlay,
                teams_list,
                skills_list,
                personas_list,
            )
        )

    relative_path = file_info["relative_path"]

    # Determine target path based on location
    if location == "PERSONAL":
        if not personal_overlay:
            error(
                "Personal overlay not found. Cannot create file at PERSONAL level.", ctx
            )
            sys.exit(1)
        target_path = personal_overlay / relative_path
    elif location == "ORG":
        target_path = org_root / ".agent" / relative_path
    else:  # PROJECT (default)
        target_path = repo_root / ".agent" / relative_path

    # Get template or placeholder
    content, is_placeholder = get_template_content(
        file_info["file_type"], file_info.get("name"), file_info.get("language")
    )

    # Create parent directories
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Alert user if placeholder was used
    if is_placeholder:
        click.echo(
            f"\n⚠️  No template found for {file_info['file_type']}. Created placeholder file."
        )

    return target_path


def offer_create_missing_files(
    missing_files: list,
    repo_root: Path,
    org_root: Path,
    personal_overlay,
    teams_list: list,
    skills_list: list,
    personas_list: list,
    ctx,
) -> list:
    """
    Offer to create missing files and handle user interaction.

    Returns:
        List of created file paths
    """
    created_files = []

    try:
        import questionary
    except ImportError:
        # Fallback to click prompts if questionary not available
        questionary = None

    for missing_line in missing_files:
        # Parse missing file info
        file_info = parse_missing_file(missing_line)

        # If relative_path not determined, try to determine it
        if file_info.get("relative_path") is None:
            file_info.update(
                determine_file_type_and_path(
                    file_info["name"],
                    repo_root,
                    org_root,
                    personal_overlay,
                    teams_list,
                    skills_list,
                    personas_list,
                )
            )

        file_name = file_info["name"]
        file_type_display = file_info["file_type"].replace("_", " ").title()

        click.echo(f"\nMissing {file_type_display}: {file_name}")

        # Offer location choice
        if questionary:
            location = questionary.select(
                f"Where should '{file_name}' be created?",
                choices=["PROJECT (default)", "ORG", "PERSONAL"],
                default="PROJECT (default)",
            ).ask()
            # Map the selected choice back to the location value
            if location == "PROJECT (default)":
                location = "PROJECT"
        else:
            click.echo("  Where should this file be created?")
            click.echo("  1. PROJECT (default)")
            click.echo("  2. ORG")
            click.echo("  3. PERSONAL")
            choice = click.prompt(
                "Select [1-3]", default="1", type=click.Choice(["1", "2", "3"])
            )
            location_map = {"1": "PROJECT", "2": "ORG", "3": "PERSONAL"}
            location = location_map[choice]

        if not location:
            click.echo("Skipping file creation.")
            continue

        # Create the file
        try:
            created_path = create_missing_file(
                file_info,
                location,
                repo_root,
                org_root,
                personal_overlay,
                teams_list,
                skills_list,
                personas_list,
                ctx,
            )
            created_files.append(created_path)
            click.echo(f"✓ Created: {created_path}")
        except Exception as e:
            error(f"Failed to create file: {e}", ctx)
            continue

    return created_files
