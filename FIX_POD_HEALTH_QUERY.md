# Fix: "Are All Pods Healthy" Query Issue

## Problem
When asking the agent "are all my pods healthy?", it was failing with:
```
Error running agent: KubernetesTools.get_pod_status() missing 1 required positional argument: 'pod_name'
```

## Root Cause
The agent was trying to call `get_pod_status()` without a pod name because:

1. **Ambiguous Tool Descriptions**: The tool descriptions didn't clearly distinguish between:
   - Tools that require specific resource names (like `get_pod_status` which needs a pod name)
   - Tools that can list all resources (like `list_pods` which can work without parameters)

2. **Misleading Parameter Requirements**: The `list_pods` tool description said:
   ```
   Input should be: namespace or namespace,label_selector
   ```
   This made the LLM think it MUST provide a namespace, when actually the namespace parameter is optional and defaults to the configured namespace.

## Solution

### 1. Updated Tool Descriptions
Made tool descriptions more explicit about parameter requirements:

**For tools requiring specific resources** (marked with "REQUIRED"):
- `get_pod_status`: "Input REQUIRED: pod_name or pod_name,namespace"
- `get_pod_logs`: "Input REQUIRED: pod_name or pod_name,namespace or pod_name,namespace,container"
- `describe_pod`: "Input REQUIRED: pod_name or pod_name,namespace"

**For tools that list all resources** (marked with "empty" option):
- `list_pods`: "Input can be: empty (uses default namespace), namespace, or namespace,label_selector"
  - Added explicit note: "Use this to see all pods and their status, or to check if all pods are healthy."
  - Added cross-reference: "NOTE: To check ALL pods, use list_pods instead."

**For tools with no parameters**:
- `list_consul_services`: "Input: empty string "" (datacenter parameter not currently used)"
- `list_consul_intentions`: "Input: empty string """
- `get_consul_members`: "Input: empty string """

### 2. How It Works Now

The `_parse_and_call` method in `agent.py` already handles empty input correctly:

```python
def _parse_and_call(self, func, input_str: str):
    """Parse comma-separated input and call function with appropriate arguments."""
    if not input_str or input_str.strip() == "":
        return func()  # Call with no arguments - uses defaults
    
    parts = [p.strip() for p in input_str.split(',')]
    return func(*parts)
```

When the agent receives "are all my pods healthy?", it should now:
1. Recognize this is asking about ALL pods (not a specific pod)
2. Choose the `list_pods` tool
3. Call it with empty input: `list_pods("")`
4. The tool calls `k8s_tools.list_pods()` with no arguments
5. The method uses the default namespace configured in the agent

### 3. Expected Behavior

**Query**: "are all my pods healthy?"

**Agent should**:
- Use `list_pods` tool with empty input
- Get a list of all pods in the default namespace
- Show their status (Running, Pending, etc.)
- Show ready containers (e.g., "2/2")
- Show restart counts
- Provide a summary of pod health

**Query**: "is pod my-app-123 healthy?"

**Agent should**:
- Use `get_pod_status` tool with input "my-app-123"
- Get detailed status of that specific pod
- Show container states, conditions, etc.

## Testing

### Manual Testing
1. Start the agent: `python -m src.agent`
2. Ask: "are all my pods healthy?"
3. Expected: Agent uses `list_pods` tool and shows all pods
4. Ask: "is pod <specific-pod-name> healthy?"
5. Expected: Agent uses `get_pod_status` tool for that specific pod

### Automated Testing
Run the test script:
```bash
cd ../hashi/meshtrbl
python test_pod_health_query.py
```

This tests:
- `list_pods()` with no parameters
- `list_pods(namespace="default")` with namespace
- Simulation of `_parse_and_call` behavior with empty input

## Files Modified
- `src/agent.py`: Updated tool descriptions in `_create_tools()` method (lines 140-260)

## Benefits
1. **Clearer Intent**: LLM can now distinguish between "check all" vs "check specific" queries
2. **Better UX**: Users can ask natural questions like "are all pods healthy?"
3. **Reduced Errors**: Fewer parameter mismatch errors
4. **Consistent Patterns**: All tools now follow clear parameter conventions

## Related Tools
The same pattern applies to other tools:
- **List all**: `list_pods`, `list_consul_services`, `list_consul_intentions`, `get_consul_members`
- **Check specific**: `get_pod_status`, `get_pod_logs`, `describe_pod`, `get_service_health`, etc.