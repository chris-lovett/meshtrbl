# Kubernetes & Consul Service Mesh Troubleshooting Agent

An AI-powered agent built with LangChain and OpenAI GPT-4 to help troubleshoot Kubernetes clusters and HashiCorp Consul service mesh issues.

## 🎯 Features

### Phase 1: Basic Agent (Current)
- ✅ Kubernetes pod inspection and diagnostics
- ✅ Pod logs retrieval and analysis
- ✅ Consul service discovery and health checks
- ✅ Service mesh intentions verification
- ✅ Interactive chat interface
- ✅ ReAct reasoning pattern for systematic troubleshooting

### Phase 2: Enhanced Intelligence (Coming Soon)
- 🔄 Conversation memory and context awareness
- 🔄 Common error pattern recognition
- 🔄 Consul Connect sidecar proxy diagnostics
- 🔄 Advanced service-to-service communication analysis

### Phase 3: Advanced Workflows (Future)
- 📋 LangGraph state machines for complex diagnostics
- 📋 Parallel tool execution for faster troubleshooting
- 📋 Conditional routing based on issue type
- 📋 Automated remediation suggestions

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Access to a Kubernetes cluster (with kubectl configured)
- Access to a Consul cluster (optional for Consul features)
- OpenAI API key

### Installation

1. **Clone or navigate to the project directory:**
```bash
cd k8s-consul-troubleshooting-agent
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key and other settings
```

Required environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key_here
CONSUL_HTTP_ADDR=http://localhost:8500  # Optional
K8S_NAMESPACE=default  # Optional
```

### Running the Agent

#### Interactive Mode (Recommended for learning)
```bash
python -m src.agent
```

This starts an interactive chat session where you can ask troubleshooting questions.

#### Single Query Mode
```bash
python -m src.agent --query "Why is my pod in CrashLoopBackOff?"
```

#### With Custom Options
```bash
python -m src.agent \
  --namespace production \
  --consul-host consul.example.com \
  --consul-port 8500 \
  --verbose
```

## 📖 Usage Examples

### Example 1: Troubleshooting a Crashing Pod

```
You: My pod "web-app-7d8f9c" keeps crashing. Can you help?

Agent: I'll help you diagnose the issue. Let me start by checking the pod status.

[Agent uses get_pod_status tool]
[Agent uses get_pod_logs tool]
[Agent analyzes the information]

Based on the logs, your pod is experiencing an OOMKilled error. The container 
is being terminated because it's exceeding its memory limit of 128Mi. 

Recommendations:
1. Increase the memory limit in your deployment
2. Investigate memory leaks in your application
3. Consider implementing memory profiling

Would you like me to show you how to update the memory limits?
```

### Example 2: Consul Service Communication Issues

```
You: Service "api" cannot connect to "database" service. What's wrong?

Agent: Let me check the Consul service mesh configuration.

[Agent uses get_service_health tool]
[Agent uses check_consul_intention tool]
[Agent analyzes the results]

I found the issue! There's a DENY intention blocking traffic from "api" to 
"database". The intention was created 2 days ago.

To fix this:
1. Update the intention to ALLOW
2. Or verify if this restriction is intentional for security

Would you like me to show you the current intentions configuration?
```

### Example 3: Listing and Inspecting Services

```
You: Show me all services in the production namespace

Agent: [Uses list_pods tool with namespace=production]

Here are all pods in the production namespace:
- web-frontend: Running (3/3 ready)
- api-backend: Running (2/2 ready)
- database: CrashLoopBackOff (0/1 ready, 5 restarts)

I notice the database pod is in CrashLoopBackOff. Would you like me to 
investigate this issue?
```

## 🛠️ Available Tools

The agent has access to the following tools:

### Kubernetes Tools
- `get_pod_status` - Check pod status and conditions
- `get_pod_logs` - Retrieve container logs
- `list_pods` - List all pods in a namespace
- `describe_pod` - Get detailed pod information (like kubectl describe)

### Consul Tools
- `list_consul_services` - List all registered services
- `get_service_health` - Check service health status
- `get_service_instances` - List service instances
- `list_consul_intentions` - Show service-to-service access rules
- `check_consul_intention` - Verify if traffic is allowed between services
- `get_consul_members` - Check Consul cluster members

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              LangChain ReAct Agent                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  System Prompt: K8s & Consul Expert                  │   │
│  │  - Troubleshooting methodology                       │   │
│  │  - Best practices knowledge                          │   │
│  │  - Step-by-step reasoning                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  OpenAI GPT-4                                │
│              (Reasoning & Analysis)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tool Selection                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│ Kubernetes Tools │      │  Consul Tools    │
│                  │      │                  │
│ - Pod Status     │      │ - Services       │
│ - Logs           │      │ - Health Checks  │
│ - Describe       │      │ - Intentions     │
│ - List           │      │ - Members        │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  K8s Cluster     │      │  Consul Cluster  │
└──────────────────┘      └──────────────────┘
```

## 📚 Learning Resources

### Understanding LangChain
- The agent uses LangChain's ReAct (Reasoning + Acting) pattern
- Tools are wrapped as LangChain Tool objects
- The agent iteratively reasons and acts until it finds a solution

### Understanding the Code

**Key Files:**
- `src/agent.py` - Main agent implementation
- `src/tools/kubernetes.py` - Kubernetes inspection tools
- `src/tools/consul_tools.py` - Consul service mesh tools
- `src/prompts/system_prompts.py` - Expert system prompts

**How it Works:**
1. User asks a question
2. Agent analyzes the question using GPT-4
3. Agent decides which tools to use
4. Tools gather information from K8s/Consul
5. Agent synthesizes findings into actionable advice

## 🔧 Configuration

### Agent Configuration (`config/agent_config.yaml`)
```yaml
llm:
  model: "gpt-4-turbo-preview"
  temperature: 0.1  # Low temperature for consistent, factual responses

behavior:
  max_iterations: 10  # Maximum reasoning steps
  verbose: false  # Set to true for debugging
```

### Environment Variables (`.env`)
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional - Kubernetes
KUBECONFIG_PATH=  # Leave empty for default ~/.kube/config
K8S_NAMESPACE=default

# Optional - Consul
CONSUL_HTTP_ADDR=http://localhost:8500
CONSUL_HTTP_TOKEN=  # If ACLs are enabled
CONSUL_DATACENTER=dc1

# Optional - Agent
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1
VERBOSE=false
```

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (Current)
- Basic LangChain agent
- Kubernetes and Consul tools
- Interactive chat interface
- ReAct reasoning pattern

### 🔄 Phase 2: Enhanced Intelligence (Next)
- Conversation memory
- Error pattern recognition
- Consul Connect proxy diagnostics
- Historical context awareness

### 📋 Phase 3: Advanced Workflows (Future)
- LangGraph state machines
- Complex multi-step diagnostics
- Parallel tool execution
- Automated remediation

## 🤝 Contributing

This is a learning project for understanding LangChain and LangGraph. Feel free to:
- Add new tools for additional diagnostics
- Improve prompts for better reasoning
- Add support for other service meshes (Istio, Linkerd)
- Enhance error pattern recognition

## 📝 License

MIT License - Feel free to use and modify for your needs.

## 🙏 Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Powered by [OpenAI GPT-4](https://openai.com/)
- Kubernetes client: [kubernetes-client/python](https://github.com/kubernetes-client/python)
- Consul client: [python-consul](https://github.com/cablehead/python-consul)

---

**Happy Troubleshooting! 🚀**