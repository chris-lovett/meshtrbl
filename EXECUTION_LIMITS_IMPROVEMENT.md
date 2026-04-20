# Execution Limits Improvement

## Problem
During complex troubleshooting scenarios (e.g., investigating a pod stuck in Pending state), the agent was stopping prematurely with:
```
Status: Partial diagnosis (execution limit reached)
Try narrowing the question to one workload, service, or namespace for a deeper follow-up.
```

This prevented the agent from completing thorough investigations and providing complete diagnoses.

## Root Cause
The agent had hardcoded execution limits that were too restrictive for complex troubleshooting:
- **max_iterations**: 20 tool calls
- **max_execution_time**: 120 seconds (2 minutes)

Complex troubleshooting often requires:
- Multiple tool calls to gather information (list pods, describe pod, get logs, check events)
- Cross-referencing between Kubernetes and Consul
- Pattern matching against error databases
- Synthesizing information from multiple sources

## Solution

### 1. Made Limits Configurable
Added two new parameters to `TroubleshootingAgent.__init__()`:
- `max_iterations`: Maximum number of tool calls per query
- `max_execution_time`: Maximum execution time in seconds

### 2. Increased Default Values
New defaults provide more room for complex investigations:
- **max_iterations**: 35 (was 20) - 75% increase
- **max_execution_time**: 300 seconds / 5 minutes (was 120 seconds / 2 minutes) - 150% increase

### 3. Added CLI Arguments
Users can now customize limits via command-line:
```bash
python src/agent.py --max-iterations 50 --max-time 600
```

## Usage

### Default Behavior (Recommended)
Simply use the agent normally - the new defaults handle most complex scenarios:
```bash
python src/agent.py
```

### Custom Limits for Very Complex Scenarios
For extremely complex multi-service investigations:
```bash
# Allow up to 50 tool calls and 10 minutes
python src/agent.py --max-iterations 50 --max-time 600
```

### Programmatic Usage
```python
from src.agent import TroubleshootingAgent

# Use defaults (35 iterations, 5 minutes)
agent = TroubleshootingAgent()

# Or customize for specific needs
agent = TroubleshootingAgent(
    max_iterations=50,      # Allow more tool calls
    max_execution_time=600  # Allow 10 minutes
)
```

## Benefits

### 1. Complete Diagnoses
The agent can now:
- Fully investigate complex issues without hitting limits
- Follow multiple diagnostic paths
- Cross-reference information across systems
- Provide comprehensive root cause analysis

### 2. Better User Experience
- Fewer "partial diagnosis" messages
- More thorough troubleshooting
- Less need to "narrow the question"
- Complete solutions in one interaction

### 3. Flexibility
- Users can adjust limits based on their needs
- Different scenarios can use different limits
- No need to modify code for different use cases

## Example Scenarios

### Scenario 1: Pod Stuck in Pending
**Before** (20 iterations, 2 minutes):
```
Agent: Checking pod status...
Agent: Listing events...
Agent: Checking node resources...
Status: Partial diagnosis (execution limit reached)
Try narrowing the question to one workload, service, or namespace.
```

**After** (35 iterations, 5 minutes):
```
Agent: Checking pod status...
Agent: Listing events...
Agent: Checking node resources...
Agent: Analyzing resource requests...
Agent: Checking PVC status...
Agent: Reviewing scheduler logs...
Agent: Matching error patterns...

Diagnosis: Pod is pending due to insufficient CPU resources.
The pod requests 2 CPU cores but no nodes have that capacity available.

Solution:
1. Reduce pod CPU request to 1 core, or
2. Add nodes with more CPU capacity, or
3. Scale down other workloads to free resources
```

### Scenario 2: Service Communication Issues
**Before**: Might timeout while checking intentions, service health, and network policies

**After**: Can thoroughly investigate:
- Service registration in Consul
- Health check status
- Intention rules
- Network policies
- Pod-to-pod connectivity
- DNS resolution
- Certificate issues

## Performance Considerations

### Resource Usage
- **Memory**: Minimal increase (stores more conversation history)
- **API Calls**: More OpenAI API calls for longer investigations
- **Cost**: Proportional to investigation depth

### Optimization Tips
1. **Use caching**: Keep `enable_cache=True` (default) to avoid redundant tool calls
2. **Use intent routing**: Keep `enable_intent_routing=True` (default) for faster simple queries
3. **Be specific**: More specific questions still complete faster
4. **Monitor costs**: Longer investigations = more API calls

### When to Adjust Limits

**Increase limits when**:
- Investigating multi-service issues
- Debugging complex networking problems
- Analyzing cascading failures
- Need comprehensive root cause analysis

**Decrease limits when**:
- Running automated checks
- Cost optimization is critical
- Simple status queries
- Quick health checks

## Technical Details

### Implementation
The limits are applied to both agent executors:
1. **Main executor** (`self.agent_executor`): Used for most queries
2. **Reasoning executor**: Used for complex troubleshooting with reasoning model

Both use the same configurable limits for consistency.

### Limit Behavior
When a limit is reached:
- **Iteration limit**: Agent stops after N tool calls
- **Time limit**: Agent stops after N seconds
- **Partial diagnosis**: Agent returns findings gathered so far

The agent gracefully handles limit scenarios and provides useful partial information.

## Files Modified
- `src/agent.py`:
  - Added `max_iterations` and `max_execution_time` parameters to `__init__()`
  - Updated both `AgentExecutor` instances to use configurable limits
  - Added CLI arguments `--max-iterations` and `--max-time`
  - Changed defaults from 20/120 to 35/300

## Backward Compatibility
✅ Fully backward compatible
- Existing code continues to work with new defaults
- No breaking changes to API
- Optional parameters with sensible defaults

## Testing Recommendations

### Test Complex Scenarios
```bash
# Test with a complex multi-step issue
python src/agent.py --query "Why is my pod stuck in pending and how do I fix it?"

# Test with verbose mode to see all tool calls
python src/agent.py --verbose --query "Investigate service communication between web and api"
```

### Monitor Execution
Watch for:
- Number of tool calls used
- Time taken for diagnosis
- Quality of final diagnosis
- Whether limits are still being hit

### Adjust as Needed
If you still see "execution limit reached":
- Increase `--max-iterations` further
- Increase `--max-time` further
- Or break the question into smaller parts

## Related Features
- **Session Cache**: Reduces redundant tool calls (helps stay under iteration limit)
- **Intent Routing**: Fast-paths simple queries (uses fewer iterations)
- **Error Pattern Recognition**: Instant diagnosis for known issues (minimal iterations)
- **Memory**: Maintains context across conversation (more efficient follow-ups)

## Summary
The execution limit improvements allow the agent to complete thorough investigations of complex issues without premature termination. The new defaults (35 iterations, 5 minutes) handle most scenarios, while CLI arguments provide flexibility for exceptional cases.