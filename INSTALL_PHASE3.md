# Installing Phase 3 Dependencies

## Quick Installation

To use the new Phase 3 LangGraph workflow features, you need to install the updated dependencies:

```bash
# Navigate to project directory
cd meshtrbl

# Activate your virtual environment (if using one)
source venv/bin/activate

# Install/upgrade all dependencies including LangGraph
pip install -r requirements.txt

# Or install just LangGraph
pip install 'langgraph>=0.1.0,<0.2.0'
```

## Verification

Verify the installation:

```bash
python3 -c "import langgraph; print('LangGraph version:', langgraph.__version__)"
```

## Running the Agent

After installation, run the agent normally:

```bash
# Interactive mode with workflow support
python3 -m src.agent

# Or with explicit workflow mode
python3 -m src.agent --verbose
```

## Fallback Behavior

**Good news:** The agent will still work even without LangGraph installed! It will:
- Automatically detect if LangGraph is not available
- Show a warning message (in verbose mode)
- Fall back to the standard ReAct agent mode
- All Phase 1 and Phase 2 features continue to work

## Python Version Note

You're currently using Python 3.9, which is past its end-of-life. Consider upgrading to Python 3.11+ for better performance and security:

```bash
# Install Python 3.11 via Homebrew (recommended)
brew install python@3.11

# Create new virtual environment with Python 3.11
/opt/homebrew/bin/python3.11 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'langgraph'

**Solution:** Install LangGraph:
```bash
pip install langgraph
```

### Issue: urllib3 OpenSSL warning

**Solution:** This is a warning, not an error. The agent will still work. To fix:
```bash
# Use Homebrew Python instead of system Python
brew install python@3.11
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Google auth warnings

**Solution:** These are warnings about Python 3.9 being EOL. Upgrade to Python 3.11+.

## Testing Phase 3

After installation, test the workflow mode:

```bash
python3 -m src.agent
```

Then try a complex query:
```
You: Investigate intermittent connectivity issues between service A and service B 
     in the service mesh with timeout errors
```

You should see:
```
[Phase 3] Running LangGraph workflow mode...
```

## Disabling Workflow Mode

If you want to disable workflow mode and use only the standard agent:

```python
from src.agent import TroubleshootingAgent

agent = TroubleshootingAgent(
    enable_workflow=False  # Disable Phase 3 workflows
)
```

Or set in your code/config to always use standard mode.