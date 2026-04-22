# Installation Guide for meshtrbl

Quick installation guide for the **meshtrbl** (Mesh Troubleshooter) package.

## Quick Install

```bash
# Install from source
pip install .

# Or with all features including LangGraph workflows
pip install ".[all]"
```

## After Installation

The package provides the `meshtrbl` command:

```bash
# Run the agent
meshtrbl

# Show help
meshtrbl --help

# Run with options
meshtrbl --verbose --namespace production
```

## Installation Options

### Basic Installation
```bash
pip install .
```
Includes: Core dependencies (LangChain, OpenAI, Kubernetes, Consul clients)

### With Workflow Support (Phase 3)
```bash
pip install ".[workflow]"
```
Includes: Core + LangGraph for advanced workflows

### With Development Tools
```bash
pip install ".[dev]"
```
Includes: Core + pytest, black, flake8, mypy

### Complete Installation
```bash
pip install ".[all]"
```
Includes: Everything (core + workflow + dev tools)

## Development Installation

For development, use editable mode:

```bash
# Install in editable mode
pip install -e ".[all]"

# Now changes to source code take effect immediately
```

## Environment Setup

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Edit `.env` and add your OpenAI API key:**
```bash
OPENAI_API_KEY=sk-your-key-here
```

3. **Optional Consul configuration:**
```bash
CONSUL_HTTP_ADDR=127.0.0.1:8501
CONSUL_HTTP_SSL=true
CONSUL_HTTP_TOKEN=your-consul-token
```

## Verify Installation

```bash
# Check the command is available
which meshtrbl

# Show version and help
meshtrbl --help

# Test import
python -c "from src.agent import TroubleshootingAgent; print('✓ Installation successful')"
```

## Usage Examples

### Interactive Mode
```bash
meshtrbl
```

### Single Query
```bash
meshtrbl --query "List all pods in default namespace"
```

### With Options
```bash
meshtrbl --verbose --namespace production --no-cache
```

## Upgrading

```bash
# Reinstall from source
pip install --upgrade .

# Or force reinstall
pip install --force-reinstall .
```

## Uninstalling

```bash
pip uninstall meshtrbl
```

## Troubleshooting

### Command not found: meshtrbl

**Solution:** Ensure the package is installed and you're in the correct environment:
```bash
pip list | grep meshtrbl
which python
```

### Import errors

**Solution:** Reinstall with all dependencies:
```bash
pip install -e ".[all]"
```

### Missing LangGraph

**Solution:** Install workflow support:
```bash
pip install ".[workflow]"
```

## Next Steps

After installation:
1. ✅ Set up your `.env` file with API keys
2. ✅ Run `meshtrbl` to start the agent
3. ✅ Read [QUICKSTART.md](QUICKSTART.md) for usage examples
4. ✅ Read [PHASE3_LANGGRAPH_WORKFLOWS.md](PHASE3_LANGGRAPH_WORKFLOWS.md) for advanced features

## Building from Source

See [PACKAGING.md](PACKAGING.md) for detailed packaging and distribution instructions.