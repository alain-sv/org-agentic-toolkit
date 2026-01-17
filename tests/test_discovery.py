"""Tests for discovery module."""

import os
import tempfile
from pathlib import Path

import pytest

from oat.discovery import find_repo_root, find_org_root, find_personal_overlay, get_org_root_name


class TestFindRepoRoot:
    """Test repo root discovery."""
    
    def test_find_repo_root_by_git(self, tmp_path):
        """Test finding repo root by .git directory."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        
        subdir = repo_root / "sub" / "dir"
        subdir.mkdir(parents=True)
        
        result = find_repo_root(cwd=subdir)
        assert result == repo_root.resolve()
    
    def test_find_repo_root_by_inherits(self, tmp_path):
        """Test finding repo root by .agent/inherits.yaml."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("org_root: ../..")
        
        subdir = repo_root / "sub" / "dir"
        subdir.mkdir(parents=True)
        
        result = find_repo_root(cwd=subdir)
        assert result == repo_root.resolve()
    
    def test_find_repo_root_explicit_path(self, tmp_path):
        """Test finding repo root with explicit path."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        
        result = find_repo_root(explicit_path=repo_root)
        assert result == repo_root.resolve()
    
    def test_find_repo_root_not_found(self, tmp_path):
        """Test when repo root is not found."""
        some_dir = tmp_path / "some" / "dir"
        some_dir.mkdir(parents=True)
        
        result = find_repo_root(cwd=some_dir)
        assert result is None


class TestFindOrgRoot:
    """Test org root discovery."""
    
    def test_find_org_root_relative_path(self, tmp_path):
        """Test finding org root with relative path."""
        repo_root = tmp_path / "repo"
        org_root = tmp_path / "org"
        repo_root.mkdir()
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("version: 1.0.0")
        
        inherits_config = {"org_root": "../org"}
        
        result = find_org_root(repo_root, inherits_config)
        assert result == org_root.resolve()
    
    def test_find_org_root_env_var(self, tmp_path, monkeypatch):
        """Test finding org root via OAT_ROOT env var."""
        org_root = tmp_path / "org"
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("version: 1.0.0")
        
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        
        monkeypatch.setenv("OAT_ROOT", str(org_root))
        
        inherits_config = {"org_root": "../other"}
        result = find_org_root(repo_root, inherits_config)
        assert result == org_root.resolve()
    
    def test_find_org_root_absolute_path_forbidden(self, tmp_path):
        """Test that absolute paths in org_root are rejected."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        
        inherits_config = {"org_root": "/absolute/path"}
        
        result = find_org_root(repo_root, inherits_config)
        assert result is None


class TestFindPersonalOverlay:
    """Test personal overlay discovery."""
    
    def test_find_personal_overlay_env_var(self, tmp_path, monkeypatch):
        """Test finding personal overlay via env var."""
        personal_dir = tmp_path / "personal"
        personal_dir.mkdir()
        
        monkeypatch.setenv("AGENT_PERSONAL_FOLDER", str(personal_dir))
        
        result = find_personal_overlay()
        assert result == personal_dir.resolve()
    
    def test_find_personal_overlay_default(self, tmp_path, monkeypatch):
        """Test finding personal overlay at default location."""
        home = tmp_path / "home"
        personal_dir = home / ".agent"
        personal_dir.mkdir(parents=True)
        
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.delenv("AGENT_PERSONAL_FOLDER", raising=False)
        
        result = find_personal_overlay()
        assert result == personal_dir.resolve()
    
    def test_find_personal_overlay_not_found(self, tmp_path, monkeypatch):
        """Test when personal overlay is not found."""
        home = tmp_path / "home"
        home.mkdir()
        
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.delenv("AGENT_PERSONAL_FOLDER", raising=False)
        
        result = find_personal_overlay()
        assert result is None


class TestGetOrgRootName:
    """Test org root name resolution."""
    
    def test_get_org_root_name_from_env(self, monkeypatch):
        """Test getting org root name from env var."""
        monkeypatch.setenv("ORG_AGENTIC_TOOLKIT_ROOT_NAME", "custom-name")
        
        result = get_org_root_name()
        assert result == "custom-name"
    
    def test_get_org_root_name_from_orgname(self, monkeypatch):
        """Test getting org root name from ORGNAME."""
        monkeypatch.delenv("ORG_AGENTIC_TOOLKIT_ROOT_NAME", raising=False)
        monkeypatch.setenv("ORGNAME", "myorg")
        
        result = get_org_root_name()
        assert result == "myorg-agentic-toolkit"
