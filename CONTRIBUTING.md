# Contributing to Org Agentic Toolkit

Thank you for your interest in contributing to the Org Agentic Toolkit (OAT)! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)
- [Adding New Features](#adding-new-features)

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions. We welcome contributions from everyone.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/org_agentic_toolkit.git
   cd org_agentic_toolkit
   ```

3. **Set up the upstream remote**:
   ```bash
   git remote add upstream https://github.com/alain-sv/org_agentic_toolkit.git
   ```

## Development Setup

### Prerequisites

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package installer and resolver
- **Git**

### Installation

1. **Install dependencies**:
   ```bash
   just install
   # or manually:
   uv pip install -e ".[dev]"
   ```

2. **Verify installation**:
   ```bash
   oat --version
   ```

### Development Commands

The project uses a `justfile` for common tasks:

```bash
# Show all available commands
just

# Run tests
just test

# Run tests with coverage
just coverage

# Run validation on current repo
just validate

# Clean build artifacts
just clean

# Build package
just build
```

## Project Structure

```
org_agentic_toolkit/
├── oat/                    # Main package
│   ├── __init__.py
│   ├── cli.py              # CLI commands (Click)
│   ├── compiler.py         # Compilation engine
│   ├── config.py           # YAML configuration loading
│   ├── discovery.py        # Root discovery logic
│   ├── template_manager.py # Template management
│   ├── validator.py        # Validation logic
│   └── templates/          # Package data (templates)
│       ├── toolkit/
│       ├── skills/
│       ├── personas/
│       └── ...
├── tests/                  # Test suite
│   ├── test_cli_init.py
│   ├── test_compiler.py
│   ├── test_config.py
│   ├── test_discovery.py
│   └── test_validator.py
├── pyproject.toml          # Package configuration
├── justfile               # Development commands
└── README.md
```

## Development Workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the [Code Style](#code-style) guidelines

3. **Run tests** to ensure everything works:
   ```bash
   just test
   ```

4. **Run validation** to check the repo configuration:
   ```bash
   just validate
   ```

5. **Commit your changes** with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "Add feature: description of what you did"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

## Testing

### Running Tests

```bash
# Run all tests
just test

# Run with coverage
just coverage

# Run specific test file
uv run --extra dev pytest tests/test_compiler.py

# Run specific test
uv run --extra dev pytest tests/test_compiler.py::test_specific_function
```

### Writing Tests

- Tests use **pytest**
- Test files should be named `test_*.py`
- Test functions should be named `test_*`
- Place tests in the `tests/` directory
- Follow the existing test structure and patterns

### Test Coverage

Aim for high test coverage, especially for:
- Core compilation logic (`compiler.py`)
- Configuration loading (`config.py`)
- Validation logic (`validator.py`)
- Discovery mechanisms (`discovery.py`)

## Code Style

### Python Style

- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Keep functions focused and small
- Add docstrings for public functions and classes

### Formatting

The project doesn't enforce a specific formatter, but please:
- Use consistent indentation (4 spaces)
- Keep lines under 100 characters when possible
- Use meaningful variable and function names

### Imports

- Group imports: standard library, third-party, local
- Use absolute imports
- Sort imports alphabetically within groups

Example:
```python
import json
import sys
from pathlib import Path

import click
import yaml

from oat.compiler import compile_document
from oat.config import load_inherits_yaml
```

### Error Handling

- Use specific exception types
- Provide clear error messages
- Handle errors at appropriate levels

### Documentation

- Add docstrings to public functions and classes
- Use clear, concise language
- Include parameter and return type information when using type hints

## Submitting Changes

### Pull Request Guidelines

1. **Keep PRs focused**: One feature or fix per PR
2. **Write clear descriptions**: Explain what and why, not just how
3. **Reference issues**: Link to related issues if applicable
4. **Update documentation**: Update README or docs if needed
5. **Add tests**: Include tests for new features or bug fixes
6. **Ensure tests pass**: All tests must pass before merging

### PR Template

When creating a PR, include:

- **Description**: What does this PR do?
- **Type**: Feature, Bug Fix, Documentation, Refactoring
- **Testing**: How was this tested?
- **Breaking Changes**: Are there any breaking changes?

### Commit Messages

Write clear, descriptive commit messages:

```
Add feature: support for custom target output paths

- Add --output-path option to compile command
- Update documentation
- Add tests for new functionality
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Document complex logic with inline comments
- Keep comments up-to-date with code changes

### User Documentation

- Update `README.md` for user-facing changes
- Add examples for new features
- Update CLI help text if adding new commands

### Internal Documentation

- Document design decisions in code comments
- Update this CONTRIBUTING.md if processes change

## Adding New Features

### Before You Start

1. **Check existing issues**: See if someone else is working on it
2. **Open an issue**: Discuss the feature before implementing
3. **Get feedback**: Ensure the feature aligns with project goals

### Implementation Steps

1. **Design**: Plan the feature and its integration points
2. **Implement**: Write code following project standards
3. **Test**: Add comprehensive tests
4. **Document**: Update relevant documentation
5. **Validate**: Run `oat validate` to ensure configuration is valid

### Adding CLI Commands

1. Add command to `oat/cli.py` using Click decorators
2. Implement the command logic
3. Add tests in `tests/test_cli_*.py`
4. Update `README.md` with command documentation
5. Update help text and examples

### Adding Templates

1. Add template files to `oat/templates/`
2. Update `template_manager.py` if needed
3. Test template loading and compilation
4. Document template usage

### Adding Skills/Personas

1. Create markdown files in appropriate `oat/templates/` subdirectories
2. Follow existing template structure
3. Test compilation with new skills/personas
4. Update documentation if needed

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues and discussions
- Review the README for usage examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
