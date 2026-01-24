"""Tests for CLI helpers compile summary module."""

import pytest
from pathlib import Path

from oat.cli_helpers.compile_summary import (
    find_file_in_locations,
    generate_compile_summary,
)
from oat.compiler import CompileOptions


class TestFindFileInLocations:
    """Test finding files in locations."""
    
    def test_find_in_personal(self, tmp_path):
        """Test finding file in personal overlay."""
        personal = tmp_path / "personal"
        org_root = tmp_path / "org"
        repo_root = tmp_path / "repo"
        
        # Create file in personal
        (personal / "skills").mkdir(parents=True)
        (personal / "skills" / "test.md").write_text("# Test")
        
        found_path, locations = find_file_in_locations(
            "skills/test.md", personal, org_root, repo_root
        )
        assert found_path is not None
        assert len(locations) > 0
        assert locations[0][0] == "personal"
    
    def test_find_in_org(self, tmp_path):
        """Test finding file in org root."""
        personal = None
        org_root = tmp_path / "org"
        repo_root = tmp_path / "repo"
        
        # Create file in org
        (org_root / ".agent" / "skills").mkdir(parents=True)
        (org_root / ".agent" / "skills" / "test.md").write_text("# Test")
        
        found_path, locations = find_file_in_locations(
            "skills/test.md", personal, org_root, repo_root
        )
        assert found_path is not None
        assert len(locations) > 0
        assert locations[0][0] == "org"
    
    def test_find_not_found(self, tmp_path):
        """Test finding file that doesn't exist."""
        personal = None
        org_root = tmp_path / "org"
        repo_root = tmp_path / "repo"
        
        found_path, locations = find_file_in_locations(
            "skills/nonexistent.md", personal, org_root, repo_root
        )
        assert found_path is None
        assert len(locations) == 0


class TestGenerateCompileSummary:
    """Test compile summary generation."""
    
    def test_generate_summary_basic(self, tmp_path):
        """Test basic summary generation."""
        repo_root = tmp_path / "repo"
        org_root = tmp_path / "org"
        
        # Setup basic structure
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text("# Constitution")
        
        inherits_config = {
            "org_root": "../org",
            "skills": {"universal": []},
            "personas": [],
        }
        options = CompileOptions()
        output_path = repo_root / "AGENTS.compiled.md"
        
        summary = generate_compile_summary(
            repo_root, org_root, None, inherits_config, options, output_path
        )
        
        assert "Constitution" in summary
        assert "Output:" in summary
