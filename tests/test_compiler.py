"""Tests for compiler module."""

from pathlib import Path

import pytest

from oat.compiler import compile_document, CompileOptions, CompileError, merge_markdown


class TestCompileDocument:
    """Test document compilation."""
    
    def test_compile_basic(self, tmp_path):
        """Test basic compilation."""
        # Setup org root
        org_root = tmp_path / "org"
        org_root.mkdir()
        (org_root / ".oat-root").write_text("")
        (org_root / ".agent" / "memory").mkdir(parents=True)
        (org_root / ".agent" / "memory" / "constitution.md").write_text(
            "<!-- version: 1.0.0 -->\n# Constitution\nOrg rules."
        )
        (org_root / ".agent" / "skills").mkdir(parents=True)
        (org_root / ".agent" / "skills" / "git.md").write_text("# Git Skills")
        (org_root / ".agent" / "personas").mkdir(parents=True)
        (org_root / ".agent" / "personas" / "backend-developer.md").write_text(
            "# Backend Developer"
        )
        
        # Setup repo
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / "AGENTS.md").write_text("# Agent Instructions")
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("""org_root: ../org
skills:
  universal:
    - git
personas:
  - backend-developer
""")
        (repo_root / ".agent" / "project.md").write_text("# Project Rules")
        
        options = CompileOptions()
        compiled, metadata = compile_document(repo_root, org_root, None, options)
        
        assert "Constitution" in compiled
        assert "Git Skills" in compiled
        assert "Backend Developer" in compiled
        assert "Project Rules" in compiled
        assert metadata["constitution_version"] == "1.0.0"
    
    def test_compile_missing_constitution(self, tmp_path):
        """Test compilation fails when constitution is missing."""
        org_root = tmp_path / "org"
        org_root.mkdir()
        
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".agent").mkdir()
        (repo_root / ".agent" / "inherits.yaml").write_text("""org_root: ../org
skills:
  universal: []
personas: []
""")
        
        options = CompileOptions()
        with pytest.raises(CompileError):
            compile_document(repo_root, org_root, None, options)
    
    def test_compile_with_personal_overlay(self, tmp_path):
        """Test compilation with personal overlay."""
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
        
        # Setup personal overlay (personal_overlay should be the .agent directory)
        personal = tmp_path / "personal" / ".agent"
        (personal / "memory").mkdir(parents=True)
        (personal / "memory" / "personal-context.md").write_text(
            "# Personal Context"
        )
        
        options = CompileOptions()
        compiled, metadata = compile_document(repo_root, org_root, personal, options)
        
        assert "Personal Context" in compiled
        assert metadata["personal_overlay"] == str(personal)


class TestMergeMarkdown:
    """Test markdown merging."""
    
    def test_merge_markdown(self, tmp_path):
        """Test merging multiple markdown sources."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        
        file1 = repo_root / "file1.md"
        file2 = repo_root / "file2.md"
        
        sources = [
            ("Section 1", file1, "Content 1"),
            ("Section 2", file2, "Content 2"),
        ]
        
        result = merge_markdown(sources, repo_root, None)
        
        assert "Section 1" in result
        assert "Section 2" in result
        assert "Content 1" in result
        assert "Content 2" in result
        assert "file1.md" in result
        assert "file2.md" in result
