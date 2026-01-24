"""Output formatting utilities for CLI."""

import json
import re

import click


def error(message: str, ctx):
    """Print error message."""
    if ctx.obj.get("json"):
        click.echo(json.dumps({"error": message}))
    else:
        click.echo(f"Error: {message}", err=True)


def generate_table_of_contents(content: str) -> str:
    """
    Generate a table of contents from markdown headers in the content.
    Uses GitHub-style anchor generation.

    Args:
        content: Markdown content to extract headers from

    Returns:
        Table of contents as markdown, or empty string if no headers found
    """
    lines = []
    headers = []

    # Extract headers (##, ###, ####, etc.)
    for line in content.split("\n"):
        # Match markdown headers (## Header or ### Header)
        match = re.match(r"^(#{2,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))  # Number of # characters
            header_text = match.group(2).strip()
            # Create GitHub-style anchor from header text
            # GitHub anchors: lowercase, replace spaces with hyphens, remove special chars
            anchor = header_text.lower()
            # Remove markdown links and images: [text](url) or ![alt](url)
            anchor = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", anchor)
            anchor = re.sub(r"!\[([^\]]+)\]\([^\)]+\)", r"\1", anchor)
            # Remove special characters except spaces and hyphens
            anchor = re.sub(r"[^\w\s-]", "", anchor)
            # Replace spaces and multiple hyphens with single hyphen
            anchor = re.sub(r"[-\s]+", "-", anchor)
            anchor = anchor.strip("-")
            headers.append((level, header_text, anchor))

    if not headers:
        return ""

    # Generate TOC
    lines.append("## Table of Contents")
    lines.append("")

    for level, header_text, anchor in headers:
        indent = "  " * (
            level - 2
        )  # Indent based on header level (## = 0, ### = 2, etc.)
        lines.append(f"{indent}- [{header_text}](#{anchor})")

    return "\n".join(lines)
