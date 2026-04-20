# Conversation Memory Feature

## Overview

The troubleshooting agent now includes **conversation memory** to maintain context across multiple questions in a session. This Phase 2 enhancement significantly improves the user experience by allowing the agent to remember previous discussions and build upon them.

## Key Benefits

1. **Context Retention**: The agent remembers what you've discussed, eliminating the need to repeat information
2. **Follow-up Questions**: Ask follow-up questions naturally without re-explaining the situation
3. **Improved Diagnosis**: The agent can correlate information from multiple queries for better troubleshooting
4. **Session Continuity**: Maintain a coherent troubleshooting session from start to finish

## How It Works

The agent uses LangChain's `ConversationBufferMemory` to store the conversation history:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="output"
)
```

Every interaction (user input and agent response) is automatically saved to memory and made available to the agent in subsequent queries.

## Usage

### Interactive Mode with Memory (Default)

Memory is **enabled by default** in interactive mode:

```bash
python -m src.agent
```

You'll see:
```
======================================================================
Kubernetes & Consul Troubleshooting Agent
======================================================================

I'm here to help you troubleshoot Kubernetes and Consul issues.
💾 Conversation memory is ENABLED - I'll remember our discussion!

Special commands:
  /clear    - Clear conversation memory
  /history  - Show conversation history
  /summary  - Show conversation summary

Type 'exit' or 'quit' to end the session.
```

### Example Conversation with Memory

```
You: Check the status of pod web-app-123

Agent: [Checks pod status]
The pod web-app-123 is in CrashLoopBackOff state...

You: What are the logs showing?

Agent: [Remembers we're discussing web-app-123]
Let me check the logs for web-app-123...
```

Notice how you didn't need to specify the pod name again!

### Memory Management Commands

#### `/clear` - Clear Memory
Clears all conversation history:
```
You: /clear
✓ Conversation memory cleared.
```

Use this when:
- Starting a new troubleshooting session
- Switching to a different issue
- The conversation context is no longer relevant

#### `/history` - View Full History
Shows all messages in the conversation:
```
You: /history

📜 Conversation History (4 messages):

1. You:
   Check the status of pod web-app-123

2. Agent:
   The pod web-app-123 is in CrashLoopBackOff state. Let me investigate...

3. You:
   What are the logs showing?

4. Agent:
   The logs for web-app-123 show an OOMKilled error...
```

#### `/summary` - View Summary
Shows a condensed view of the conversation:
```
You: /summary

📋 Conversation Summary:
1. User: Check the status of pod web-app-123
2. Agent: The pod web-app-123 is in CrashLoopBackOff state. Let me investigate...
3. User: What are the logs showing?
4. Agent: The logs for web-app-123 show an OOMKilled error...
```

### Disabling Memory

If you prefer to run without memory (each query is independent):

```bash
python -m src.agent --no-memory
```

This is useful for:
- Scripting and automation
- One-off queries
- Testing specific scenarios

### Single Query Mode

In single query mode, memory is available but less useful since there's only one interaction:

```bash
python -m src.agent --query "Why is my pod crashing?"
```

## Programming Interface

### Creating an Agent with Memory

```python
from src.agent import TroubleshootingAgent

# With memory (default)
agent = TroubleshootingAgent(
    model="gpt-4o-mini",
    enable_memory=True
)

# Without memory
agent = TroubleshootingAgent(
    model="gpt-4o-mini",
    enable_memory=False
)
```

### Memory Management Methods

#### `clear_memory()`
Clear all conversation history:
```python
agent.clear_memory()
```

#### `get_conversation_history()`
Get the raw message list:
```python
from langchain_core.messages import BaseMessage
from typing import List

history: List[BaseMessage] = agent.get_conversation_history()
for msg in history:
    print(f"{msg.type}: {msg.content}")
```

#### `get_conversation_summary()`
Get a human-readable summary:
```python
summary = agent.get_conversation_summary()
print(summary)
```

#### `save_context()`
Manually save context (useful for non-agent interactions):
```python
agent.save_context(
    {"input": "What is Kubernetes?"},
    {"output": "Kubernetes is a container orchestration platform."}
)
```

## Technical Details

### Memory Storage

- **Type**: `ConversationBufferMemory` (stores all messages in memory)
- **Persistence**: Session-only (cleared when agent terminates)
- **Format**: LangChain message objects (HumanMessage, AIMessage)

### Memory Integration

The memory is integrated with:
1. **Main Agent Executor**: Automatically saves all interactions
2. **Reasoning Model Executor**: Also uses memory for complex queries
3. **Tool Calls**: Tool outputs are part of the agent's reasoning but not directly stored as separate messages

### Performance Considerations

- **Memory Growth**: Conversation history grows with each interaction
- **Token Usage**: Longer conversations consume more tokens as history is included in prompts
- **Recommendation**: Use `/clear` periodically for long sessions to manage token costs

### Memory Scope

Memory is **session-scoped**:
- ✅ Persists across multiple queries in the same session
- ✅ Available to all execution paths (live troubleshooting, direct answer, etc.)
- ❌ Does NOT persist between different agent instances
- ❌ Does NOT persist after the program exits

## Best Practices

### When to Use Memory

✅ **Good use cases:**
- Interactive troubleshooting sessions
- Multi-step diagnostics
- Exploring related issues
- Learning about your infrastructure

❌ **Not ideal for:**
- Automated scripts
- One-off queries
- Unrelated sequential queries
- CI/CD pipelines

### Managing Long Conversations

For long troubleshooting sessions:

1. **Clear periodically**: Use `/clear` when switching topics
2. **Check history**: Use `/history` to see what the agent remembers
3. **Monitor tokens**: Longer history = higher token costs
4. **Restart if needed**: Exit and restart for a fresh session

### Memory and Query Routing

Memory works with all query routing paths:
- **Live Troubleshooting**: Full memory integration
- **Direct Answer**: Memory available but less utilized
- **Repo Code Assistance**: Memory available for context

## Examples

### Example 1: Multi-Step Diagnosis

```
You: List all pods in the production namespace

Agent: [Lists pods, finds several in error state]

You: Focus on the api-backend pod

Agent: [Remembers we're in production namespace]
Checking api-backend in production...

You: Show me the logs

Agent: [Remembers we're looking at api-backend in production]
Retrieving logs for api-backend...
```

### Example 2: Consul Service Mesh

```
You: Check the health of the payment-service

Agent: [Checks service health]
The payment-service has 2 unhealthy instances...

You: Are there any intentions blocking it?

Agent: [Remembers we're investigating payment-service]
Let me check intentions for payment-service...
```

### Example 3: Using Memory Commands

```
You: Check pod web-app-123
Agent: [Provides status]

You: /summary
📋 Conversation Summary:
1. User: Check pod web-app-123
2. Agent: The pod is running but has 3 restarts...

You: /clear
✓ Conversation memory cleared.

You: Check pod database-456
Agent: [Treats this as a fresh query]
```

## Troubleshooting

### Memory Not Working?

Check if memory is enabled:
```python
if agent.enable_memory:
    print("Memory is enabled")
else:
    print("Memory is disabled")
```

### Memory Growing Too Large?

Clear it periodically:
```
You: /clear
```

Or restart the agent for a fresh session.

### Want to See What's Stored?

Use the history command:
```
You: /history
```

## Future Enhancements

Planned improvements for Phase 3:
- **Persistent Memory**: Save conversations to disk
- **Memory Summarization**: Automatically condense long conversations
- **Selective Memory**: Remember only important context
- **Memory Search**: Search through past conversations
- **Memory Export**: Export conversation history for analysis

## Related Documentation

- [README.md](README.md) - Main project documentation
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview and roadmap
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide

---

**Phase 2 Feature** - Conversation Memory ✅ Complete