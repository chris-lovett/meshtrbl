# Packaging Guide for meshtrbl

This guide explains how to package and distribute the **meshtrbl** (Mesh Troubleshooter) - an AI-powered troubleshooting agent for Kubernetes and Consul service mesh.

## Package Structure

The project is configured as a proper Python package with:
- `setup.py` - Traditional setup configuration
- `pyproject.toml` - Modern Python packaging configuration (PEP 518)
- `MANIFEST.in` - Specifies additional files to include in distribution
- Console script entry point: `meshtrbl`

## Installation Methods

### Method 1: Install from Source (Development)

```bash
# Clone or navigate to the repository
cd meshtrbl

# Install in editable mode (recommended for development)
pip install -e .

# Or install with all optional dependencies
pip install -e ".[all]"
```

### Method 2: Install from Source (Production)

```bash
# Install directly from source
pip install .

# Or with workflow support
pip install ".[workflow]"

# Or with development tools
pip install ".[dev]"
```

### Method 3: Build and Install Distribution

```bash
# Build the package
python -m build

# This creates:
# - dist/meshtrbl-3.0.0.tar.gz (source distribution)
# - dist/meshtrbl-3.0.0-py3-none-any.whl (wheel)

# Install from wheel
pip install dist/meshtrbl-3.0.0-py3-none-any.whl
```

### Method 4: Install from Git (Future)

```bash
# Once published to GitHub
pip install git+https://github.com/yourusername/meshtrbl.git

# Or specific branch/tag
pip install git+https://github.com/yourusername/meshtrbl.git@main
pip install git+https://github.com/yourusername/meshtrbl.git@v3.0.0
```

### Method 5: Install from PyPI (Future)

```bash
# Once published to PyPI
pip install meshtrbl

# With workflow support
pip install meshtrbl[workflow]

# With all extras
pip install meshtrbl[all]
```

## Package Extras

The package defines several optional dependency groups:

### `workflow` - Phase 3 LangGraph Workflows
```bash
pip install meshtrbl[workflow]
```
Includes: `langgraph>=0.1.0,<0.2.0`

### `dev` - Development Tools
```bash
pip install meshtrbl[dev]
```
Includes: pytest, pytest-asyncio, pytest-cov, black, flake8, mypy

### `all` - Everything
```bash
pip install meshtrbl[all]
```
Includes all optional dependencies

## Using the Console Script

After installation, the package provides the `meshtrbl` command:

```bash
# Run the agent (replaces: python -m src.agent)
meshtrbl

# With options
meshtrbl --verbose
meshtrbl --namespace production
meshtrbl --query "Check pod status"
meshtrbl --no-memory --no-cache
```

All command-line options are available:
- `--model` - OpenAI model (default: gpt-4o-mini)
- `--reasoning-model` - Stronger model for complex queries
- `--namespace` - Kubernetes namespace (default: default)
- `--consul-host` - Consul server host
- `--consul-port` - Consul server port
- `--verbose` - Enable verbose logging
- `--query` - Single query mode
- `--no-memory` - Disable conversation memory
- `--no-intent-routing` - Disable fast-path routing
- `--no-cache` - Disable session caching
- `--cache-ttl` - Cache TTL in seconds
- `--cache-size` - Maximum cache entries
- `--max-iterations` - Maximum tool calls
- `--max-time` - Maximum execution time

## Building the Package

### Prerequisites

```bash
# Install build tools
pip install build twine
```

### Build Process

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build source distribution and wheel
python -m build

# Verify the build
ls -lh dist/
```

### Check the Package

```bash
# Check package metadata
twine check dist/*

# Inspect the wheel contents
unzip -l dist/meshtrbl-3.0.0-py3-none-any.whl
```

## Publishing to PyPI

### Test PyPI (Recommended First)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ meshtrbl
```

### Production PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Verify
pip install meshtrbl
```

## Version Management

The package version is defined in:
- `setup.py` - Line 16: `version="3.0.0"`
- `pyproject.toml` - Line 6: `version = "3.0.0"`

Update both files when releasing new versions:
- **3.0.0** - Current (Phase 3 complete)
- **3.1.0** - Next minor release
- **4.0.0** - Next major release

Follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Package Metadata

Update these fields before publishing:

### In `setup.py`:
```python
author="Your Name"
author_email="your.email@example.com"
url="https://github.com/yourusername/meshtrbl"
```

### In `pyproject.toml`:
```toml
[project.authors]
name = "Your Name"
email = "your.email@example.com"

[project.urls]
Homepage = "https://github.com/yourusername/meshtrbl"
```

## Testing the Package

### Test Installation

```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate

# Install the package
pip install dist/meshtrbl-3.0.0-py3-none-any.whl

# Test the console script
meshtrbl --help

# Test import
python -c "from src.agent import TroubleshootingAgent; print('OK')"

# Deactivate and clean up
deactivate
rm -rf test_env
```

### Run Tests

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest test_workflows.py -v
```

## Quick Start After Installation

```bash
# Install the package
pip install meshtrbl[all]

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the agent
meshtrbl

# Or single query
meshtrbl --query "List all pods in default namespace"
```

## Distribution Checklist

Before publishing:

- [ ] Update version in `setup.py` and `pyproject.toml`
- [ ] Update `README.md` with latest features
- [ ] Update `CHANGELOG.md` (create if needed)
- [ ] Update author information
- [ ] Update repository URLs
- [ ] Run tests: `pytest`
- [ ] Build package: `python -m build`
- [ ] Check package: `twine check dist/*`
- [ ] Test installation in clean environment
- [ ] Test console script works: `meshtrbl --help`
- [ ] Upload to Test PyPI first
- [ ] Test installation from Test PyPI
- [ ] Upload to production PyPI
- [ ] Create GitHub release with tag
- [ ] Update documentation

## Continuous Integration

Consider setting up CI/CD with GitHub Actions:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Troubleshooting

### Issue: Module not found after installation

**Solution:** Ensure you're using the correct Python environment:
```bash
which python
which meshtrbl
```

### Issue: Console script not working

**Solution:** Reinstall the package:
```bash
pip uninstall meshtrbl
pip install -e .
```

### Issue: Missing dependencies

**Solution:** Install with extras:
```bash
pip install ".[all]"
```

### Issue: Import errors

**Solution:** Check package structure:
```bash
python -c "import src; print(src.__file__)"
```

## Package Name: meshtrbl

The package name "meshtrbl" is short for "Mesh Troubleshooter" and provides:
- ✅ Short, memorable command: `meshtrbl`
- ✅ Clear purpose: mesh (service mesh) + trbl (troubleshooter)
- ✅ Easy to type and remember
- ✅ Unique PyPI package name

## Additional Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)
- [Semantic Versioning](https://semver.org/)
- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/meshtrbl/issues
- Documentation: See README.md and feature documentation files