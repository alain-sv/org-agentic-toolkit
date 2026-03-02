"""Setup and sync functionality for CLI."""

import importlib.resources
import sys
from pathlib import Path

import click
import yaml

from oat.cli_helpers.output import error
from oat.config import (
    load_inherits_yaml,
    ConfigError,
)
from oat.discovery import (
    find_repo_root,
    find_org_root_by_walking,
)


def _is_skill_folder(item) -> bool:
    """Check if a directory is a skill folder (contains skill.md)."""
    return item.is_dir() and item.joinpath("skill.md").is_file()


def get_available_options() -> dict:
    """Scan template folders for available skills, personas, and teams."""
    options: dict = {"skills": [], "personas": [], "teams": []}

    def _get_stem(name: str) -> str:
        """Extract stem from filename (name without extension)."""
        if name.endswith(".md"):
            return name[:-3]
        return name

    try:
        templates_root = importlib.resources.files("oat.templates")

        # Scan Universal Skills (skill folders in skills/ root)
        skills_dir = templates_root.joinpath("skills")
        if skills_dir.is_dir():
            for item in skills_dir.iterdir():
                if not item.is_dir() or item.name.startswith("_"):
                    continue

                # Check if this is a universal skill folder (has skill.md)
                if _is_skill_folder(item):
                    options["skills"].append(item.name)
                else:
                    # This is a language directory — scan for skill subfolders
                    lang_skills = []
                    for skill_item in item.iterdir():
                        if _is_skill_folder(skill_item):
                            lang_skills.append(skill_item.name)
                    if lang_skills:
                        options[item.name] = lang_skills

        # Scan Personas (excluding those starting with _)
        personas_dir = templates_root.joinpath("personas")
        if personas_dir.is_dir():
            for item in personas_dir.iterdir():
                if (
                    item.is_file()
                    and item.name.endswith(".md")
                    and not item.name.startswith("_")
                ):
                    options["personas"].append(_get_stem(item.name))

        # Scan Teams (excluding those starting with _)
        teams_dir = templates_root.joinpath("teams")
        if teams_dir.is_dir():
            for item in teams_dir.iterdir():
                if (
                    item.is_file()
                    and item.name.endswith(".md")
                    and not item.name.startswith("_")
                ):
                    options["teams"].append(_get_stem(item.name))

    except Exception:
        # Fallback: if template scanning fails, return empty options
        pass

    # Sort everything
    for k in options:
        if isinstance(options[k], list):
            options[k].sort()

    return options


def detect_languages(repo_root: Path) -> set:
    """Detect main languages in the repo."""
    langs = set()
    if (
        (repo_root / "requirements.txt").exists()
        or (repo_root / "pyproject.toml").exists()
        or (repo_root / "setup.py").exists()
        or list(repo_root.glob("*.py"))
    ):
        langs.add("python")

    if (
        (repo_root / "package.json").exists()
        or list(repo_root.glob("*.js"))
        or (repo_root / "node_modules").exists()
    ):
        langs.add("javascript")

    if (
        (repo_root / "tsconfig.json").exists()
        or list(repo_root.glob("*.ts"))
        or list(repo_root.glob("*.tsx"))
    ):
        langs.add("typescript")

    if (repo_root / "go.mod").exists() or list(repo_root.glob("*.go")):
        langs.add("go")

    if (repo_root / "Cargo.toml").exists() or list(repo_root.glob("*.rs")):
        langs.add("rust")

    if (
        (repo_root / "pom.xml").exists()
        or (repo_root / "build.gradle").exists()
        or list(repo_root.glob("*.java"))
    ):
        langs.add("java")

    return langs


def suggest_skills_personas(repo_root: Path) -> dict:
    """Suggest skills and personas based on project files."""
    suggestions = {"skills": [], "personas": []}

    # Detect languages/frameworks
    detected_langs = set()

    # Check for Python
    if (
        (repo_root / "requirements.txt").exists()
        or (repo_root / "pyproject.toml").exists()
        or (repo_root / "setup.py").exists()
        or list(repo_root.glob("*.py"))
    ):
        detected_langs.add("python")
        suggestions["skills"].extend(["django", "fastapi", "pytest"])
        suggestions["personas"].append("backend-developer")

    # Check for JavaScript/Node.js
    if (
        (repo_root / "package.json").exists()
        or list(repo_root.glob("*.js"))
        or (repo_root / "node_modules").exists()
    ):
        detected_langs.add("javascript")
        suggestions["skills"].extend(["react", "nodejs", "jest"])
        suggestions["personas"].extend(["frontend-developer", "backend-developer"])

    # Check for TypeScript
    if (
        (repo_root / "tsconfig.json").exists()
        or list(repo_root.glob("*.ts"))
        or list(repo_root.glob("*.tsx"))
    ):
        detected_langs.add("typescript")
        suggestions["skills"].extend(["angular", "nestjs"])

    # Check for Go
    if (repo_root / "go.mod").exists() or list(repo_root.glob("*.go")):
        detected_langs.add("go")
        suggestions["skills"].extend(["gin", "testing"])
        suggestions["personas"].append("backend-developer")

    # Check for Rust
    if (repo_root / "Cargo.toml").exists() or list(repo_root.glob("*.rs")):
        detected_langs.add("rust")
        suggestions["skills"].extend(["cargo", "testing"])
        suggestions["personas"].append("backend-developer")

    # Check for Java
    if (
        (repo_root / "pom.xml").exists()
        or (repo_root / "build.gradle").exists()
        or list(repo_root.glob("*.java"))
    ):
        detected_langs.add("java")
        suggestions["skills"].extend(["spring", "maven"])
        suggestions["personas"].append("backend-developer")

    # Always suggest universal skills
    suggestions["skills"].extend(["git", "test", "db", "review-checklist"])

    # Always suggest tech-lead
    suggestions["personas"].append("tech-lead")

    # Remove duplicates
    suggestions["skills"] = list(set(suggestions["skills"]))
    suggestions["personas"] = list(set(suggestions["personas"]))

    return suggestions


def run_setup(ctx):
    """Refactored setup logic shared between setup command and init_project."""
    try:
        import questionary

        repo_root = find_repo_root()
        if not repo_root:
            error("Could not find repo root. Run from inside a repository.", ctx)
            sys.exit(1)

        inherits_path = repo_root / ".agent" / "inherits.yaml"
        current_config = {}
        if inherits_path.exists():
            try:
                current_config = load_inherits_yaml(inherits_path)
            except ConfigError:
                if not ctx.obj["quiet"]:
                    click.echo(
                        "Warning: Existing inherits.yaml is invalid. Starting fresh."
                    )

        # Determine org root
        # First, check if repo_root itself is the org root (has .oat-root)
        org_root_path = None
        if (repo_root / ".oat-root").exists():
            org_root_path = repo_root
        elif "org_root" in current_config:
            # Try to resolve from inherits.yaml
            org_root_path = (repo_root / current_config["org_root"]).resolve()
            # Verify it's actually an org root
            if not org_root_path.exists() or not (
                (org_root_path / ".oat-root").exists()
                or (org_root_path / ".agent" / "memory" / "constitution.md").exists()
            ):
                org_root_path = None

        # If not found, walk up the directory tree looking for .oat-root
        if not org_root_path:
            org_root_path = find_org_root_by_walking(repo_root)

        if not org_root_path:
            error(
                "Could not find Organization Root. A directory with a .oat-root file must exist. "
                "Please run 'oat init org' to create one, or 'oat init project --org-root <path>' to link to an existing one.",
                ctx,
            )
            sys.exit(1)

        try:
            org_root_rel = str(Path(org_root_path).relative_to(repo_root))
        except ValueError:
            org_root_rel = str(org_root_path)

        # Get available options
        options = get_available_options()

        # Prepare defaults from current config
        current_skills = current_config.get("skills", {}).get("universal", [])
        current_personas = current_config.get("personas", [])
        current_team = (
            current_config.get("teams", [None])[0]
            if current_config.get("teams")
            else None
        )
        # Load available target agents from templates
        available_targets = []
        try:
            targets_path = importlib.resources.files("oat.templates").joinpath(
                "toolkit/targets.yaml"
            )
            targets_content = targets_path.read_text(encoding="utf-8")
            targets_config = yaml.safe_load(targets_content)
            if isinstance(targets_config, dict) and "targets" in targets_config:
                available_targets = list(targets_config["targets"].keys())
        except Exception:
            # Fallback to default targets if template loading fails
            available_targets = ["cursor", "windsurf"]

        # Default to first two targets if no current config, or use current config
        if not current_config.get("target_agents"):
            default_targets = (
                available_targets[:2]
                if len(available_targets) >= 2
                else available_targets
            )
        else:
            default_targets = current_config.get("target_agents", [])
        current_targets = default_targets
        current_lang_skills = current_config.get("skills", {}).get("languages", {})

        click.echo(f"\nConfiguring Project at: {repo_root}")
        click.echo(f"Linked Org Root: {org_root_path}")

        # 1. TEAM
        if options["teams"]:
            team_choices = ["None"] + options["teams"]
            default_team = current_team if current_team in options["teams"] else "None"

            selected_team = questionary.select(
                "Select Team:", choices=team_choices, default=default_team
            ).ask()

            if selected_team == "None":
                current_team = None
            else:
                current_team = selected_team

        # 2. UNIVERSAL SKILLS
        if options["skills"]:
            # Pre-select based on current config
            choices = []
            for skill in options["skills"]:
                choices.append(
                    questionary.Choice(skill, checked=(skill in current_skills))
                )

            current_skills = questionary.checkbox(
                "Select Universal Skills:", choices=choices
            ).ask()

        # 3. LANGUAGES & SKILLS
        all_langs = sorted(
            list(set([k for k in options if k not in ["teams", "skills", "personas"]]))
        )
        detected = detect_languages(repo_root)  # set of detected languages

        if all_langs:
            # First, ask which languages to configure
            # Default to detected + currently configured
            lang_choices = []
            for lang in all_langs:
                checked = (lang in detected) or (lang in current_lang_skills)
                lang_choices.append(questionary.Choice(lang, checked=checked))

            selected_langs = questionary.checkbox(
                "Select Languages to configure:", choices=lang_choices
            ).ask()

            # Now for each selected language, pick skills
            new_lang_skills = {}
            for lang in selected_langs:
                available = options[lang]
                if not available:
                    continue

                curr = current_lang_skills.get(lang, [])
                skill_choices = []
                for s in available:
                    skill_choices.append(questionary.Choice(s, checked=(s in curr)))

                chosen = questionary.checkbox(
                    f"Select {lang} Skills:", choices=skill_choices
                ).ask()

                if chosen:
                    new_lang_skills[lang] = chosen

            current_lang_skills = new_lang_skills

        # 4. PERSONAS
        if options["personas"]:
            persona_choices = []
            for p in options["personas"]:
                persona_choices.append(
                    questionary.Choice(p, checked=(p in current_personas))
                )

            current_personas = questionary.checkbox(
                "Select Personas:", choices=persona_choices
            ).ask()

        # 5. TARGET AGENTS
        target_choices = []
        for target in available_targets:
            target_choices.append(
                questionary.Choice(target, checked=(target in current_targets))
            )

        current_targets = questionary.checkbox(
            "Select Target Agents:", choices=target_choices
        ).ask()

        # SAVE
        new_config = {
            "org_root": org_root_rel,
            "skills": {"universal": current_skills, "languages": current_lang_skills},
            "personas": current_personas,
            "target_agents": current_targets,
        }
        if current_team:
            new_config["teams"] = [current_team]

        with open(inherits_path, "w", encoding="utf-8") as f:
            yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)

        if not ctx.obj["quiet"]:
            click.echo(f"\nConfiguration saved to {inherits_path}")

        # Run sync from_template to copy missing files
        if not ctx.obj["quiet"]:
            click.echo("\nSyncing templates to .agent folder...")
        sync_from_template(repo_root, new_config, ctx)

    except ImportError:
        error(
            "Module 'questionary' not found. Please reinstall org-agentic-toolkit.", ctx
        )
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


def sync_from_template(repo_root: Path, config: dict, ctx):
    """
    Sync template files to .agent folder based on inherits.yaml configuration.

    Args:
        repo_root: Path to repository root
        config: Parsed inherits.yaml configuration dict
        ctx: Click context
    """
    added_files = []
    removed_suggestions = []

    try:
        templates_root = importlib.resources.files("oat.templates")
        agent_dir = repo_root / ".agent"

        # Sync Universal Skills
        skills_config = config.get("skills", {})
        universal_skills = skills_config.get("universal", [])
        skills_dir = agent_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        templates_skills_dir = templates_root.joinpath("skills")
        if templates_skills_dir.is_dir():
            # Get all existing skill folders in .agent/skills
            existing_skills = set()
            if skills_dir.exists():
                for d in skills_dir.iterdir():
                    if d.is_dir() and (d / "skill.md").exists():
                        existing_skills.add(d.name)

            # Copy missing universal skills
            for skill_name in universal_skills:
                template_dir = templates_skills_dir.joinpath(skill_name)
                template_file = (
                    template_dir.joinpath("skill.md") if template_dir.is_dir() else None
                )
                if template_file and template_file.is_file():
                    target_dir = skills_dir / skill_name
                    target_file = target_dir / "skill.md"
                    if not target_file.exists():
                        target_dir.mkdir(parents=True, exist_ok=True)
                        content = template_file.read_text(encoding="utf-8")
                        target_file.write_text(content, encoding="utf-8")
                        added_files.append(f".agent/skills/{skill_name}/skill.md")
                elif skill_name not in existing_skills:
                    # Skill is in config but template doesn't exist
                    if not ctx.obj["quiet"]:
                        click.echo(
                            f"Warning: Template for skill '{skill_name}' not found in templates",
                            err=True,
                        )

            # Suggest removal of skills not in config
            for existing_skill in existing_skills:
                if existing_skill not in universal_skills:
                    removed_suggestions.append(f".agent/skills/{existing_skill}/")

        # Sync Language Skills
        language_skills = skills_config.get("languages", {})
        for lang, lang_skill_list in language_skills.items():
            lang_skills_dir = skills_dir / lang
            lang_skills_dir.mkdir(parents=True, exist_ok=True)

            templates_lang_dir = templates_skills_dir.joinpath(lang)
            if templates_lang_dir.is_dir():
                # Get existing skill folders
                existing_lang_skills = set()
                if lang_skills_dir.exists():
                    for d in lang_skills_dir.iterdir():
                        if d.is_dir() and (d / "skill.md").exists():
                            existing_lang_skills.add(d.name)

                # Copy missing language skills
                for skill_name in lang_skill_list:
                    template_dir = templates_lang_dir.joinpath(skill_name)
                    template_file = (
                        template_dir.joinpath("skill.md")
                        if template_dir.is_dir()
                        else None
                    )
                    if template_file and template_file.is_file():
                        target_dir = lang_skills_dir / skill_name
                        target_file = target_dir / "skill.md"
                        if not target_file.exists():
                            target_dir.mkdir(parents=True, exist_ok=True)
                            content = template_file.read_text(encoding="utf-8")
                            target_file.write_text(content, encoding="utf-8")
                            added_files.append(
                                f".agent/skills/{lang}/{skill_name}/skill.md"
                            )
                    elif skill_name not in existing_lang_skills:
                        if not ctx.obj["quiet"]:
                            click.echo(
                                f"Warning: Template for skill '{lang}/{skill_name}' not found in templates",
                                err=True,
                            )

                # Suggest removal
                for existing_skill in existing_lang_skills:
                    if existing_skill not in lang_skill_list:
                        removed_suggestions.append(
                            f".agent/skills/{lang}/{existing_skill}/"
                        )

        # Sync Personas
        personas_list = config.get("personas", [])
        personas_dir = agent_dir / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)

        templates_personas_dir = templates_root.joinpath("personas")
        if templates_personas_dir.is_dir():
            # Get existing files
            existing_personas = set()
            if personas_dir.exists():
                for f in personas_dir.glob("*.md"):
                    existing_personas.add(f.stem)

            # Copy missing personas
            for persona_name in personas_list:
                template_file = templates_personas_dir.joinpath(f"{persona_name}.md")
                if template_file.is_file():
                    target_file = personas_dir / f"{persona_name}.md"
                    if not target_file.exists():
                        content = template_file.read_text(encoding="utf-8")
                        target_file.write_text(content, encoding="utf-8")
                        added_files.append(f".agent/personas/{persona_name}.md")
                elif persona_name not in existing_personas:
                    if not ctx.obj["quiet"]:
                        click.echo(
                            f"Warning: Template for persona '{persona_name}' not found in templates",
                            err=True,
                        )

            # Suggest removal
            for existing_persona in existing_personas:
                if existing_persona not in personas_list:
                    removed_suggestions.append(f".agent/personas/{existing_persona}.md")

        # Sync Teams
        teams_list = config.get("teams", [])
        teams_dir = agent_dir / "memory" / "teams"
        teams_dir.mkdir(parents=True, exist_ok=True)

        templates_teams_dir = templates_root.joinpath("teams")
        if templates_teams_dir.is_dir():
            # Get existing files (excluding _template.md)
            existing_teams = set()
            if teams_dir.exists():
                for f in teams_dir.glob("*.md"):
                    if f.stem != "_template":
                        existing_teams.add(f.stem)

            # Copy missing teams
            for team_name in teams_list:
                template_file = templates_teams_dir.joinpath(f"{team_name}.md")
                if template_file.is_file():
                    target_file = teams_dir / f"{team_name}.md"
                    if not target_file.exists():
                        content = template_file.read_text(encoding="utf-8")
                        target_file.write_text(content, encoding="utf-8")
                        added_files.append(f".agent/memory/teams/{team_name}.md")
                elif team_name not in existing_teams:
                    if not ctx.obj["quiet"]:
                        click.echo(
                            f"Warning: Template for team '{team_name}' not found in templates",
                            err=True,
                        )

            # Suggest removal
            for existing_team in existing_teams:
                if existing_team not in teams_list:
                    removed_suggestions.append(
                        f".agent/memory/teams/{existing_team}.md"
                    )

        # Report results
        if not ctx.obj["quiet"]:
            if added_files:
                click.echo(f"\nAdded {len(added_files)} file(s):")
                for file_path in added_files:
                    click.echo(f"  + {file_path}")
            else:
                click.echo("\nNo new files to add.")

            if removed_suggestions:
                click.echo(
                    f"\nNote: {len(removed_suggestions)} file(s) in .agent/ are not in inherits.yaml and may be removed:"
                )
                for file_path in removed_suggestions:
                    click.echo(f"  - {file_path}")

    except Exception as e:
        if not ctx.obj["quiet"]:
            click.echo(f"Warning: Error syncing templates: {e}", err=True)
