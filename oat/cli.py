"""CLI module for the Org Agentic Toolkit."""

import json
import sys
from pathlib import Path

import click

from oat import __version__
from oat.constants import (
    MAINTENANCE_COMMENT,
    CRITICAL_NOTICE_WITH_NL,
    CRITICAL_NOTICE_WITHOUT_NL,
)
from oat.discovery import (
    find_repo_root,
    find_org_root,
    find_org_root_by_walking,
    find_personal_overlay,
)
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
    get_agents_org_md_template,
    get_inherits_yaml_template,
    get_project_md_template,
    get_constitution_md_template,
    get_general_context_md_template,
    get_manifest_yaml_template,
    get_team_md_template,
    get_personal_context_md_template,
    get_me_md_template,
)
from oat.cli_helpers.output import error, generate_table_of_contents
from oat.cli_helpers.file_creation import (
    parse_missing_file,
    determine_file_type_and_path,
    get_template_content,
    create_missing_file,
    offer_create_missing_files,
)
from oat.cli_helpers.compile_summary import (
    find_file_in_locations,
    generate_compile_summary,
)
from oat.cli_helpers.setup_sync import (
    get_available_options,
    detect_languages,
    suggest_skills_personas,
    run_setup,
    sync_from_template as sync_from_template_helper,
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
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--rules-mode",
    type=click.Choice(["copy", "link"], case_sensitive=False),
    help="Rules inclusion mode: 'copy' (copy all rules) or 'link' (point to AGENTS.compiled.md)",
)
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
    force,
    rules_mode,
):
    """Compile agent instructions from org rules, project rules, and personal overlay."""
    try:
        # Find repo root
        repo_root = find_repo_root(explicit_path=Path(repo) if repo else None)
        if not repo_root:
            error(
                "Could not find repo root. Run from inside a repository or use --repo.",
                ctx,
            )
            sys.exit(1)

        # Load inherits.yaml
        inherits_path = repo_root / ".agent" / "inherits.yaml"
        try:
            inherits_config = load_inherits_yaml(inherits_path)
        except ConfigError as e:
            error(f"Error loading inherits.yaml: {e}", ctx)
            sys.exit(1)

        # Find org root
        org_root = find_org_root(repo_root, inherits_config)
        if not org_root:
            error("Could not resolve org root from inherits.yaml", ctx)
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

        # Determine output path for summary
        summary_output_path = None
        summary_target = target
        if target:
            # Load targets.yaml from templates for summary
            import importlib.resources
            import yaml as yaml_module

            template_targets = {}
            try:
                targets_path = importlib.resources.files("oat.templates").joinpath(
                    "toolkit/targets.yaml"
                )
                targets_content = targets_path.read_text(encoding="utf-8")
                targets_config = yaml_module.safe_load(targets_content)
                template_targets = (
                    targets_config.get("targets", {})
                    if isinstance(targets_config, dict)
                    else {}
                )
            except Exception:
                pass

            # Fallback to org root
            if not template_targets:
                template_targets = load_targets_yaml(
                    org_root / ".agent" / "toolkit" / "targets.yaml"
                )

            if target in template_targets:
                summary_output_path = repo_root / template_targets[target]
        elif output_path:
            summary_output_path = Path(output_path)
        else:
            summary_output_path = repo_root / "AGENTS.compiled.md"

        # Generate and show compilation summary
        summary = generate_compile_summary(
            repo_root,
            org_root,
            personal_overlay,
            inherits_config,
            options,
            summary_output_path,
            summary_target,
        )

        if not ctx.obj["quiet"]:
            click.echo("\n" + "=" * 70)
            click.echo("Compilation Summary")
            click.echo("=" * 70)
            click.echo(summary)
            click.echo("=" * 70)

        # Get configuration lists for file creation
        teams_list = get_teams_from_config(inherits_config)
        skills_config = get_skills_from_config(inherits_config)
        skills_list = skills_config.get("universal", [])
        personas_list = get_personas_from_config(inherits_config)

        # Check for missing files
        missing_files = []
        for line in summary.split("\n"):
            if "❌ MISSING" in line:
                missing_files.append(line.strip())

        if missing_files:
            if force:
                error(
                    f"\nFound {len(missing_files)} missing file(s). Use --force to attempt compilation anyway (will fail).",
                    ctx,
                )
                sys.exit(1)
            
            # Offer to create missing files
            if not ctx.obj["quiet"] and sys.stdin.isatty():
                click.echo(f"\nFound {len(missing_files)} missing file(s).")
                if click.confirm("Would you like to create them now?", default=True):
                    created_files = offer_create_missing_files(
                        missing_files,
                        repo_root,
                        org_root,
                        personal_overlay,
                        teams_list,
                        skills_list,
                        personas_list,
                        ctx
                    )
                    
                    if created_files:
                        click.echo(f"\n✓ Created {len(created_files)} file(s).")
                        click.echo("\nPlease edit the created file(s) and run `oat compile` again:")
                        for file_path in created_files:
                            click.echo(f"  - {file_path}")
                        sys.exit(0)
                    else:
                        click.echo("\nNo files were created. Compilation cancelled.")
                        sys.exit(0)
                else:
                    click.echo("\nCompilation cancelled.")
                    sys.exit(0)
            else:
                error(
                    f"\nFound {len(missing_files)} missing file(s). Please fix these issues before compiling.",
                    ctx,
                )
                sys.exit(1)

        # Prompt for rules mode if not provided
        if rules_mode is None and not ctx.obj["quiet"] and sys.stdin.isatty():
            click.echo("\nRules inclusion mode for target files:")
            click.echo("  copy = copy all rules into target files(default)")
            click.echo("  link = target files only point to AGENTS.compiled.md")
            rules_mode = click.prompt(
                "Select mode",
                type=click.Choice(["copy", "link"], case_sensitive=False),
                default="copy",
                show_choices=True,
                show_default=True,
            )
        elif rules_mode is None:
            # Default to "copy" if not interactive
            rules_mode = "copy"

        # Normalize to lowercase
        rules_mode = rules_mode.lower() if rules_mode else "copy"

        # Ask for confirmation unless --force is used
        if not force and not ctx.obj["quiet"] and sys.stdin.isatty():
            if not click.confirm("\nProceed with compilation?", default=True):
                click.echo("Compilation cancelled.")
                sys.exit(0)

        # Compile
        try:
            compiled, metadata = compile_document(
                repo_root, org_root, personal_overlay, options
            )
        except CompileError as e:
            error(f"Compilation error: {e}", ctx)
            sys.exit(1)

        # Determine output path
        if target:
            # Load targets.yaml from templates (fallback to org root if not found)
            import importlib.resources
            import yaml as yaml_module

            template_targets = {}
            try:
                targets_path = importlib.resources.files("oat.templates").joinpath(
                    "toolkit/targets.yaml"
                )
                targets_content = targets_path.read_text(encoding="utf-8")
                targets_config = yaml_module.safe_load(targets_content)
                template_targets = (
                    targets_config.get("targets", {})
                    if isinstance(targets_config, dict)
                    else {}
                )
            except Exception:
                pass

            # Fallback to org root targets.yaml if template not available
            if not template_targets:
                template_targets = load_targets_yaml(
                    org_root / ".agent" / "toolkit" / "targets.yaml"
                )

            if target not in template_targets:
                error(
                    f"Unknown target: {target}. Available: {', '.join(template_targets.keys())}",
                    ctx,
                )
                sys.exit(1)
            output_path = repo_root / template_targets[target]
        elif not output_path:
            output_path = repo_root / "AGENTS.compiled.md"
        else:
            output_path = Path(output_path)

        # Handle diff mode
        if diff:
            if output_path.exists():
                with open(output_path, "r", encoding="utf-8") as f:
                    old_content = f.read()
                # Remove maintenance comment for comparison
                if old_content.startswith(MAINTENANCE_COMMENT):
                    old_content = old_content[len(MAINTENANCE_COMMENT) :]
                # Remove critical notice for comparison
                if old_content.startswith(CRITICAL_NOTICE_WITH_NL):
                    old_content = old_content[len(CRITICAL_NOTICE_WITH_NL) :]
                elif old_content.startswith(CRITICAL_NOTICE_WITHOUT_NL):
                    # For link mode files
                    old_content = old_content[len(CRITICAL_NOTICE_WITHOUT_NL) :]
                # Also check for TOC
                if old_content.startswith("## Table of Contents"):
                    # Find where TOC ends (usually after a blank line and before content)
                    toc_end = old_content.find(
                        "\n\n", old_content.find("## Table of Contents")
                    )
                    if toc_end != -1:
                        old_content = old_content[toc_end + 2 :]
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
            # Always write AGENTS.compiled.md with full content
            agents_compiled_path = repo_root / "AGENTS.compiled.md"
            agents_compiled_path.parent.mkdir(parents=True, exist_ok=True)
            toc = generate_table_of_contents(compiled)
            with open(agents_compiled_path, "w", encoding="utf-8") as f:
                f.write(MAINTENANCE_COMMENT)
                f.write(CRITICAL_NOTICE_WITH_NL)
                if toc:
                    f.write(toc + "\n\n")
                f.write(compiled)
            if not ctx.obj["quiet"]:
                click.echo(f"Compiled to: {agents_compiled_path}")

            # Write to output_path (target file or custom path) based on rules_mode
            if output_path != agents_compiled_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if rules_mode == "link":
                    # Link mode: target files only contain the critical notice
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(MAINTENANCE_COMMENT)
                        f.write(CRITICAL_NOTICE_WITHOUT_NL)
                else:
                    # Copy mode: write full content without critical notice
                    toc = generate_table_of_contents(compiled)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(MAINTENANCE_COMMENT)
                        if toc:
                            f.write(toc + "\n\n")
                        f.write(compiled)
                if not ctx.obj["quiet"]:
                    click.echo(f"Created target file: {output_path}")

        # Create target agent files based on target_agents in inherits.yaml
        # Only create if not using --target (which already writes to a specific file)
        # and not using --print (which just prints to stdout)
        if not print_output and not target:
            target_agents = get_target_agents_from_config(inherits_config)
            if target_agents:
                # Load targets.yaml from templates
                import importlib.resources
                import yaml as yaml_module

                try:
                    targets_path = importlib.resources.files("oat.templates").joinpath(
                        "toolkit/targets.yaml"
                    )
                    targets_content = targets_path.read_text(encoding="utf-8")
                    targets_config = yaml_module.safe_load(targets_content)
                    template_targets = (
                        targets_config.get("targets", {})
                        if isinstance(targets_config, dict)
                        else {}
                    )

                    created_targets = []
                    
                    for agent_name in target_agents:
                        if agent_name in template_targets:
                            target_file_path = repo_root / template_targets[agent_name]
                            # Create parent directories if needed (e.g., .github/, .qoder/)
                            target_file_path.parent.mkdir(parents=True, exist_ok=True)

                            # Write file based on rules_mode
                            if rules_mode == "link":
                                # Link mode: only write the critical notice
                                with open(target_file_path, "w", encoding="utf-8") as f:
                                    f.write(MAINTENANCE_COMMENT)
                                    f.write(CRITICAL_NOTICE_WITHOUT_NL)
                            else:
                                # Copy mode: write full content without critical notice
                                toc = generate_table_of_contents(compiled)
                                with open(target_file_path, "w", encoding="utf-8") as f:
                                    f.write(MAINTENANCE_COMMENT)
                                    if toc:
                                        f.write(toc + "\n\n")
                                    f.write(compiled)

                            created_targets.append(target_file_path)
                            if not ctx.obj["quiet"]:
                                click.echo(f"Created target file: {target_file_path}")

                    if created_targets and not ctx.obj["quiet"]:
                        click.echo(
                            f"\nCreated {len(created_targets)} target agent file(s)"
                        )

                except Exception as e:
                    if not ctx.obj["quiet"]:
                        click.echo(
                            f"Warning: Could not create target agent files: {e}",
                            err=True,
                        )

        # Watch mode (basic implementation)
        if watch:
            if not ctx.obj["quiet"]:
                click.echo("Watch mode not yet implemented. Use a file watcher tool.")

    except Exception as e:
        error(f"Unexpected error: {e}", ctx)
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
            error(
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
        error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="Output JSON")
@click.pass_context
def doctor(ctx, output_json):
    """Show diagnostic information about the current repository configuration."""
    try:
        repo_root = find_repo_root()
        if not repo_root:
            error("Could not find repo root. Run from inside a repository.", ctx)
            sys.exit(1)

        # Load inherits.yaml
        inherits_path = repo_root / ".agent" / "inherits.yaml"
        if not inherits_path.exists():
            error("No .agent/inherits.yaml found.", ctx)
            sys.exit(1)

        try:
            inherits_config = load_inherits_yaml(inherits_path)
        except ConfigError as e:
            error(f"Error loading inherits.yaml: {e}", ctx)
            sys.exit(1)

        # Find org root
        org_root = find_org_root(repo_root, inherits_config)
        if not org_root:
            error("Could not resolve org root.", ctx)
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
        error(f"Unexpected error: {e}", ctx)
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
            error("Could not find repo root. Run from inside a repository.", ctx)
            sys.exit(1)

        # Check for existing files
        agents_md = repo_root / "AGENTS.md"
        inherits_yaml = repo_root / ".agent" / "inherits.yaml"
        project_md = repo_root / ".agent" / "project.md"

        if not force:
            if agents_md.exists() or inherits_yaml.exists() or project_md.exists():
                error("Files already exist. Use --force to overwrite.", ctx)
                sys.exit(1)

        # Determine org root
        org_root_path = None
        if org_root:
            org_root_path = Path(org_root).resolve()
        else:
            # Try to find org root by walking up (prioritizes .oat-root)
            org_root_path = find_org_root_by_walking(repo_root)

        if not org_root_path:
            error("Could not determine org root. Use --org-root to specify.", ctx)
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
            suggestions = suggest_skills_personas(repo_root)
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
        error(f"Unexpected error: {e}", ctx)
        sys.exit(1)




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

        # 2. AGENTS.md
        _create_file(
            root / "AGENTS.md",
            get_agents_org_md_template(),
        )

        # 3. Memory (Constitution, etc.)
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

        # 5. Teams (template)
        _create_file(
            root / ".agent" / "memory" / "teams" / "_template.md",
            get_team_md_template("TEMPLATE"),
        )

        # 6. Skills (dir only)
        (root / ".agent" / "skills" / "python").mkdir(parents=True, exist_ok=True)
        (root / ".agent" / "skills" / "javascript").mkdir(parents=True, exist_ok=True)

        # 7. Personas (dir only)
        (root / ".agent" / "personas").mkdir(parents=True, exist_ok=True)

        # 8. Toolkit
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
        error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@init.command("personal")
@click.option("--path", help="Override personal folder path")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.pass_context
def init_personal(ctx, path, force):
    """Initialize personal overlay directory."""
    try:
        if path:
            base_path = Path(path).expanduser().resolve()
            # If path doesn't end with .agent, create .agent subdirectory
            if base_path.name == ".agent":
                personal_path = base_path
            else:
                personal_path = base_path / ".agent"
        elif "AGENT_PERSONAL_FOLDER" in sys.modules["os"].environ:
            env_path = (
                Path(sys.modules["os"].environ["AGENT_PERSONAL_FOLDER"])
                .expanduser()
                .resolve()
            )
            # If env path doesn't end with .agent, create .agent subdirectory
            if env_path.name == ".agent":
                personal_path = env_path
            else:
                personal_path = env_path / ".agent"
        else:
            # Default: ~/.agent is the .agent directory itself
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

        # 1. Personal Memory
        _create_file(
            personal_path / "memory" / "personal-context.md",
            get_personal_context_md_template(),
        )

        # 2. Personal Skills (dir only)
        (personal_path / "skills").mkdir(parents=True, exist_ok=True)

        # 3. Personal Personas (me.md)
        me_content = get_me_md_template()

        # Interactive prompt for team if not provided (and not force? force doesn't imply defaults, just overwrite)
        # We only prompt if we are creating the file or if we want to update it?
        # For simplicity, let's prompt if we are creating it or overwriting it.
        if (not (personal_path / "personas" / "me.md").exists()) or force:
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

        _create_file(personal_path / "personas" / "me.md", me_content)

        if not ctx.obj["quiet"]:
            if created:
                click.echo(f"Created {len(created)} files")
            if skipped:
                click.echo(f"Skipped {len(skipped)} existing files")

    except Exception as e:
        error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


@cli.command()
@click.pass_context
def setup(ctx):
    """Interactive setup for project configuration."""
    run_setup(ctx)




@cli.group()
def sync():
    """Synchronize project files with templates."""
    pass


@sync.command("from_template")
@click.option("--repo", type=click.Path(exists=True), help="Explicit repo root path")
@click.pass_context
def sync_from_template(ctx, repo):
    """Sync template files to .agent folder based on inherits.yaml configuration."""
    try:
        repo_root = find_repo_root(explicit_path=Path(repo) if repo else None)
        if not repo_root:
            error(
                "Could not find repo root. Run from inside a repository or use --repo.",
                ctx,
            )
            sys.exit(1)

        inherits_path = repo_root / ".agent" / "inherits.yaml"
        if not inherits_path.exists():
            error("No .agent/inherits.yaml found. Run 'oat init project' first.", ctx)
            sys.exit(1)

        try:
            config = load_inherits_yaml(inherits_path)
        except ConfigError as e:
            error(f"Error loading inherits.yaml: {e}", ctx)
            sys.exit(1)

        sync_from_template_helper(repo_root, config, ctx)

    except Exception as e:
        error(f"Unexpected error: {e}", ctx)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
