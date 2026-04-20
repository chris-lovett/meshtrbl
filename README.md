# Kubernetes & Consul Service Mesh Troubleshooting Agent

An AI-powered agent built with LangChain and OpenAI GPT-4 to help troubleshoot Kubernetes clusters and HashiCorp Consul service mesh issues.

## 🎯 Features

### Phase 1: Basic Agent ✅ Complete
- ✅ Kubernetes pod inspection and diagnostics
- ✅ Pod logs retrieval and analysis
- ✅ Consul service discovery and health checks
- ✅ Service mesh intentions verification
- ✅ Interactive chat interface
- ✅ ReAct reasoning pattern for systematic troubleshooting

### Phase 2: Enhanced Intelligence (In Progress)
- ✅ **Conversation memory and session context reuse** 🎉 NEW!
- 🔄 Common error pattern recognition for faster diagnosis
- 🔄 Intent classification and direct routing for common troubleshooting flows
- 🔄 Cached tool results within a troubleshooting session
- 🔄 Consul Connect sidecar proxy diagnostics
- 🔄 Advanced service-to-service communication analysis

### Phase 2 Priorities

Phase 2 is being prioritized around two goals:

1. **Responsiveness**
   - Reduce unnecessary LLM/tool loops
   - Reuse context already gathered in the current session
   - Route common troubleshooting questions into targeted workflows

2. **Capability**
   - Improve follow-up question handling
   - Recognize recurring Kubernetes and Consul failure patterns
   - Expand diagnostics for Consul Connect and service-to-service issues

Planned implementation order for highest user value:
1. Conversation memory and session context reuse
2. Intent classification and direct routing for common issues
3. Session-scoped caching of tool results
4. Common error pattern recognition
5. Consul Connect sidecar proxy diagnostics
6. Advanced service-to-service communication analysis

This keeps the original Phase 2 direction intact while reordering work to improve speed and usability first.

### Phase 3: Advanced Workflows (Future)
- 📋 LangGraph state machines for complex diagnostics
- 📋 Parallel tool execution for faster troubleshooting
- 📋 Conditional routing based on issue type
- 📋 Automated remediation suggestions

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher recommended
- Access to a Kubernetes cluster (with kubectl configured)
- Access to a Consul cluster (optional for Consul features)
- OpenAI API key

> macOS note: avoid the Apple Command Line Tools Python for this project. It may be linked against LibreSSL, which triggers `urllib3` warnings. Use a Homebrew Python 3.11+ interpreter instead.

### Installation

1. **Clone or navigate to the project directory:**
```bash
cd k8s-consul-troubleshooting-agent
```

2. **Install a supported Python on macOS (recommended):**
```bash
brew install python@3.11
/opt/homebrew/bin/python3.11 -c "import ssl,sys; print(sys.version); print(ssl.OPENSSL_VERSION)"
```

3. **Create and activate virtual environment:**
```bash
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. **Install dependencies:**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key and other settings
# Default model: gpt-4o-mini
```

Required environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key_here
CONSUL_HTTP_ADDR=127.0.0.1:8500  # Optional, use host:port format for python-consul
K8S_NAMESPACE=default  # Optional
```

Optional Consul environment variables:
```bash
CONSUL_HTTP_TOKEN=                             # Recommended for ACL-enabled Consul clusters
CONSUL_HTTP_SSL=false                          # Set to true for HTTPS
CONSUL_HTTP_SSL_VERIFY=true                    # Keep enabled when using a trusted CA bundle
CONSUL_CACERT=/path/to/consul-ca.pem           # Preferred for HTTPS with a private CA
```

### Consul HTTPS Setup

For production-like use, prefer a verified HTTPS configuration over `CONSUL_HTTP_SSL_VERIFY=false`.

Recommended workflow for Kubernetes / OpenShift deployments:
1. Extract the active Consul CA certificate from the running cluster:
```bash
kubectl get secret -n consul consul-ca-cert -o jsonpath='{.data.tls\.crt}' | base64 --decode > consul-ca-from-cluster.pem
```

2. Verify the HTTPS listener using that CA bundle:
```bash
openssl s_client \
  -connect 127.0.0.1:8501 \
  -CAfile ./consul-ca-from-cluster.pem \
  </dev/null
```

3. Confirm OpenSSL reports:
```text
Verify return code: 0 (ok)
```

4. Configure the agent to use the verified CA:
```bash
export CONSUL_HTTP_ADDR=127.0.0.1:8501
export CONSUL_HTTP_SSL=true
unset CONSUL_HTTP_SSL_VERIFY
export CONSUL_CACERT=$(pwd)/consul-ca-from-cluster.pem
export CONSUL_HTTP_TOKEN=<consul-token-secret-id>
```

Lessons learned:
- Use the CA extracted from the running cluster, not an older local copy.
- `CONSUL_HTTP_ADDR` must be `host:port` without `http://` or `https://`.
- The built-in Consul CA can be correct, but the local PEM must match the active cluster CA exactly.
- OpenShift/AWS only matter if TLS is terminated before Consul. If the presented certificate is `server.dc1.consul`, you are talking directly to Consul's HTTPS listener.
- Avoid `CONSUL_HTTP_SSL_VERIFY=false` except for short-lived local debugging.

Do not commit extracted CA files into git. Keep them local and ignored.

### Running the Agent

#### Interactive Mode with Conversation Memory (Recommended)
```bash
python -m src.agent
```

This starts an interactive chat session with **conversation memory enabled** by default. The agent will remember your discussion and provide better context-aware responses!

**New in Phase 2:** Memory commands available in interactive mode:
- `/clear` - Clear conversation memory
- `/history` - Show full conversation history
- `/summary` - Show conversation summary

📖 **[Read the full Memory Feature documentation](MEMORY_FEATURE.md)** for detailed usage examples and best practices.

#### Interactive Mode without Memory
```bash
python -m src.agent --no-memory
```

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

### Consul ACL Setup for Troubleshooting

If your Consul cluster has ACLs enabled, create a dedicated token for the agent.

1. Create a policy file in the repository:
```bash
cat > examples/consul-agent-troubleshooter-policy.hcl <<'EOF'
agent_prefix "" {
  policy = "read"
}

node_prefix "" {
  policy = "read"
}

service_prefix "" {
  policy = "read"
}

session_prefix "" {
  policy = "read"
}

query_prefix "" {
  policy = "read"
}

key_prefix "" {
  policy = "read"
}

event_prefix "" {
  policy = "read"
}

operator = "read"
mesh = "read"
peering = "read"
acl = "read"

intention_prefix "" {
  policy = "read"
}
EOF
```

2. Create the policy and token:
```bash
consul acl policy create \
  -name agent-troubleshooter-admin \
  -description "Admin-level read policy for troubleshooting agent" \
  -rules @examples/consul-agent-troubleshooter-policy.hcl

consul acl token create \
  -description "Token for k8s-consul troubleshooting agent" \
  -policy-name agent-troubleshooter-admin
```

3. Configure the token for the agent:
```bash
export CONSUL_HTTP_ADDR=127.0.0.1:8501
export CONSUL_HTTP_SSL=true
export CONSUL_HTTP_SSL_VERIFY=false   # or set CONSUL_CACERT instead
export CONSUL_HTTP_TOKEN=<secret-id>
python -m src.agent
```

Notes:
- Use `CONSUL_HTTP_ADDR=host:port` without `http://` or `https://`.
- Prefer `CONSUL_CACERT` over disabling TLS verification.
- If you need true write/admin behavior, create a separate higher-privilege policy rather than broadening the default troubleshooting token.

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