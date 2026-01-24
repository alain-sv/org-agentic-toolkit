"""Tests for CLI helpers file creation module."""

import pytest
from pathlib import Path

from oat.cli_helpers.file_creation import (
    parse_missing_file,
    determine_file_type_and_path,
    get_template_content,
)


class TestParseMissingFile:
    """Test missing file parsing."""
    
    def test_parse_language_skill(self):
        """Test parsing language skill missing file."""
        result = parse_missing_file("❌ MISSING: python/django")
        assert result["file_type"] == "language_skill"
        assert result["name"] == "django"
        assert result["language"] == "python"
        assert result["relative_path"] == "skills/python/django.md"
    
    def test_parse_constitution(self):
        """Test parsing constitution missing file."""
        result = parse_missing_file("❌ MISSING: Constitution: /path/to/constitution.md")
        assert result["file_type"] == "constitution"
        assert result["name"] == "constitution"
        assert result["relative_path"] == "memory/constitution.md"
    
    def test_parse_team(self):
        """Test parsing team missing file."""
        result = parse_missing_file("❌ MISSING: platform")
        assert result["file_type"] == "unknown"
        assert result["name"] == "platform"


class TestDetermineFileTypeAndPath:
    """Test file type and path determination."""
    
    def test_determine_team(self, tmp_path):
        """Test determining team file type."""
        repo_root = tmp_path / "repo"
        org_root = tmp_path / "org"
        result = determine_file_type_and_path(
            "platform", repo_root, org_root, None,
            ["platform"], [], []
        )
        assert result["file_type"] == "team"
        assert result["relative_path"] == "memory/teams/platform.md"
    
    def test_determine_skill(self, tmp_path):
        """Test determining skill file type."""
        repo_root = tmp_path / "repo"
        org_root = tmp_path / "org"
        result = determine_file_type_and_path(
            "git", repo_root, org_root, None,
            [], ["git"], []
        )
        assert result["file_type"] == "universal_skill"
        assert result["relative_path"] == "skills/git.md"
    
    def test_determine_persona(self, tmp_path):
        """Test determining persona file type."""
        repo_root = tmp_path / "repo"
        org_root = tmp_path / "org"
        result = determine_file_type_and_path(
            "backend-developer", repo_root, org_root, None,
            [], [], ["backend-developer"]
        )
        assert result["file_type"] == "persona"
        assert result["relative_path"] == "personas/backend-developer.md"


class TestGetTemplateContent:
    """Test template content retrieval."""
    
    def test_get_template_content_team(self):
        """Test getting team template content."""
        content, is_placeholder = get_template_content("team", "test-team")
        assert isinstance(content, str)
        assert "Team: test-team" in content or is_placeholder
    
    def test_get_template_content_constitution(self):
        """Test getting constitution template content."""
        content, is_placeholder = get_template_content("constitution")
        assert isinstance(content, str)
        assert len(content) > 0
