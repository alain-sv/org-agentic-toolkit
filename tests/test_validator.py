"""Tests for validator module."""

from pathlib import Path

import pytest

from oat.validator import validate_repo, validate_org_root, validate_personal_overlay, ValidationResult


class TestValidateRepo:
    """Test repository validation."""
    
    def test_validate_valid_repo(self, tmp_path):
        """Test validation of valid repository."""
        # Setup org root
        org_root = tmp_path / "org"
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("# Constitution")
        (org_root / ".agent" / "skills").mkdir(parents=True)
        (org_root / ".agent" / "skills" / "git.md").write_text("# Git")
        (org_root / ".agent" / "personas").mkdir(parents=True)
        (org_root / ".agent" / "personas" / "backend-developer.md").write_text(
            "# Backend Developer"
        )
        
        # Setup repo
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / "AGENTS.md").write_text("# Agents")
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("""org_root: ../org
skills:
  universal:
    - git
personas:
  - backend-developer
""")
        (repo_root / ".agent" / "project.md").write_text("# Project")
        
        result = validate_repo(repo_root)
        assert result.is_valid()
        assert len(result.errors) == 0
    
    def test_validate_missing_inherits(self, tmp_path):
        """Test validation fails when inherits.yaml is missing."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        
        result = validate_repo(repo_root)
        assert not result.is_valid()
        assert any("inherits.yaml" in e.message for e in result.errors)
    
    def test_validate_missing_skills_section(self, tmp_path):
        """Test validation fails when skills section is missing."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("""org_root: ../org
personas: []
""")
        
        result = validate_repo(repo_root)
        assert not result.is_valid()
        assert any("skills" in e.message.lower() for e in result.errors)
    
    def test_validate_missing_skill_file(self, tmp_path):
        """Test validation fails when referenced skill file is missing."""
        # Setup org root
        org_root = tmp_path / "org"
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("# Constitution")
        (org_root / ".agent" / "skills").mkdir(parents=True)
        (org_root / ".agent" / "personas").mkdir(parents=True)
        
        # Setup repo
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("""org_root: ../org
skills:
  universal:
    - missing-skill
personas: []
""")
        
        result = validate_repo(repo_root)
        assert not result.is_valid()
        assert any("missing-skill" in e.message for e in result.errors)
    
    def test_validate_missing_project_md_warning(self, tmp_path):
        """Test validation warns when project.md is missing."""
        # Setup org root
        org_root = tmp_path / "org"
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("# Constitution")
        (org_root / ".agent" / "skills").mkdir(parents=True)
        (org_root / ".agent" / "personas").mkdir(parents=True)
        
        # Setup repo
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("""org_root: ../org
skills:
  universal: []
personas: []
""")
        
        result = validate_repo(repo_root, strict=False)
        assert result.is_valid()  # No errors, but warnings
        assert any("project.md" in w.message.lower() for w in result.warnings)
    
    def test_validate_strict_mode(self, tmp_path):
        """Test strict mode treats warnings as errors."""
        # Setup org root
        org_root = tmp_path / "org"
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("# Constitution")
        (org_root / ".agent" / "skills").mkdir(parents=True)
        (org_root / ".agent" / "personas").mkdir(parents=True)
        
        # Setup repo
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("""org_root: ../org
skills:
  universal: []
personas: []
""")
        
        result = validate_repo(repo_root, strict=True)
        assert not result.is_valid()  # Warnings become errors
        assert any("project.md" in e.message.lower() for e in result.errors)


class TestValidateOrgRoot:
    """Test org root validation."""
    
    def test_validate_valid_org(self, tmp_path):
        """Test validation of valid org root."""
        org_root = tmp_path / "org"
        org_root.mkdir()
        
        # Create required files
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("# Constitution")
        (org_root / ".agent" / "skills").mkdir(parents=True)
        (org_root / ".agent" / "personas").mkdir(parents=True)
        
        result = validate_org_root(org_root)
        assert result.is_valid()
    
    def test_validate_missing_constitution(self, tmp_path):
        """Test validation fails when constitution is missing."""
        org_root = tmp_path / "org"
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        
        result = validate_org_root(org_root)
        assert not result.is_valid()
        assert any("Constitution" in e.message for e in result.errors)


class TestValidatePersonalOverlay:
    """Test personal overlay validation."""
    
    def test_validate_valid_personal(self, tmp_path):
        """Test validation of valid personal overlay."""
        home = tmp_path / "home"
        overlay = home / ".agent"
        overlay.mkdir(parents=True)
        
        (overlay / "memory").mkdir(parents=True)
        (overlay / "memory" / "personal-context.md").write_text("# About Me")
        
        result = validate_personal_overlay(overlay)
        assert result.is_valid()
    
    def test_validate_missing_overlay(self, tmp_path):
        """Test validation fails when overlay directory doesn't exist."""
        result = validate_personal_overlay(tmp_path / "nonexistent")
        assert not result.is_valid()
        assert any("does not exist" in e.message for e in result.errors)
