"""Tests for config module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from oat.config import (
    load_inherits_yaml,
    load_memory_manifest,
    load_targets_yaml,
    validate_inherits_structure,
    get_skills_from_config,
    get_personas_from_config,
    get_teams_from_config,
    ConfigError,
)


class TestLoadInheritsYaml:
    """Test loading inherits.yaml."""
    
    def test_load_valid_inherits(self, tmp_path):
        """Test loading valid inherits.yaml."""
        inherits_path = tmp_path / "inherits.yaml"
        config = {
            "org_root": "../..",
            "skills": {
                "universal": ["git", "test"],
                "languages": {"python": ["django"]}
            },
            "personas": ["backend-developer"]
        }
        inherits_path.write_text(yaml.dump(config))
        
        result = load_inherits_yaml(inherits_path)
        assert result == config
    
    def test_load_missing_file(self, tmp_path):
        """Test loading non-existent file."""
        inherits_path = tmp_path / "missing.yaml"
        
        with pytest.raises(ConfigError):
            load_inherits_yaml(inherits_path)
    
    def test_load_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML."""
        inherits_path = tmp_path / "invalid.yaml"
        inherits_path.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ConfigError):
            load_inherits_yaml(inherits_path)


class TestLoadMemoryManifest:
    """Test loading memory manifest."""
    
    def test_load_valid_manifest(self, tmp_path):
        """Test loading valid manifest."""
        manifest_path = tmp_path / "manifest.yaml"
        manifest = {
            "name": "test",
            "version": "1.0.0",
            "constitution": "constitution.md"
        }
        manifest_path.write_text(yaml.dump(manifest))
        
        result = load_memory_manifest(manifest_path)
        assert result == manifest
    
    def test_load_missing_manifest(self, tmp_path):
        """Test loading non-existent manifest (should return None)."""
        manifest_path = tmp_path / "missing.yaml"
        
        result = load_memory_manifest(manifest_path)
        assert result is None


class TestLoadTargetsYaml:
    """Test loading targets.yaml."""
    
    def test_load_valid_targets(self, tmp_path):
        """Test loading valid targets.yaml."""
        targets_path = tmp_path / "targets.yaml"
        targets = {
            "targets": {
                "cursor": ".cursorrules",
                "windsurf": ".windsurfrules"
            }
        }
        targets_path.write_text(yaml.dump(targets))
        
        result = load_targets_yaml(targets_path)
        assert result == targets["targets"]
    
    def test_load_missing_targets(self, tmp_path):
        """Test loading non-existent targets (should return empty dict)."""
        targets_path = tmp_path / "missing.yaml"
        
        result = load_targets_yaml(targets_path)
        assert result == {}


class TestValidateInheritsStructure:
    """Test inherits.yaml structure validation."""
    
    def test_valid_structure(self):
        """Test valid structure passes."""
        config = {
            "org_root": "../..",
            "skills": {
                "universal": ["git"],
                "languages": {"python": ["django"]}
            },
            "personas": ["backend-developer"]
        }
        
        errors = validate_inherits_structure(config)
        assert len(errors) == 0
    
    def test_missing_org_root(self):
        """Test missing org_root is detected."""
        config = {
            "skills": {"universal": ["git"]},
            "personas": ["backend-developer"]
        }
        
        errors = validate_inherits_structure(config)
        assert any("org_root" in e.lower() for e in errors)
    
    def test_missing_skills(self):
        """Test missing skills is detected."""
        config = {
            "org_root": "../..",
            "personas": ["backend-developer"]
        }
        
        errors = validate_inherits_structure(config)
        assert any("skills" in e.lower() for e in errors)
    
    def test_absolute_path_forbidden(self):
        """Test absolute paths are rejected."""
        config = {
            "org_root": "/absolute/path",
            "skills": {"universal": ["git"]},
            "personas": ["backend-developer"]
        }
        
        errors = validate_inherits_structure(config)
        assert any("relative" in e.lower() or "absolute" in e.lower() for e in errors)


class TestGetSkillsFromConfig:
    """Test extracting skills from config."""
    
    def test_get_skills(self):
        """Test extracting skills."""
        config = {
            "skills": {
                "universal": ["git", "test"],
                "languages": {"python": ["django"], "javascript": ["react"]}
            }
        }
        
        result = get_skills_from_config(config)
        assert result["universal"] == ["git", "test"]
        assert result["languages"]["python"] == ["django"]
        assert result["languages"]["javascript"] == ["react"]


class TestGetPersonasFromConfig:
    """Test extracting personas from config."""
    
    def test_get_personas(self):
        """Test extracting personas."""
        config = {
            "personas": ["backend-developer", "frontend-developer"]
        }
        
        result = get_personas_from_config(config)
        assert result == ["backend-developer", "frontend-developer"]


class TestGetTeamsFromConfig:
    """Test extracting teams from config."""
    
    def test_get_teams(self):
        """Test extracting teams."""
        config = {
            "teams": ["platform", "product"]
        }
        
        result = get_teams_from_config(config)
        assert result == ["platform", "product"]
    
    def test_get_teams_missing(self):
        """Test extracting teams when not specified."""
        config = {}
        
        result = get_teams_from_config(config)
        assert result == []
