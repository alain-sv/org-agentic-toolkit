"""CLI module for the Org Agentic Toolkit."""

import json
import sys
from pathlib import Path

import click

from oat import __version__
from oat.discovery import find_repo_root, find_org_root, find_personal_overlay
from oat.config import (
    load_inherits_yaml,
    load_memory_manifest,
    load_targets_yaml,
    get_skills_from_config,
    get_personas_from_config,
    get_teams_from_config,
    get_target_agents_from_config,
    ConfigError,
)
from oat.compiler import compile_document, CompileOptions, CompileError
from oat.validator import validate_repo, validate_org_root, validate_personal_overlay
from oat.template_manager import (
    get_agents_md_template,
    get_inherits_yaml_template,
    get_project_md_template,
    get_constitution_md_template,
    get_general_context_md_template,
    get_manifest_yaml_template,
    get_team_md_template,
    get_personal_context_md_template,
    get_me_md_template,
)


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--json", "output_json", is_flag=True, help="Output machine-readable JSON"
)
@click.option("--quiet", is_flag=True, help="Suppress non-error output")
@click.pass_context
def cli(ctx, output_json, quiet):
    """Org Agentic Toolkit - Compile and validate organization-level agent rules."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json
    ctx.obj["quiet"] = quiet


@cli.command()
@click.option("--out", "output_path", type=click.Path(), help="Output file path")
@click.option("--target", help="Target IDE/Agent name (e.g., cursor, windsurf)")
@click.option("--watch", is_flag=True, help="Watch for changes and re-compile")
@click.option("--no-personal", is_flag=True, help="Ignore personal overlay")
@click.option(
    "--print", "print_output", is_flag=True, help="Print compiled content to stdout"
)
@click.option(
    "--hash", "include_hash", is_flag=True, help="Include content hash in output"
)
@click.option("--diff", is_flag=True, help="Show changes since last compilation")
@click.option(
    "--strict", is_flag=True, default=True, help="Treat missing project.md as error"
)
@click.option(
    "--include-skill",
    "include_skills",
    multiple=True,
    help="Additionally include a skill",
)
@click.option(
    "--exclude-skill",
    "exclude_skills",
    multiple=True,
    help="Exclude a skill from manifest",
)
@click.option(
    "--include-persona",
    "include_personas",
    multiple=True,
    help="Additionally include a persona",
)
@click.option(
    "--exclude-persona",
    "exclude_personas",
    multiple=True,
    help="Exclude a persona from manifest",
)
@click.option("--repo", type=click.Path(exists=True), help="Explicit repo root path")
@click.pass_context
def compile(
    ctx,
    output_path,
    target,
    watch,
    no_personal,
    print_output,
    include_hash,
    diff,
    strict,
    include_skills,
    exclude_skills,
    include_personas,
    exclude_personas,
    repo,
):
    """Compile agent instructions from org rules, project rules, and personal overlay."""
    try:
        # Find repo root
        repo_root = find_repo_root(explicit_path=Path(repo) if repo else None)
        if not repo_root:
            _error(
                "Could not find repo root. Run from inside a repository or use --repo.",
                ctx,
            )
            sys.exit(1)

        # Load inherits.yaml
        inherits_path = repo_root / ".agent" / "inherits.yaml"
        try:
            inherits_config = load_inherits_yaml(inherits_path)
        except ConfigError as e:
            _error(f"Error loading inherits.yaml: {e}", ctx)
            sys.exit(1)

        # Find org root
        org_root = find_org_root(repo_root, inherits_config)
        if not org_root:
            _error("Could not resolve org root from inherits.yaml", ctx)
            sys.exit(1)

        # Find personal overlay
        personal_overlay = None if no_personal else find_personal_overlay()

        # Build compile options
        options = CompileOptions(
            include_skills=list(include_skills),
            exclude_skills=list(exclude_skills),
            include_personas=list(include_personas),
            exclude_personas=list(exclude_personas),
            no_personal=no_personal,
            include_hash=include_hash,
        )

        # Compile
        try:
            compiled, metadata = compile_document(
                repo_root, org_root, personal_overlay, options
            )
        except CompileError as e:
            _error(f"Compilation error: {e}", ctx)
            sys.exit(1)

        # Determine output path
        if target:
            targets = load_targets_yaml(
                org_root / ".agent" / "toolkit" / "targets.yaml"
            )
            if target not in targets:
                _error(
                    f"Unknown target: {target}. Available: {', '.join(targets.keys())}",
                    ctx,
                )
                sys.exit(1)
            output_path = repo_root / targets[target]
        elif not output_path:
            output_path = repo_root / "AGENTS.compiled.md"
        else:
            output_path = Path(output_path)

        # Handle diff mode
        if diff:
            if output_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    old_content = f.read()
                # Simple diff - just show if different
                if old_content != compiled:
                    if not ctx.obj["quiet"]:
                        click.echo("Content has changed since last compilation.")
                    if print_output:
                        click.echo(compiled)
                else:
                    if not ctx.obj["quiet"]:
                        click.echo("No changes since last compilation.")
            else:
                if not ctx.obj["quiet"]:
                    click.echo("No previous compilation found.")
                if print_output:
                    click.echo(compiled)
            return

        # Print or write
        if print_output:
            click.echo(compiled)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(compiled)
            if not ctx.obj["quiet"]:
                click.echo(f"Compiled to: {output_path}")

        # Watch mode (basic implementation)
        if watch:
            if not ctx.obj["quiet"]:
                click.echo("Watch mode not yet implemented. Use a file watcher tool.")

    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@cli.command()
@click.option("--repo", type=click.Path(exists=True), help="Explicit repo root path")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
@click.pass_context
def validate(ctx, repo, strict, output_json):
    """Validate repository configuration and referenced files."""
    try:
        path_to_validate = Path(repo).resolve() if repo else Path.cwd()

        # Auto-detect context
        context_type = "unknown"
        result = None

        # 1. Check for Org Root
        if (path_to_validate / ".oat-root").exists() or (
            path_to_validate / ".agent" / "memory" / "constitution.md"
        ).exists():
            context_type = "org"
            if not ctx.obj["quiet"]:
                click.echo(f"Validating Org Root at: {path_to_validate}")
            result = validate_org_root(path_to_validate, strict=strict)

        # 2. Check for Personal Overlay
        elif (path_to_validate / ".agent" / "memory" / "personal-context.md").exists():
            context_type = "personal"
            if not ctx.obj["quiet"]:
                click.echo(f"Validating Personal Overlay at: {path_to_validate}")
            result = validate_personal_overlay(path_to_validate, strict=strict)

        # 3. Check for Project Repo
        elif (path_to_validate / ".agent" / "inherits.yaml").exists() or find_repo_root(
            explicit_path=path_to_validate
        ):
            context_type = "project"
            repo_root = find_repo_root(explicit_path=path_to_validate)
            if not repo_root:
                # Should detect invalid repo if inherits.yaml exists but find_repo_root fails?
                repo_root = path_to_validate

            if not ctx.obj["quiet"]:
                click.echo(f"Validating Project Repo at: {repo_root}")
            result = validate_repo(repo_root, strict=strict)

        else:
            _error(
                "Could not detect OAT context (Org, Personal, or Project). Run from a valid root.",
                ctx,
            )
            sys.exit(1)

        if output_json or ctx.obj["json"]:
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            # Print errors and warnings
            if result.errors:
                click.echo("Errors:", err=True)
                for error in result.errors:
                    file_str = f" ({error.file})" if error.file else ""
                    click.echo(f"  ERROR: {error.message}{file_str}", err=True)

            if result.warnings:
                click.echo("Warnings:", err=True)
                for warning in result.warnings:
                    file_str = f" ({warning.file})" if warning.file else ""
                    click.echo(f"  WARNING: {warning.message}{file_str}", err=True)

            if result.is_valid():
                if not ctx.obj["quiet"]:
                    click.echo("Validation passed.")
                sys.exit(0)
            else:
                click.echo("Validation failed.", err=True)
                sys.exit(1)

    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
@click.pass_context
def doctor(ctx, output_json):
    """Show diagnostic information about the current repository configuration."""
    try:
        repo_root = find_repo_root()
        if not repo_root:
            _error("Could not find repo root. Run from inside a repository.", ctx)
            sys.exit(1)

        # Load inherits.yaml
        inherits_path = repo_root / ".agent" / "inherits.yaml"
        if not inherits_path.exists():
            _error("No .agent/inherits.yaml found.", ctx)
            sys.exit(1)

        try:
            inherits_config = load_inherits_yaml(inherits_path)
        except ConfigError as e:
            _error(f"Error loading inherits.yaml: {e}", ctx)
            sys.exit(1)

        # Find org root
        org_root = find_org_root(repo_root, inherits_config)
        if not org_root:
            _error("Could not resolve org root.", ctx)
            sys.exit(1)

        # Get configuration
        skills_config = get_skills_from_config(inherits_config)
        personas_list = get_personas_from_config(inherits_config)
        teams_list = get_teams_from_config(inherits_config)
        target_agents = get_target_agents_from_config(inherits_config)

        # Load memory manifest
        memory_manifest = load_memory_manifest(
            org_root / ".agent" / "memory" / "manifest.yaml"
        )

        # Get constitution version
        constitution_path = org_root / ".agent" / "memory" / "constitution.md"
        constitution_version = None
        if constitution_path.exists():
            with open(constitution_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Extract version
                for line in content.split("\n")[:20]:
                    if "version:" in line.lower():
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            constitution_version = parts[1].strip().strip("\"'")
                            break

        # Find personal overlay
        personal_overlay = find_personal_overlay()

        # Build diagnostic info
        info = {
            "repo_root": str(repo_root),
            "org_root": str(org_root),
            "entry_point": str(repo_root / "AGENTS.md")
            if (repo_root / "AGENTS.md").exists()
            else None,
            "constitution_version": constitution_version,
            "memory_files": [],
            "universal_skills": skills_config.get("universal", []),
            "language_skills": skills_config.get("languages", {}),
            "personas": personas_list,
            "teams": teams_list,
            "target_agents": target_agents,
            "project_rules": str(repo_root / ".agent" / "project.md")
            if (repo_root / ".agent" / "project.md").exists()
            else None,
            "personal_overlay": str(personal_overlay) if personal_overlay else None,
        }

        # Add memory files
        if (org_root / ".agent" / "memory" / "constitution.md").exists():
            info["memory_files"].append("constitution.md")
        if (org_root / ".agent" / "memory" / "general-context.md").exists():
            info["memory_files"].append("general-context.md")

        # Find available but not included items
        available_skills = set()
        if (org_root / ".agent" / "skills").exists():
            for skill_file in (org_root / ".agent" / "skills").glob("*.md"):
                available_skills.add(skill_file.stem)

        available_personas = set()
        if (org_root / ".agent" / "personas").exists():
            for persona_file in (org_root / ".agent" / "personas").glob("*.md"):
                available_personas.add(persona_file.stem)

        included_skills = set(skills_config.get("universal", []))
        for lang_skills in skills_config.get("languages", {}).values():
            included_skills.update(lang_skills)

        info["available_but_not_included"] = {
            "skills": sorted(available_skills - included_skills),
            "personas": sorted(available_personas - set(personas_list)),
        }

        if output_json or ctx.obj["json"]:
            click.echo(json.dumps(info, indent=2))
        else:
            # Print human-readable output
            click.echo("Repository Configuration:")
            click.echo(f"  Repo Root: {info['repo_root']}")
            click.echo(f"  Org Root: {info['org_root']}")
            if info["entry_point"]:
                click.echo(f"  Entry Point: {info['entry_point']}")
            if info["constitution_version"]:
                click.echo(f"  Constitution Version: {info['constitution_version']}")
            if info["memory_files"]:
                click.echo(f"  Memory Files: {', '.join(info['memory_files'])}")
            click.echo(
                f"  Universal Skills ({len(info['universal_skills'])}): {', '.join(info['universal_skills'])}"
            )
            if info["language_skills"]:
                for lang, skills in info["language_skills"].items():
                    click.echo(f"  {lang} Skills ({len(skills)}): {', '.join(skills)}")
            click.echo(
                f"  Personas ({len(info['personas'])}): {', '.join(info['personas'])}"
            )
            if info["teams"]:
                click.echo(f"  Teams: {', '.join(info['teams'])}")
            if info["target_agents"]:
                click.echo(f"  Target Agents: {', '.join(info['target_agents'])}")
            if info["project_rules"]:
                click.echo(f"  Project Rules: {info['project_rules']}")
            if info["personal_overlay"]:
                click.echo(f"  Personal Overlay: {info['personal_overlay']}")
            else:
                click.echo("  Personal Overlay: Not found")

            if (
                info["available_but_not_included"]["skills"]
                or info["available_but_not_included"]["personas"]
            ):
                click.echo("\nAvailable but not included:")
                if info["available_but_not_included"]["skills"]:
                    click.echo(
                        f"  Skills: {', '.join(info['available_but_not_included']['skills'])}"
                    )
                if info["available_but_not_included"]["personas"]:
                    click.echo(
                        f"  Personas: {', '.join(info['available_but_not_included']['personas'])}"
                    )

    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@cli.group()
def init():
    """Initialize project or org structure."""
    pass


@init.command("project")
@click.option("--org-root", type=click.Path(exists=True), help="Explicit org root path")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option(
    "--suggest", is_flag=True, help="Suggest skills/personas based on project files"
)
@click.pass_context
def init_project(ctx, org_root, force, suggest):
    """Initialize a project repository with agentic toolkit configuration."""
    try:
        repo_root = find_repo_root()
        if not repo_root:
            _error("Could not find repo root. Run from inside a repository.", ctx)
            sys.exit(1)

        # Check for existing files
        agents_md = repo_root / "AGENTS.md"
        inherits_yaml = repo_root / ".agent" / "inherits.yaml"
        project_md = repo_root / ".agent" / "project.md"

        if not force:
            if agents_md.exists() or inherits_yaml.exists() or project_md.exists():
                _error("Files already exist. Use --force to overwrite.", ctx)
                sys.exit(1)

        # Determine org root
        org_root_path = None
        if org_root:
            org_root_path = Path(org_root).resolve()
        else:
            # Try to find org root by walking up
            current = repo_root.parent
            while current != current.parent:
                if (current / ".oat-root").exists() or (
                    current / ".agent" / "memory" / "constitution.md"
                ).exists():
                    org_root_path = current
                    break
                current = current.parent

        if not org_root_path:
            _error("Could not determine org root. Use --org-root to specify.", ctx)
            sys.exit(1)

        # Compute relative path
        try:
            org_root_rel = str(Path(org_root_path).relative_to(repo_root))
        except ValueError:
            # If not relative, use absolute path (will be caught by validator)
            org_root_rel = str(org_root_path)

        # Create .agent directory
        (repo_root / ".agent").mkdir(exist_ok=True)

        # Create AGENTS.md
        agents_content = get_agents_md_template()
        with open(agents_md, "w", encoding="utf-8") as f:
            f.write(agents_content)
        if not ctx.obj["quiet"]:
            click.echo(f"Created: {agents_md}")

        # Create inherits.yaml (default for now)
        inherits_content = get_inherits_yaml_template()
        inherits_content = inherits_content.replace(
            "org_root: ../..", f"org_root: {org_root_rel}"
        )

        # Suggestion mode - we can use this to pre-fill?
        # Actually, let's just create the file with defaults, then call setup if interactive
        # If suggest is True, we might want to pass that to setup?
        # But setup doesn't take suggestion flag yet.
        # Let's simplify: init creates files, then setup configures them.

        if suggest:
            # Pre-fill
            suggestions = _suggest_skills_personas(repo_root)
            if suggestions:
                # Load default target agents from templates
                import importlib.resources
                import yaml as yaml_module

                default_targets = ["cursor", "windsurf"]  # Fallback
                try:
                    targets_path = importlib.resources.files("oat.templates").joinpath(
                        "toolkit/targets.yaml"
                    )
                    targets_content = targets_path.read_text(encoding="utf-8")
                    targets_config = yaml_module.safe_load(targets_content)
                    if isinstance(targets_config, dict) and "targets" in targets_config:
                        available_targets = list(targets_config["targets"].keys())
                        default_targets = (
                            available_targets[:2]
                            if len(available_targets) >= 2
                            else available_targets
                        )
                except Exception:
                    pass  # Use fallback

                config = {
                    "org_root": org_root_rel,
                    "skills": {
                        "universal": suggestions.get("skills", []),
                        "languages": {},  # Todo: auto-detect languages for suggestions?
                    },
                    "personas": suggestions.get("personas", []),
                    "target_agents": default_targets,
                }
                import yaml

                with open(inherits_yaml, "w", encoding="utf-8") as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        else:
            with open(inherits_yaml, "w", encoding="utf-8") as f:
                f.write(inherits_content)

        if not ctx.obj["quiet"]:
            click.echo(f"Created: {inherits_yaml}")

        # Create project.md
        project_content = get_project_md_template()
        with open(project_md, "w", encoding="utf-8") as f:
            f.write(project_content)
        if not ctx.obj["quiet"]:
            click.echo(f"Created: {project_md}")

        if not ctx.obj["quiet"]:
            click.echo("\nProject initialized successfully!")
            click.echo("\nRun 'oat setup' to configure your project interactively.")

    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


def _get_available_options() -> dict:
    """Scan template folders for available skills, personas, and teams."""
    import importlib.resources

    options: dict = {"skills": [], "personas": [], "teams": []}

    def _get_stem(name: str) -> str:
        """Extract stem from filename (name without extension)."""
        if name.endswith(".md"):
            return name[:-3]
        return name

    try:
        templates_root = importlib.resources.files("oat.templates")

        # Scan Universal Skills (files in skills/ root, excluding those starting with _)
        skills_dir = templates_root.joinpath("skills")
        if skills_dir.is_dir():
            for item in skills_dir.iterdir():
                if (
                    item.is_file()
                    and item.name.endswith(".md")
                    and not item.name.startswith("_")
                ):
                    options["skills"].append(_get_stem(item.name))

                # Scan Language Skills (subdirectories)
                if item.is_dir():
                    lang_skills = []
                    for skill_file in item.iterdir():
                        if (
                            skill_file.is_file()
                            and skill_file.name.endswith(".md")
                            and not skill_file.name.startswith("_")
                        ):
                            lang_skills.append(_get_stem(skill_file.name))
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


def _detect_languages(repo_root: Path) -> set:
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


def _suggest_skills_personas(repo_root: Path) -> dict:
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


def _error(message: str, ctx):
    """Print error message."""
    if ctx.obj.get("json"):
        click.echo(json.dumps({"error": message}))
    else:
        click.echo(f"Error: {message}", err=True)


@init.command("org")
@click.option("--name", default="My Org", help="Organization name")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.pass_context
def init_org(ctx, name, force):
    """Initialize an organization root repository."""
    try:
        root = Path.cwd()

        # Check if directory is empty or we are forcing
        if any(root.iterdir()) and not force:
            # We allow existing implementation if we are just filling in gaps,
            # but we should warn if it looks like a random directory
            pass

        created = []
        skipped = []

        def _create_file(path: Path, content: str):
            if path.exists() and not force:
                skipped.append(str(path))
                return

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            created.append(str(path))

        # 1. .oat-root
        _create_file(root / ".oat-root", "")

        # 2. Memory (Constitution, etc.)
        _create_file(
            root / ".agent" / "memory" / "constitution.md",
            get_constitution_md_template(),
        )
        _create_file(
            root / ".agent" / "memory" / "general-context.md",
            get_general_context_md_template(),
        )
        _create_file(
            root / ".agent" / "memory" / "manifest.yaml",
            get_manifest_yaml_template(name),
        )

        # 4. Teams (template)
        _create_file(
            root / ".agent" / "memory" / "teams" / "_template.md",
            get_team_md_template("TEMPLATE"),
        )

        # 5. Skills (dir only)
        (root / ".agent" / "skills" / "python").mkdir(parents=True, exist_ok=True)
        (root / ".agent" / "skills" / "javascript").mkdir(parents=True, exist_ok=True)

        # 6. Personas (dir only)
        (root / ".agent" / "personas").mkdir(parents=True, exist_ok=True)

        # 7. Toolkit
        (root / ".agent" / "toolkit").mkdir(parents=True, exist_ok=True)
        # We could copy schemas here if we had them as resources

        if not ctx.obj["quiet"]:
            click.echo(f"Initialized Org Root at {root}")
            if created:
                click.echo(f"Created {len(created)} files:")
                for f in created:
                    click.echo(f"  + {f}")
            if skipped:
                click.echo(
                    f"Skipped {len(skipped)} existing files (use --force to overwrite):"
                )
                for f in skipped:
                    click.echo(f"  - {f}")

            click.echo(
                "\nConsider running: git init && git add . && git commit -m 'Initial org agentic toolkit'"
            )

    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@init.command("personal")
@click.option("--path", help="Override personal folder path")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.pass_context
def init_personal(ctx, path, force):
    """Initialize personal overlay directory."""
    try:
        if path:
            personal_path = Path(path).expanduser().resolve()
        elif "AGENT_PERSONAL_FOLDER" in sys.modules["os"].environ:
            personal_path = (
                Path(sys.modules["os"].environ["AGENT_PERSONAL_FOLDER"])
                .expanduser()
                .resolve()
            )
        else:
            personal_path = Path.home() / ".agent"

        click.echo(f"Initializing personal overlay at: {personal_path}")

        created = []
        skipped = []

        def _create_file(path: Path, content: str):
            if path.exists() and not force:
                skipped.append(str(path))
                return

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            created.append(str(path))

        if not ctx.obj["quiet"]:
            if created:
                click.echo(f"Created {len(created)} files")
            if skipped:
                click.echo(f"Skipped {len(skipped)} existing files")

        # 1. Personal Memory
        _create_file(
            personal_path / ".agent" / "memory" / "personal-context.md",
            get_personal_context_md_template(),
        )

        # 2. Personal Skills (dir only)
        (personal_path / ".agent" / "skills").mkdir(parents=True, exist_ok=True)

        # 3. Personal Personas (me.md)
        me_content = get_me_md_template()

        # Interactive prompt for team if not provided (and not force? force doesn't imply defaults, just overwrite)
        # We only prompt if we are creating the file or if we want to update it?
        # For simplicity, let's prompt if we are creating it or overwriting it.
        if (not (personal_path / ".agent" / "personas" / "me.md").exists()) or force:
            team = ""
            if sys.stdin.isatty():
                team = click.prompt(
                    "Enter your team name (optional)", default="", show_default=False
                )

            if team:
                # Replace placeholder or add field
                # The template currently has "team: []" or similar?
                # Let's assume we want to inject it.
                # If template is simple, we might just replace a placeholder like "[TEAM_NAME]" if existed,
                # but based on previous view it was a static template.
                # Let's check template content first?
                # For now, let's assume we replace "team: []" with "team: [team_name]" or similar logic.
                # Actually, better to just append or replace.
                if "team: []" in me_content:
                    me_content = me_content.replace("team: []", f"team: [{team}]")
                elif "team:" in me_content:
                    # Regex replace might be better but let's stick to simple replacement if possible
                    import re

                    me_content = re.sub(r"team: \[.*\]", f"team: [{team}]", me_content)

        _create_file(personal_path / ".agent" / "personas" / "me.md", me_content)

    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@cli.command()
@click.pass_context
def setup(ctx):
    """Interactive setup for project configuration."""
    _run_setup(ctx)


def _run_setup(ctx):
    """Refactored setup logic shared between setup command and init_project."""
    try:
        import questionary

        repo_root = find_repo_root()
        if not repo_root:
            _error("Could not find repo root. Run from inside a repository.", ctx)
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
        org_root_path = None
        if "org_root" in current_config:
            org_root_path = (
                repo_root / ".agent" / current_config["org_root"]
            ).resolve()

        if not org_root_path or not org_root_path.exists():
            current = repo_root.parent
            while current != current.parent:
                if (current / ".oat-root").exists() or (
                    current / ".agent" / "memory" / "constitution.md"
                ).exists():
                    org_root_path = current
                    break
                current = current.parent

        if not org_root_path:
            _error(
                "Could not find Organization Root. Please run 'oat init project --org-root <path>' first to link.",
                ctx,
            )
            sys.exit(1)

        try:
            org_root_rel = str(Path(org_root_path).relative_to(repo_root))
        except ValueError:
            org_root_rel = str(org_root_path)

        # Get available options
        options = _get_available_options()

        # Prepare defaults from current config
        current_skills = current_config.get("skills", {}).get("universal", [])
        current_personas = current_config.get("personas", [])
        current_team = (
            current_config.get("teams", [None])[0]
            if current_config.get("teams")
            else None
        )
        # Load available target agents from templates
        import importlib.resources

        available_targets = []
        try:
            targets_path = importlib.resources.files("oat.templates").joinpath(
                "toolkit/targets.yaml"
            )
            targets_content = targets_path.read_text(encoding="utf-8")
            import yaml

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
        detected = _detect_languages(repo_root)  # set of detected languages

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

        import yaml

        with open(inherits_path, "w", encoding="utf-8") as f:
            yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)

        if not ctx.obj["quiet"]:
            click.echo(f"\nConfiguration saved to {inherits_path}")

    except ImportError:
        _error(
            "Module 'questionary' not found. Please reinstall org-agentic-toolkit.", ctx
        )
        sys.exit(1)
    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
