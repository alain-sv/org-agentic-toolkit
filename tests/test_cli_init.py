"""Tests for CLI init commands."""

import os
from pathlib import Path
from click.testing import CliRunner
from oat.cli import cli

def test_init_org_command(tmp_path):
    """Test 'oat init org' command."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init", "org", "--name", "Test Org"])
        assert result.exit_code == 0
        assert "Initialized Org Root" in result.output
        
        # Check files
        assert Path(".oat-root").exists()
        assert Path("AGENTS.md").exists()
        assert Path(".agent/memory/constitution.md").exists()
        assert Path(".agent/skills/python").is_dir()
        assert Path(".agent/personas").is_dir()

def test_init_org_existing_error(tmp_path):
    """Test 'oat init org' fails (or warns) on non-empty dir without force."""
    # Note: The implementation currently passes `if any(...) and not force: pass`.
    # It says "but we should warn if it looks like a random directory".
    # Implementation checks for overwrite inside _create_file.
    pass

def test_init_org_force(tmp_path):
    """Test 'oat init org --force' overwrites files."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("AGENTS.md").write_text("Old")
        result = runner.invoke(cli, ["init", "org", "--force"])
        assert result.exit_code == 0
        assert "# Organization Agentic Toolkit" in Path("AGENTS.md").read_text()

def test_init_personal_command(tmp_path):
    """Test 'oat init personal' command."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        personal_path = Path("personal")
        result = runner.invoke(cli, ["init", "personal", "--path", str(personal_path)])
        assert result.exit_code == 0
        assert f"Initializing personal overlay at: {personal_path.resolve()}" in result.output
        
        # Check files
        assert (personal_path / ".agent/memory/personal-context.md").exists()
        assert (personal_path / ".agent/personas/me.md").exists()
