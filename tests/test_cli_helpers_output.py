"""Tests for CLI helpers output module."""

import pytest

from oat.cli_helpers.output import error, generate_table_of_contents


class TestGenerateTableOfContents:
    """Test table of contents generation."""
    
    def test_generate_toc_basic(self):
        """Test basic TOC generation."""
        content = """## Header 1
Some content
### Header 2
More content
#### Header 3
"""
        toc = generate_table_of_contents(content)
        assert "## Table of Contents" in toc
        assert "Header 1" in toc
        assert "Header 2" in toc
        assert "Header 3" in toc
    
    def test_generate_toc_empty(self):
        """Test TOC generation with no headers."""
        content = "Just some text without headers"
        toc = generate_table_of_contents(content)
        assert toc == ""
    
    def test_generate_toc_with_links(self):
        """Test TOC generation with markdown links in headers."""
        content = """## Header with [link](url)
Content
"""
        toc = generate_table_of_contents(content)
        assert "Header with link" in toc or "Header with" in toc


class TestError:
    """Test error output function."""
    
    def test_error_function_exists(self):
        """Test that error function exists and is callable."""
        assert callable(error)
