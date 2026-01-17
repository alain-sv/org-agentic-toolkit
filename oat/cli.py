"""CLI module for the Org Agentic Toolkit."""

import json
import sys
from pathlib import Path
from typing import Optional

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
from oat.validator import validate_repo, validate_org_root, validate_personal_overlay, ValidationResult
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
@click.option("--json", "output_json", is_flag=True, help="Output machine-readable JSON")
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
@click.option("--print", "print_output", is_flag=True, help="Print compiled content to stdout")
@click.option("--hash", "include_hash", is_flag=True, help="Include content hash in output")
@click.option("--diff", is_flag=True, help="Show changes since last compilation")
@click.option("--strict", is_flag=True, default=True, help="Treat missing project.md as error")
@click.option("--include-skill", "include_skills", multiple=True, help="Additionally include a skill")
@click.option("--exclude-skill", "exclude_skills", multiple=True, help="Exclude a skill from manifest")
@click.option("--include-persona", "include_personas", multiple=True, help="Additionally include a persona")
@click.option("--exclude-persona", "exclude_personas", multiple=True, help="Exclude a persona from manifest")
@click.option("--repo", type=click.Path(exists=True), help="Explicit repo root path")
@click.pass_context
def compile(ctx, output_path, target, watch, no_personal, print_output, include_hash, diff, strict,
            include_skills, exclude_skills, include_personas, exclude_personas, repo):
    """Compile agent instructions from org rules, project rules, and personal overlay."""
    try:
        # Find repo root
        repo_root = find_repo_root(explicit_path=Path(repo) if repo else None)
        if not repo_root:
            _error("Could not find repo root. Run from inside a repository or use --repo.", ctx)
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
            compiled, metadata = compile_document(repo_root, org_root, personal_overlay, options)
        except CompileError as e:
            _error(f"Compilation error: {e}", ctx)
            sys.exit(1)
        
        # Determine output path
        if target:
            targets = load_targets_yaml(org_root / ".agent" / "toolkit" / "targets.yaml")
            if target not in targets:
                _error(f"Unknown target: {target}. Available: {', '.join(targets.keys())}", ctx)
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
        if (path_to_validate / ".oat-root").exists() or (path_to_validate / ".agent" / "memory" / "constitution.md").exists():
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
        elif (path_to_validate / ".agent" / "inherits.yaml").exists() or find_repo_root(explicit_path=path_to_validate):
            context_type = "project"
            repo_root = find_repo_root(explicit_path=path_to_validate)
            if not repo_root:
                 # Should detect invalid repo if inherits.yaml exists but find_repo_root fails?
                 repo_root = path_to_validate
                 
            if not ctx.obj["quiet"]:
                click.echo(f"Validating Project Repo at: {repo_root}")
            result = validate_repo(repo_root, strict=strict)
            
        else:
            _error("Could not detect OAT context (Org, Personal, or Project). Run from a valid root.", ctx)
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
        memory_manifest = load_memory_manifest(org_root / ".agent" / "memory" / "manifest.yaml")
        
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
                            constitution_version = parts[1].strip().strip('"\'')
                            break
        
        # Find personal overlay
        personal_overlay = find_personal_overlay()
        
        # Build diagnostic info
        info = {
            "repo_root": str(repo_root),
            "org_root": str(org_root),
            "entry_point": str(repo_root / "AGENTS.md") if (repo_root / "AGENTS.md").exists() else None,
            "constitution_version": constitution_version,
            "memory_files": [],
            "universal_skills": skills_config.get("universal", []),
            "language_skills": skills_config.get("languages", {}),
            "personas": personas_list,
            "teams": teams_list,
            "target_agents": target_agents,
            "project_rules": str(repo_root / ".agent" / "project.md") if (repo_root / ".agent" / "project.md").exists() else None,
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
            click.echo(f"  Universal Skills ({len(info['universal_skills'])}): {', '.join(info['universal_skills'])}")
            if info["language_skills"]:
                for lang, skills in info["language_skills"].items():
                    click.echo(f"  {lang} Skills ({len(skills)}): {', '.join(skills)}")
            click.echo(f"  Personas ({len(info['personas'])}): {', '.join(info['personas'])}")
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
            
            if info["available_but_not_included"]["skills"] or info["available_but_not_included"]["personas"]:
                click.echo("\nAvailable but not included:")
                if info["available_but_not_included"]["skills"]:
                    click.echo(f"  Skills: {', '.join(info['available_but_not_included']['skills'])}")
                if info["available_but_not_included"]["personas"]:
                    click.echo(f"  Personas: {', '.join(info['available_but_not_included']['personas'])}")
    
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
@click.option("--suggest", is_flag=True, help="Suggest skills/personas based on project files")
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
                if (current / ".oat-root").exists() or (current / ".agent" / "memory" / "constitution.md").exists():
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
        
        # Prepare selections
        selected_team = None
        selected_skills = []
        selected_personas = []
        selected_lang_skills = {}
        target_agents = ["cursor", "windsurf"] # Default targets
        
        # Suggestion mode
        if suggest:
             suggestions = _suggest_skills_personas(repo_root)
             if suggestions:
                 if not ctx.obj["quiet"]:
                     click.echo("\nSuggested configuration based on project files:")
                     if suggestions.get("skills"):
                         click.echo(f"  Skills: {', '.join(suggestions['skills'])}")
                     if suggestions.get("personas"):
                         click.echo(f"  Personas: {', '.join(suggestions['personas'])}")
                 
                 selected_skills = suggestions.get("skills", [])
                 selected_personas = suggestions.get("personas", [])
        
        # Interactive mode (if not suggest and strictly interactive)
        elif sys.stdin.isatty():
             if not ctx.obj["quiet"]:
                 click.echo(f"\nScanning Org Root at {org_root_path}...")
             
             options = _get_available_options(org_root_path)
             
             # Prompt Team
             if options["teams"]:
                 click.echo("\nAvailable Teams:")
                 for i, t in enumerate(options["teams"], 1):
                     click.echo(f"  {i}. {t}")
                 click.echo("  0. None")
                 choice = click.prompt("Select Team (number)", type=int, default=0)
                 if 0 < choice <= len(options["teams"]):
                     selected_team = options["teams"][choice-1]
            
             # Prompt Universal Skills
             if options["skills"]:
                 click.echo("\nAvailable Universal Skills:")
                 # Pre-select some common ones if available
                 defaults = [s for s in ["git", "test", "db"] if s in options["skills"]]
                 default_str = ", ".join(defaults)
                 
                 click.echo(f"  (Available: {', '.join(options['skills'])})")
                 skills_in = click.prompt("Enter Universal Skills (comma-separated)", default=default_str)
                 if skills_in.strip():
                     selected_skills = [s.strip() for s in skills_in.split(",") if s.strip()]
            
             # Prompt Language Skills
             all_langs = sorted(list(set([k for k in options if k not in ["teams", "skills", "personas"]])))
             # Heuristic: Detect language to filter?
             detected = _detect_languages(repo_root)
             
             for lang in all_langs:
                 lang_skills = options[lang]
                 if not lang_skills: continue
                 
                 # Only prompt if detected or user wants to see all?
                 # Let's prompt for relevant languages
                 if lang in detected or click.confirm(f"\nInclude {lang} skills?", default=(lang in detected)):
                     click.echo(f"Available {lang} skills: {', '.join(lang_skills)}")
                     l_skills_in = click.prompt(f"Enter {lang} skills (comma-separated)", default="")
                     if l_skills_in.strip():
                         selected_lang_skills[lang] = [s.strip() for s in l_skills_in.split(",") if s.strip()]

             # Prompt Personas
             if options["personas"]:
                 click.echo("\nAvailable Personas:")
                 click.echo(f"  (Available: {', '.join(options['personas'])})")
                 personas_in = click.prompt("Enter Personas (comma-separated)", default="tech-lead")
                 if personas_in.strip():
                     selected_personas = [p.strip() for p in personas_in.split(",") if p.strip()]
        
        # Create .agent directory
        (repo_root / ".agent").mkdir(exist_ok=True)
        
        # Create AGENTS.md
        agents_content = get_agents_md_template()
        with open(agents_md, "w", encoding="utf-8") as f:
            f.write(agents_content)
        if not ctx.obj["quiet"]:
            click.echo(f"Created: {agents_md}")
        
        # Create inherits.yaml
        inherits_content = get_inherits_yaml_template()
        
        # Do simple replacement for org_root
        inherits_content = inherits_content.replace("org_root: ../..", f"org_root: {org_root_rel}")
        
        # If we have selections, we should construct the YAML or replace sections
        # For robustness, let's use a simple YAML dump if we have selections, otherwise template defaults
        if selected_skills or selected_personas or selected_team or selected_lang_skills:
            # Construct dictionary
            config = {
                "org_root": org_root_rel,
                "skills": {
                    "universal": selected_skills,
                    "languages": selected_lang_skills
                },
                "personas": selected_personas,
                "target_agents": target_agents
            }
            if selected_team:
                config["teams"] = [selected_team] # Specification says list?
            
            # Simple YAML dumper to preserve order/format is hard without ruamel.yaml
            # But we can try to be neat.
            import yaml
            # To avoid weird yaml tags/flow style, we construct string manually or use safe_dump
            # Let's use string construction for better comments/formatting control if we care, 
            # or just dump it.
            # Using yaml.safe_dump is safest for validity.
            with open(inherits_yaml, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        else:
            # Use template default
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
    
    except Exception as e:
        _error(f"Unexpected error: {e}", ctx)
        # import traceback
        # traceback.print_exc()
        sys.exit(1)


def _get_available_options(org_root: Path) -> dict:
    """Scan org root for available skills, personas, and teams."""
    options = {
        "skills": [],
        "personas": [],
        "teams": []
    }
    
    # Scan Universal Skills
    skills_dir = org_root / ".agent" / "skills"
    if skills_dir.exists():
        for f in skills_dir.glob("*.md"):
            options["skills"].append(f.stem)
        
        # Scan Language Skills
        for d in skills_dir.iterdir():
            if d.is_dir():
                lang_skills = [f.stem for f in d.glob("*.md")]
                if lang_skills:
                    options[d.name] = lang_skills
    
    # Scan Personas
    personas_dir = org_root / ".agent" / "personas"
    if personas_dir.exists():
        for f in personas_dir.glob("*.md"):
            options["personas"].append(f.stem)
            
    # Scan Teams
    teams_dir = org_root / ".agent" / "memory" / "teams"
    if teams_dir.exists():
        for f in teams_dir.glob("*.md"):
            if f.stem != "_template":
                options["teams"].append(f.stem)
    
    # Sort everything
    for k in options:
        options[k].sort()
        
    return options

def _detect_languages(repo_root: Path) -> set:
    """Detect main languages in the repo."""
    langs = set()
    if (repo_root / "requirements.txt").exists() or (repo_root / "pyproject.toml").exists() or \
       (repo_root / "setup.py").exists() or list(repo_root.glob("*.py")):
        langs.add("python")
    
    if (repo_root / "package.json").exists() or list(repo_root.glob("*.js")) or \
       (repo_root / "node_modules").exists():
        langs.add("javascript")
        
    if (repo_root / "tsconfig.json").exists() or list(repo_root.glob("*.ts")) or \
       list(repo_root.glob("*.tsx")):
        langs.add("typescript")
    
    if (repo_root / "go.mod").exists() or list(repo_root.glob("*.go")):
        langs.add("go")
        
    if (repo_root / "Cargo.toml").exists() or list(repo_root.glob("*.rs")):
        langs.add("rust")
        
    if (repo_root / "pom.xml").exists() or (repo_root / "build.gradle").exists() or \
       list(repo_root.glob("*.java")):
        langs.add("java")
        
    return langs


def _suggest_skills_personas(repo_root: Path) -> dict:
    """Suggest skills and personas based on project files."""
    suggestions = {"skills": [], "personas": []}
    
    # Detect languages/frameworks
    detected_langs = set()
    
    # Check for Python
    if (repo_root / "requirements.txt").exists() or (repo_root / "pyproject.toml").exists() or \
       (repo_root / "setup.py").exists() or list(repo_root.glob("*.py")):
        detected_langs.add("python")
        suggestions["skills"].extend(["django", "fastapi", "pytest"])
        suggestions["personas"].append("backend-developer")
    
    # Check for JavaScript/Node.js
    if (repo_root / "package.json").exists() or list(repo_root.glob("*.js")) or \
       (repo_root / "node_modules").exists():
        detected_langs.add("javascript")
        suggestions["skills"].extend(["react", "nodejs", "jest"])
        suggestions["personas"].extend(["frontend-developer", "backend-developer"])
    
    # Check for TypeScript
    if (repo_root / "tsconfig.json").exists() or list(repo_root.glob("*.ts")) or \
       list(repo_root.glob("*.tsx")):
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
    if (repo_root / "pom.xml").exists() or (repo_root / "build.gradle").exists() or \
       list(repo_root.glob("*.java")):
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
        _create_file(root / ".agent" / "memory" / "constitution.md", get_constitution_md_template())
        _create_file(root / ".agent" / "memory" / "general-context.md", get_general_context_md_template())
        _create_file(root / ".agent" / "memory" / "manifest.yaml", get_manifest_yaml_template(name))
        
        # 4. Teams (template)
        _create_file(root / ".agent" / "memory" / "teams" / "_template.md", get_team_md_template("TEMPLATE"))
        
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
                click.echo(f"Skipped {len(skipped)} existing files (use --force to overwrite):")
                for f in skipped:
                    click.echo(f"  - {f}")
            
            click.echo("\nConsider running: git init && git add . && git commit -m 'Initial org agentic toolkit'")
            
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
             personal_path = Path(sys.modules["os"].environ["AGENT_PERSONAL_FOLDER"]).expanduser().resolve()
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
        _create_file(personal_path / ".agent" / "memory" / "personal-context.md", get_personal_context_md_template())
        
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
                 team = click.prompt("Enter your team name (optional)", default="", show_default=False)
             
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


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
