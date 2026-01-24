"""Tests for constants module."""

from oat.constants import (
    MAINTENANCE_COMMENT,
    CRITICAL_NOTICE_WITH_NL,
    CRITICAL_NOTICE_WITHOUT_NL,
)


def test_maintenance_comment():
    """Test maintenance comment constant."""
    assert MAINTENANCE_COMMENT.startswith("# This file is maintained by oat")
    assert "https://github.com/alain-sv/org-agentic-toolkit" in MAINTENANCE_COMMENT
    assert MAINTENANCE_COMMENT.endswith("\n\n")


def test_critical_notice_with_nl():
    """Test critical notice with newline constant."""
    assert CRITICAL_NOTICE_WITH_NL == "> CRITICAL: Read AGENTS.compiled.md first.\n\n"
    assert CRITICAL_NOTICE_WITH_NL.endswith("\n\n")


def test_critical_notice_without_nl():
    """Test critical notice without trailing newline constant."""
    assert CRITICAL_NOTICE_WITHOUT_NL == "> CRITICAL: Read AGENTS.compiled.md first.\n"
    assert CRITICAL_NOTICE_WITHOUT_NL.endswith("\n")
    assert not CRITICAL_NOTICE_WITHOUT_NL.endswith("\n\n")
