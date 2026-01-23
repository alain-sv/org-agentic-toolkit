set dotenv-load := true
set export
set shell := ["bash", "-uc"]
nowts:=`date +%Y%m%d_%H%M%S`
YYYYMMDD:= `date +%Y%m%d`


# Show all available commands (default)
default:
    @just --list

# Install dependencies
install:
    uv pip install -e ".[dev]"

# Run tests
test:
    uv run --extra dev pytest tests/

# Run tests with coverage
coverage:
    uv run --extra dev pytest --cov=oat tests/

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov

# Build package for publishing
build:
    python -m pip install --upgrade build
    python -m build

# Publish to PyPI using twine
publish: build
    python -m pip install --upgrade twine
    python -m twine upload dist/*

# Run validation on the current repo
validate:
    oat validate

####
# Development
####    

install_tool:
    uv tool install --editable .

####
# Version bumping
####

# Bump patch version (1.0.0 -> 1.0.1)
bump-patch:
    uv tool run bump-my-version bump patch --config-file pyproject.toml

# Bump minor version (1.0.0 -> 1.1.0)
bump-minor:
    uv tool run bump-my-version bump minor --config-file pyproject.toml

# Bump major version (1.0.0 -> 2.0.0)
bump-major:
    uv tool run bump-my-version bump major --config-file pyproject.toml
