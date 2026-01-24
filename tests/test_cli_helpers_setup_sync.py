"""Tests for CLI helpers setup sync module."""

import pytest
from pathlib import Path

from oat.cli_helpers.setup_sync import (
    get_available_options,
    detect_languages,
    suggest_skills_personas,
)


class TestGetAvailableOptions:
    """Test getting available options from templates."""
    
    def test_get_available_options(self):
        """Test that options are returned."""
        options = get_available_options()
        assert isinstance(options, dict)
        assert "skills" in options
        assert "personas" in options
        assert "teams" in options


class TestDetectLanguages:
    """Test language detection."""
    
    def test_detect_python(self, tmp_path):
        """Test detecting Python."""
        (tmp_path / "requirements.txt").write_text("requests==2.0.0")
        langs = detect_languages(tmp_path)
        assert "python" in langs
    
    def test_detect_javascript(self, tmp_path):
        """Test detecting JavaScript."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        langs = detect_languages(tmp_path)
        assert "javascript" in langs
    
    def test_detect_go(self, tmp_path):
        """Test detecting Go."""
        (tmp_path / "go.mod").write_text("module test")
        langs = detect_languages(tmp_path)
        assert "go" in langs
    
    def test_detect_multiple(self, tmp_path):
        """Test detecting multiple languages."""
        (tmp_path / "requirements.txt").write_text("requests")
        (tmp_path / "package.json").write_text('{"name": "test"}')
        langs = detect_languages(tmp_path)
        assert "python" in langs
        assert "javascript" in langs


class TestSuggestSkillsPersonas:
    """Test skill and persona suggestions."""
    
    def test_suggest_python(self, tmp_path):
        """Test suggesting for Python project."""
        (tmp_path / "requirements.txt").write_text("django")
        suggestions = suggest_skills_personas(tmp_path)
        assert "django" in suggestions["skills"] or "fastapi" in suggestions["skills"]
        assert "backend-developer" in suggestions["personas"]
    
    def test_suggest_javascript(self, tmp_path):
        """Test suggesting for JavaScript project."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        suggestions = suggest_skills_personas(tmp_path)
        assert "react" in suggestions["skills"] or "nodejs" in suggestions["skills"]
    
    def test_suggest_always_includes(self, tmp_path):
        """Test that certain suggestions are always included."""
        suggestions = suggest_skills_personas(tmp_path)
        assert "git" in suggestions["skills"]
        assert "tech-lead" in suggestions["personas"]
