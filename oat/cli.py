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
    get_sub_agents_from_config,
    get_teams_from_config,
    ConfigError,
)
from oat.compiler import compile_document, CompileOptions, CompileError
from oat.validator import validate_repo, ValidationResult
from oat.templates import (
    get_agents_md_template,
    get_inherits_yaml_template,
    get_project_md_template,
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
@click.option("--include-sub-agent", "include_sub_agents", multiple=True, help="Additionally include a sub-agent")
@click.option("--exclude-sub-agent", "exclude_sub_agents", multiple=True, help="Exclude a sub-agent from manifest")
@click.option("--repo", type=click.Path(exists=True), help="Explicit repo root path")
@click.pass_context
def compile(ctx, output_path, target, watch, no_personal, print_output, include_hash, diff, strict,
            include_skills, exclude_skills, include_sub_agents, exclude_sub_agents, repo):
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
            include_sub_agents=list(include_sub_agents),
            exclude_sub_agents=list(exclude_sub_agents),
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
        repo_root = find_repo_root(explicit_path=Path(repo) if repo else None)
        if not repo_root:
            _error("Could not find repo root. Run from inside a repository or use --repo.", ctx)
            sys.exit(1)
        
        result = validate_repo(repo_root, strict=strict)
        
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
        sub_agents_list = get_sub_agents_from_config(inherits_config)
        teams_list = get_teams_from_config(inherits_config)
        
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
            "sub_agents": sub_agents_list,
            "teams": teams_list,
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
        
        available_sub_agents = set()
        if (org_root / ".agent" / "sub-agents").exists():
            for sub_agent_file in (org_root / ".agent" / "sub-agents").glob("*.md"):
                available_sub_agents.add(sub_agent_file.stem)
        
        included_skills = set(skills_config.get("universal", []))
        for lang_skills in skills_config.get("languages", {}).values():
            included_skills.update(lang_skills)
        
        info["available_but_not_included"] = {
            "skills": sorted(available_skills - included_skills),
            "sub_agents": sorted(available_sub_agents - set(sub_agents_list)),
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
            click.echo(f"  Sub-Agents ({len(info['sub_agents'])}): {', '.join(info['sub_agents'])}")
            if info["teams"]:
                click.echo(f"  Teams: {', '.join(info['teams'])}")
            if info["project_rules"]:
                click.echo(f"  Project Rules: {info['project_rules']}")
            if info["personal_overlay"]:
                click.echo(f"  Personal Overlay: {info['personal_overlay']}")
            else:
                click.echo("  Personal Overlay: Not found")
            
            if info["available_but_not_included"]["skills"] or info["available_but_not_included"]["sub_agents"]:
                click.echo("\nAvailable but not included:")
                if info["available_but_not_included"]["skills"]:
                    click.echo(f"  Skills: {', '.join(info['available_but_not_included']['skills'])}")
                if info["available_but_not_included"]["sub_agents"]:
                    click.echo(f"  Sub-Agents: {', '.join(info['available_but_not_included']['sub_agents'])}")
    
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
@click.option("--suggest", is_flag=True, help="Suggest skills/sub-agents based on project files")
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
        # Replace org_root placeholder
        inherits_content = inherits_content.replace("org_root: ../..", f"org_root: {org_root_rel}")
        
        # If suggest mode, scan project and suggest skills/sub-agents
        if suggest:
            suggestions = _suggest_skills_sub_agents(repo_root)
            if suggestions:
                # Modify inherits_content with suggestions
                # This is a simplified version - in practice, you'd parse YAML, modify, and re-serialize
                if not ctx.obj["quiet"]:
                    click.echo("\nSuggested skills/sub-agents based on project files:")
                    if suggestions.get("skills"):
                        click.echo(f"  Skills: {', '.join(suggestions['skills'])}")
                    if suggestions.get("sub_agents"):
                        click.echo(f"  Sub-Agents: {', '.join(suggestions['sub_agents'])}")
        
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
        sys.exit(1)


def _suggest_skills_sub_agents(repo_root: Path) -> dict:
    """Suggest skills and sub-agents based on project files."""
    suggestions = {"skills": [], "sub_agents": []}
    
    # Detect languages/frameworks
    detected_langs = set()
    
    # Check for Python
    if (repo_root / "requirements.txt").exists() or (repo_root / "pyproject.toml").exists() or \
       (repo_root / "setup.py").exists() or list(repo_root.glob("*.py")):
        detected_langs.add("python")
        suggestions["skills"].extend(["django", "fastapi", "pytest"])
        suggestions["sub_agents"].append("backend-developer")
    
    # Check for JavaScript/Node.js
    if (repo_root / "package.json").exists() or list(repo_root.glob("*.js")) or \
       (repo_root / "node_modules").exists():
        detected_langs.add("javascript")
        suggestions["skills"].extend(["react", "nodejs", "jest"])
        suggestions["sub_agents"].extend(["frontend-developer", "backend-developer"])
    
    # Check for TypeScript
    if (repo_root / "tsconfig.json").exists() or list(repo_root.glob("*.ts")) or \
       list(repo_root.glob("*.tsx")):
        detected_langs.add("typescript")
        suggestions["skills"].extend(["angular", "nestjs"])
    
    # Check for Go
    if (repo_root / "go.mod").exists() or list(repo_root.glob("*.go")):
        detected_langs.add("go")
        suggestions["skills"].extend(["gin", "testing"])
        suggestions["sub_agents"].append("backend-developer")
    
    # Check for Rust
    if (repo_root / "Cargo.toml").exists() or list(repo_root.glob("*.rs")):
        detected_langs.add("rust")
        suggestions["skills"].extend(["cargo", "testing"])
        suggestions["sub_agents"].append("backend-developer")
    
    # Check for Java
    if (repo_root / "pom.xml").exists() or (repo_root / "build.gradle").exists() or \
       list(repo_root.glob("*.java")):
        detected_langs.add("java")
        suggestions["skills"].extend(["spring", "maven"])
        suggestions["sub_agents"].append("backend-developer")
    
    # Always suggest universal skills
    suggestions["skills"].extend(["git", "test", "db", "review-checklist"])
    
    # Always suggest tech-lead
    suggestions["sub_agents"].append("tech-lead")
    
    # Remove duplicates
    suggestions["skills"] = list(set(suggestions["skills"]))
    suggestions["sub_agents"] = list(set(suggestions["sub_agents"]))
    
    return suggestions


def _error(message: str, ctx):
    """Print error message."""
    if ctx.obj.get("json"):
        click.echo(json.dumps({"error": message}))
    else:
        click.echo(f"Error: {message}", err=True)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
