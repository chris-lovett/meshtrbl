# Quick Start Guide

Get up and running with the Kubernetes & Consul Troubleshooting Agent in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.11+ installed (`python3 --version`)
- ✅ Access to a Kubernetes cluster (`kubectl cluster-info`)
- ✅ OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- ⚠️ Optional: Access to Consul cluster (for Consul features)

> macOS note: prefer Homebrew Python over the Apple Command Line Tools Python. The system Python may use LibreSSL and trigger `urllib3` startup warnings.

## Step 1: Setup (2 minutes)

```bash
# Navigate to the project directory
cd meshtrbl

# Install a supported Python on macOS
brew install python@3.11

# Create virtual environment
/opt/homebrew/bin/python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Step 2: Configure (1 minute)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# You can use any text editor
# Default model: gpt-4o-mini
nano .env  # or vim, code, etc.
```

Minimum required configuration in `.env`:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

If you want to use Consul features in an ACL-enabled cluster, also configure:
```bash
CONSUL_HTTP_ADDR=127.0.0.1:8501
CONSUL_HTTP_SSL=true
CONSUL_HTTP_TOKEN=<consul-token-secret-id>
```

For verified HTTPS on Kubernetes / OpenShift, extract the active CA from the running cluster:
```bash
kubectl get secret -n consul consul-ca-cert -o jsonpath='{.data.tls\.crt}' | base64 --decode > consul-ca-from-cluster.pem
```

Validate the HTTPS listener:
```bash
openssl s_client \
  -connect 127.0.0.1:8501 \
  -CAfile ./consul-ca-from-cluster.pem \
  </dev/null
```

If OpenSSL reports `Verify return code: 0 (ok)`, configure:
```bash
CONSUL_CACERT=/full/path/to/consul-ca-from-cluster.pem
```

Use `CONSUL_HTTP_SSL_VERIFY=false` only for short-lived local debugging.

## Step 3: Run (30 seconds)

```bash
# Start the interactive agent
python -m src.agent
```

You should see:
```
======================================================================
Kubernetes & Consul Troubleshooting Agent
======================================================================

I'm here to help you troubleshoot Kubernetes and Consul issues.
Type 'exit' or 'quit' to end the session.

You: 
```

## Step 4: Try It Out! (1 minute)

### Example 1: List Pods
```
You: List all pods in the default namespace

Agent: [Uses list_pods tool]
=== Pods in namespace 'default' ===
...
```

### Example 2: Check Pod Status
```
You: Check the status of pod my-app-xyz123

Agent: [Uses get_pod_status tool]
=== Pod Status: my-app-xyz123 ===
...
```

### Example 3: Troubleshoot an Issue
```
You: My pod keeps crashing. Can you help?

Agent: I'll help you diagnose the issue. What's the name of the pod?

You: web-app-7d8f9c

Agent: [Systematically checks status, logs, and events]
Based on the logs, your pod is experiencing...
```

## Common Commands

### Interactive Mode (Recommended)
```bash
python -m src.agent
```

### Single Query Mode
```bash
python -m src.agent --query "Why is my pod in CrashLoopBackOff?"
```

### With Custom Namespace
```bash
python -m src.agent --namespace production
```

### With Verbose Logging (for debugging)
```bash
python -m src.agent --verbose
```

### With Custom Consul Server
```bash
python -m src.agent --consul-host consul.example.com --consul-port 8500
```

## Troubleshooting Setup Issues

### Issue: "No module named 'langchain'"
**Solution:** Make sure you activated the virtual environment and installed dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "OpenAI API key must be provided"
**Solution:** Check your `.env` file has the correct API key:
```bash
cat .env | grep OPENAI_API_KEY
```

### Issue: "Failed to initialize Kubernetes client"
**Solution:** Verify kubectl is configured:
```bash
kubectl cluster-info
```

### Issue: "Failed to initialize Consul client"
**Solution:** Verify the Consul connection settings in `.env`:
```bash
CONSUL_HTTP_ADDR=127.0.0.1:8501
CONSUL_HTTP_SSL=true
CONSUL_HTTP_TOKEN=<token>
```

Important:
- Use `host:port` format for `CONSUL_HTTP_ADDR`
- Do not include `http://` or `https://`
- Prefer `CONSUL_CACERT` over disabling TLS verification
- On Kubernetes / OpenShift, extract the active CA from the cluster secret instead of relying on an older local copy:
```bash
kubectl get secret -n consul consul-ca-cert -o jsonpath='{.data.tls\.crt}' | base64 --decode > consul-ca-from-cluster.pem
```
- Validate the CA bundle before using it:
```bash
openssl s_client \
  -connect 127.0.0.1:8501 \
  -CAfile ./consul-ca-from-cluster.pem \
  </dev/null
```
- `Verify return code: 0 (ok)` confirms the CA matches the running HTTPS listener
- Use `CONSUL_HTTP_SSL_VERIFY=false` only for short-lived local debugging

### Issue: "Permission denied: anonymous token lacks permission"
**Solution:** Create a dedicated Consul ACL policy and token for the agent:
```bash
consul acl policy create \
  -name agent-troubleshooter-admin \
  -description "Admin-level read policy for troubleshooting agent" \
  -rules @examples/consul-agent-troubleshooter-policy.hcl

consul acl token create \
  -description "Token for k8s-consul troubleshooting agent" \
  -policy-name agent-troubleshooter-admin
```

Then set the token in your environment:
```bash
export CONSUL_HTTP_TOKEN=<secret-id>
```

## What Can I Ask?

### Kubernetes Questions
- "List all pods in namespace production"
- "Check the status of pod xyz-123"
- "Show me logs for pod abc-456"
- "Why is my pod in CrashLoopBackOff?"
- "Describe pod my-app-789"

### Consul Questions
- "List all services in Consul"
- "Check the health of service web-api"
- "Show me all Consul intentions"
- "Can service A connect to service B?"
- "Get all instances of service payment-api"

### General Troubleshooting
- "My application is not working, can you help?"
- "Service X cannot connect to service Y"
- "Why are my pods not starting?"

## Next Steps

1. **Read the full README**: `README.md` for detailed documentation
2. **Explore examples**: `examples/troubleshooting_scenarios.md` for common scenarios
3. **Customize**: Modify `config/agent_config.yaml` for your needs
4. **Learn**: The agent uses LangChain's ReAct pattern - great for learning!

## Getting Help

If you encounter issues:
1. Check the error message carefully
2. Verify your environment setup
3. Try with `--verbose` flag for more details
4. Review the examples in `examples/troubleshooting_scenarios.md`

## Tips for Best Results

1. **Be specific**: Include pod names, namespaces, and error messages
2. **Provide context**: Mention what you've already tried
3. **Ask follow-ups**: The agent can dive deeper based on initial findings
4. **Use natural language**: No need for exact commands, just describe the issue

---

**You're all set! Start troubleshooting! 🚀**

For more advanced usage, see the full [README.md](README.md)