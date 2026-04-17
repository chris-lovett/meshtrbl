# Troubleshooting Scenarios

This document provides example scenarios and how the agent can help troubleshoot them.

## Kubernetes Scenarios

### Scenario 1: CrashLoopBackOff

**Problem:** Pod keeps restarting

**Questions to ask the agent:**
```
"My pod web-app-7d8f9c is in CrashLoopBackOff. Can you help diagnose the issue?"

"Why does my application pod keep restarting?"

"Check the status and logs of pod web-app-7d8f9c in namespace production"
```

**What the agent will do:**
1. Check pod status to see the current state
2. Retrieve recent logs to identify errors
3. Look at restart count and exit codes
4. Analyze error messages
5. Provide diagnosis and recommendations

**Common causes the agent can identify:**
- Out of Memory (OOMKilled)
- Application crashes
- Missing dependencies
- Configuration errors
- Failed health checks

---

### Scenario 2: ImagePullBackOff

**Problem:** Cannot pull container image

**Questions to ask:**
```
"Pod api-backend can't pull its image. What's wrong?"

"I'm getting ImagePullBackOff error. How do I fix it?"
```

**What the agent will do:**
1. Check pod status and events
2. Identify the image being pulled
3. Look for authentication errors
4. Check for typos in image name
5. Suggest solutions

**Common causes:**
- Image doesn't exist
- Wrong image tag
- Missing image pull secrets
- Registry authentication issues
- Network connectivity problems

---

### Scenario 3: Pending Pods

**Problem:** Pod stuck in Pending state

**Questions to ask:**
```
"Why is my pod stuck in Pending state?"

"Pod database-0 won't schedule. Can you investigate?"
```

**What the agent will do:**
1. Check pod status and conditions
2. Look at pod events for scheduling failures
3. Check resource requests vs available resources
4. Identify node selector or affinity issues
5. Suggest solutions

**Common causes:**
- Insufficient CPU/memory on nodes
- Node selector doesn't match any nodes
- PersistentVolume not available
- Taints and tolerations mismatch

---

## Consul Service Mesh Scenarios

### Scenario 4: Service Not Registered

**Problem:** Service not appearing in Consul

**Questions to ask:**
```
"My service 'payment-api' is not showing up in Consul. Why?"

"List all services in Consul and check if payment-api is registered"
```

**What the agent will do:**
1. List all registered services
2. Check if the service exists
3. Verify service registration configuration
4. Check Consul annotations on the pod
5. Suggest registration fixes

**Common causes:**
- Missing Consul annotations
- Consul agent not running
- Service registration failed
- Wrong service name configuration

---

### Scenario 5: Service Health Check Failing

**Problem:** Service shows as unhealthy in Consul

**Questions to ask:**
```
"Service 'web-frontend' is failing health checks. What's the issue?"

"Check the health status of web-frontend service in Consul"
```

**What the agent will do:**
1. Get service health status
2. Identify which health checks are failing
3. Show health check output/errors
4. Analyze the failure reason
5. Suggest fixes

**Common causes:**
- Application not responding on health check endpoint
- Wrong health check configuration
- Network connectivity issues
- Application startup taking too long
- Health check timeout too short

---

### Scenario 6: Service-to-Service Communication Blocked

**Problem:** One service cannot connect to another

**Questions to ask:**
```
"Service 'api' cannot connect to 'database'. Is it an intention issue?"

"Check if traffic is allowed from api to database in Consul"

"Show me all Consul intentions"
```

**What the agent will do:**
1. Check intentions between the services
2. Verify if traffic is explicitly allowed or denied
3. Check for wildcard intentions
4. Explain the current access rules
5. Suggest intention updates if needed

**Common causes:**
- DENY intention blocking traffic
- No explicit ALLOW intention (with default deny)
- Intention misconfiguration
- Wrong service names in intentions

---

### Scenario 7: Consul Connect Sidecar Issues

**Problem:** Sidecar proxy not working

**Questions to ask:**
```
"The Consul Connect sidecar for my service isn't working. Help?"

"Check if the sidecar proxy is running for service payment-api"
```

**What the agent will do:**
1. Check if sidecar container is running
2. Verify sidecar registration in Consul
3. Check sidecar logs for errors
4. Verify proxy configuration
5. Suggest fixes

**Common causes:**
- Sidecar container not injected
- Sidecar crashed or restarting
- mTLS certificate issues
- Proxy configuration errors
- Upstream service misconfiguration

---

## Combined Kubernetes + Consul Scenarios

### Scenario 8: Service Mesh Integration Issues

**Problem:** Service registered but not accessible through mesh

**Questions to ask:**
```
"My service is registered in Consul but other services can't reach it through the mesh"

"Check both Kubernetes and Consul status for service api-backend"
```

**What the agent will do:**
1. Check Kubernetes pod status
2. Verify Consul service registration
3. Check service health in Consul
4. Verify intentions
5. Check sidecar proxy status
6. Provide comprehensive diagnosis

---

### Scenario 9: Pod Restart Affecting Service Mesh

**Problem:** Pod restarts causing service disruption

**Questions to ask:**
```
"My pod keeps restarting and it's affecting service mesh connectivity"

"Investigate why web-service pod is restarting and if it's affecting Consul"
```

**What the agent will do:**
1. Check pod status and restart count
2. Analyze pod logs
3. Check Consul service health
4. Verify if service deregistration is happening
5. Suggest stability improvements

---

## Tips for Effective Troubleshooting

### Be Specific
❌ "Something is broken"
✅ "Pod web-app-7d8f9c in namespace production is in CrashLoopBackOff"

### Provide Context
❌ "Check the service"
✅ "Check the health status of payment-api service in Consul datacenter dc1"

### Ask Follow-up Questions
After initial diagnosis, ask:
- "Can you show me the logs?"
- "What are the recent events?"
- "How can I fix this?"

### Use the Agent's Expertise
The agent knows:
- Common error patterns
- Best practices
- Troubleshooting methodologies
- How Kubernetes and Consul interact

### Example Conversation Flow

```
You: My pod api-backend-5d7f8 is not working

Agent: Let me check the pod status first.
[Checks pod status]
I see the pod is in CrashLoopBackOff with 5 restarts. Let me get the logs.
[Retrieves logs]
The logs show an OOMKilled error. Your container is exceeding its memory limit.

You: How do I fix this?

Agent: You have a few options:
1. Increase the memory limit in your deployment
2. Investigate memory leaks in your application
3. Optimize your application's memory usage

Your current limit is 128Mi. Based on the usage pattern, I recommend 
increasing it to at least 256Mi. Would you like me to show you how to 
update the deployment?

You: Yes, please show me

Agent: Here's how to update the memory limit:
[Provides kubectl command or YAML example]
```

---

## Advanced Scenarios (Phase 2 & 3)

These scenarios will be supported in future phases:

### Phase 2: Pattern Recognition
- Automatic detection of common issues
- Historical context awareness
- Proactive suggestions

### Phase 3: Complex Workflows
- Multi-step diagnostics
- Parallel investigation
- Automated remediation suggestions
- Root cause analysis across multiple services

---

## Need Help?

If you're not sure what to ask, try:
- "List all pods in namespace production"
- "Show me all Consul services"
- "What tools do you have available?"
- "How can you help me troubleshoot?"

The agent will guide you through the troubleshooting process!