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

# Run validation on the current repo
validate:
    oat validate

####
# Development
####    

install_tool:
    uv tool install --editable .
