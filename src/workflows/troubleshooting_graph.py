"""
LangGraph-based troubleshooting workflow with state machines.

This module implements Phase 3 features:
- State-based workflow management
- Parallel tool execution
- Conditional routing based on issue type
- Complex decision trees
- Automated remediation suggestions
"""

from typing import TypedDict, Annotated, Sequence, Literal, Optional, Dict, Any, List
from typing_extensions import NotRequired
import operator
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..tools import KubernetesTools, ConsulTools
from ..intent_classifier import intent_classifier, IntentType
from ..error_patterns import pattern_matcher


class WorkflowState(TypedDict):
    """
    State for the troubleshooting workflow.
    
    This state is passed between nodes and accumulates information
    as the workflow progresses through different diagnostic stages.
    """
    # Core state
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    issue_type: NotRequired[str]
    
    # Diagnostic results
    k8s_diagnostics: NotRequired[Dict[str, Any]]
    consul_diagnostics: NotRequired[Dict[str, Any]]
    proxy_diagnostics: NotRequired[Dict[str, Any]]
    
    # Analysis results
    detected_patterns: NotRequired[List[Dict[str, Any]]]
    intent_classification: NotRequired[Dict[str, Any]]
    root_cause: NotRequired[str]
    
    # Remediation
    remediation_steps: NotRequired[List[str]]
    automated_fixes: NotRequired[List[Dict[str, Any]]]
    
    # Workflow control
    next_action: NotRequired[str]
    parallel_tasks: NotRequired[List[str]]
    completed_tasks: NotRequired[List[str]]
    
    # Metadata
    workflow_start_time: NotRequired[datetime]
    workflow_end_time: NotRequired[datetime]
    execution_path: NotRequired[List[str]]


class TroubleshootingWorkflow:
    """
    LangGraph-based troubleshooting workflow orchestrator.
    
    This class implements a state machine for complex troubleshooting scenarios
    with parallel execution, conditional routing, and automated remediation.
    """
    
    def __init__(
        self,
        k8s_tools: KubernetesTools,
        consul_tools: ConsulTools,
        llm: ChatOpenAI,
        verbose: bool = False
    ):
        """
        Initialize the troubleshooting workflow.
        
        Args:
            k8s_tools: Kubernetes tools instance
            consul_tools: Consul tools instance
            llm: Language model for reasoning
            verbose: Enable verbose logging
        """
        self.k8s_tools = k8s_tools
        self.consul_tools = consul_tools
        self.llm = llm
        self.verbose = verbose
        
        # Build the workflow graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine for troubleshooting.
        
        Workflow structure:
        1. detect_issue: Classify the issue type and extract entities
        2. route_by_issue: Conditional routing based on issue type
        3. k8s_diagnostic: Kubernetes-specific diagnostics (parallel)
        4. consul_diagnostic: Consul-specific diagnostics (parallel)
        5. proxy_diagnostic: Proxy-specific diagnostics (parallel)
        6. analyze_results: Synthesize findings and identify root cause
        7. generate_remediation: Create remediation steps
        8. suggest_automation: Suggest automated fixes
        """
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("detect_issue", self._detect_issue_node)
        workflow.add_node("k8s_diagnostic", self._k8s_diagnostic_node)
        workflow.add_node("consul_diagnostic", self._consul_diagnostic_node)
        workflow.add_node("proxy_diagnostic", self._proxy_diagnostic_node)
        workflow.add_node("analyze_results", self._analyze_results_node)
        workflow.add_node("generate_remediation", self._generate_remediation_node)
        workflow.add_node("suggest_automation", self._suggest_automation_node)
        
        # Set entry point
        workflow.set_entry_point("detect_issue")
        
        # Add conditional routing from detect_issue
        workflow.add_conditional_edges(
            "detect_issue",
            self._route_by_issue_type,
            {
                "k8s_only": "k8s_diagnostic",
                "consul_only": "consul_diagnostic",
                "proxy_only": "proxy_diagnostic",
                "k8s_consul": "k8s_diagnostic",  # Will parallel to consul
                "full_stack": "k8s_diagnostic",  # Will parallel to all
                "unknown": "analyze_results"
            }
        )
        
        # Add edges for parallel execution paths
        workflow.add_edge("k8s_diagnostic", "analyze_results")
        workflow.add_edge("consul_diagnostic", "analyze_results")
        workflow.add_edge("proxy_diagnostic", "analyze_results")
        
        # Sequential flow after analysis
        workflow.add_edge("analyze_results", "generate_remediation")
        workflow.add_edge("generate_remediation", "suggest_automation")
        workflow.add_edge("suggest_automation", END)
        
        return workflow.compile()
    
    def _detect_issue_node(self, state: WorkflowState) -> WorkflowState:
        """
        Detect and classify the issue type.
        
        This node:
        1. Uses intent classification to understand the query
        2. Matches against known error patterns
        3. Determines which diagnostic paths to take
        """
        if self.verbose:
            print("\n[Workflow] Detecting issue type...")
        
        query = state["query"]
        
        # Classify intent
        intent_result = intent_classifier.classify(query)
        
        # Match error patterns
        pattern_matches = pattern_matcher.match(query)
        
        # Convert Intent to dict for state
        intent_dict = {
            "intent_type": intent_result.intent_type.value,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "suggested_flow": intent_result.suggested_flow,
            "priority": intent_result.priority
        }
        
        # Convert patterns to dicts
        pattern_dicts = [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "subcategory": p.subcategory,
                "symptoms": p.symptoms,
                "root_causes": p.root_causes,
                "solutions": p.solutions,
                "severity": p.severity,
                "keywords": p.keywords,
                "relevance_score": 1.0  # Will be calculated by matcher
            }
            for p in pattern_matches[:5]  # Top 5 patterns
        ]
        
        # Determine issue type based on intent and patterns
        issue_type = self._determine_issue_type(intent_dict, pattern_dicts)
        
        # Track execution path
        execution_path = state.get("execution_path", [])
        execution_path.append("detect_issue")
        
        return {
            **state,
            "intent_classification": intent_dict,
            "detected_patterns": pattern_dicts,
            "issue_type": issue_type,
            "workflow_start_time": datetime.now(),
            "execution_path": execution_path,
            "messages": [
                SystemMessage(content=f"Issue classified as: {issue_type}")
            ]
        }
    
    def _determine_issue_type(
        self,
        intent_result: Dict[str, Any],
        pattern_matches: List[Dict[str, Any]]
    ) -> str:
        """
        Determine the issue type based on intent and patterns.
        
        Returns one of:
        - k8s_only: Kubernetes-specific issue
        - consul_only: Consul-specific issue
        - proxy_only: Proxy/sidecar-specific issue
        - k8s_consul: Both K8s and Consul involved
        - full_stack: All components involved
        - unknown: Cannot determine
        """
        intent_type = intent_result.get("intent_type", "")
        
        # Check intent type
        k8s_intents = ["pod_status", "pod_logs", "pod_health", "pod_restart", "pod_events"]
        consul_intents = ["service_health", "service_discovery", "intention_check"]
        proxy_intents = ["proxy_status", "proxy_health", "proxy_config"]
        
        is_k8s = any(intent in intent_type for intent in k8s_intents)
        is_consul = any(intent in intent_type for intent in consul_intents)
        is_proxy = any(intent in intent_type for intent in proxy_intents)
        
        # Check pattern categories
        if pattern_matches:
            categories = {match.get("category", "") for match in pattern_matches}
            is_k8s = is_k8s or "kubernetes" in categories
            is_consul = is_consul or "consul" in categories
            is_proxy = is_proxy or "proxy" in categories
        
        # Determine combined type
        if is_k8s and is_consul and is_proxy:
            return "full_stack"
        elif is_k8s and is_consul:
            return "k8s_consul"
        elif is_k8s:
            return "k8s_only"
        elif is_consul:
            return "consul_only"
        elif is_proxy:
            return "proxy_only"
        else:
            return "unknown"
    
    def _route_by_issue_type(self, state: WorkflowState) -> str:
        """
        Route to appropriate diagnostic nodes based on issue type.
        
        This is a conditional edge function that determines the next node(s).
        """
        issue_type = state.get("issue_type", "unknown")
        
        if self.verbose:
            print(f"[Workflow] Routing based on issue type: {issue_type}")
        
        return issue_type
    
    def _k8s_diagnostic_node(self, state: WorkflowState) -> WorkflowState:
        """
        Perform Kubernetes diagnostics.
        
        This node can run in parallel with other diagnostic nodes.
        """
        if self.verbose:
            print("\n[Workflow] Running Kubernetes diagnostics...")
        
        diagnostics = {}
        intent = state.get("intent_classification", {})
        entities = intent.get("entities", {})
        
        # Extract pod name if available
        pod_name = entities.get("pod_name")
        namespace = entities.get("namespace", "default")
        
        try:
            if pod_name:
                # Get pod status
                status_result = self.k8s_tools.get_pod_status(pod_name, namespace)
                diagnostics["pod_status"] = status_result
                
                # Get pod logs if pod exists
                if "not found" not in status_result.lower():
                    logs_result = self.k8s_tools.get_pod_logs(pod_name, namespace)
                    diagnostics["pod_logs"] = logs_result
            else:
                # List pods in namespace
                list_result = self.k8s_tools.list_pods(namespace)
                diagnostics["pod_list"] = list_result
        
        except Exception as e:
            diagnostics["error"] = str(e)
        
        # Track execution path
        execution_path = state.get("execution_path", [])
        execution_path.append("k8s_diagnostic")
        
        return {
            **state,
            "k8s_diagnostics": diagnostics,
            "execution_path": execution_path,
            "messages": [
                AIMessage(content="Kubernetes diagnostics completed")
            ]
        }
    
    def _consul_diagnostic_node(self, state: WorkflowState) -> WorkflowState:
        """
        Perform Consul diagnostics.
        
        This node can run in parallel with other diagnostic nodes.
        """
        if self.verbose:
            print("\n[Workflow] Running Consul diagnostics...")
        
        diagnostics = {}
        intent = state.get("intent_classification", {})
        entities = intent.get("entities", {})
        
        # Extract service names if available
        service_name = entities.get("service_name")
        
        try:
            if service_name:
                # Get service health
                health_result = self.consul_tools.get_service_health(service_name)
                diagnostics["service_health"] = health_result
                
                # Get service instances
                instances_result = self.consul_tools.get_service_instances(service_name)
                diagnostics["service_instances"] = instances_result
            else:
                # List all services
                services_result = self.consul_tools.list_services()
                diagnostics["services_list"] = services_result
        
        except Exception as e:
            diagnostics["error"] = str(e)
        
        # Track execution path
        execution_path = state.get("execution_path", [])
        execution_path.append("consul_diagnostic")
        
        return {
            **state,
            "consul_diagnostics": diagnostics,
            "execution_path": execution_path,
            "messages": [
                AIMessage(content="Consul diagnostics completed")
            ]
        }
    
    def _proxy_diagnostic_node(self, state: WorkflowState) -> WorkflowState:
        """
        Perform proxy/sidecar diagnostics.
        
        This node can run in parallel with other diagnostic nodes.
        """
        if self.verbose:
            print("\n[Workflow] Running proxy diagnostics...")
        
        diagnostics = {}
        intent = state.get("intent_classification", {})
        entities = intent.get("entities", {})
        
        # Extract pod name for proxy diagnostics
        pod_name = entities.get("pod_name")
        namespace = entities.get("namespace", "default")
        
        try:
            if pod_name:
                # Check if pod has Consul Connect sidecar
                from ..tools.consul_connect import ConsulConnectTools
                connect_tools = ConsulConnectTools(self.k8s_tools.v1, namespace)
                
                # Get proxy status
                status_result = connect_tools.get_proxy_status(pod_name)
                diagnostics["proxy_status"] = status_result
        
        except Exception as e:
            diagnostics["error"] = str(e)
        
        # Track execution path
        execution_path = state.get("execution_path", [])
        execution_path.append("proxy_diagnostic")
        
        return {
            **state,
            "proxy_diagnostics": diagnostics,
            "execution_path": execution_path,
            "messages": [
                AIMessage(content="Proxy diagnostics completed")
            ]
        }
    
    def _analyze_results_node(self, state: WorkflowState) -> WorkflowState:
        """
        Analyze all diagnostic results and identify root cause.
        
        This node synthesizes findings from all parallel diagnostic paths.
        """
        if self.verbose:
            print("\n[Workflow] Analyzing results...")
        
        # Gather all diagnostic results
        k8s_diag = state.get("k8s_diagnostics", {})
        consul_diag = state.get("consul_diagnostics", {})
        proxy_diag = state.get("proxy_diagnostics", {})
        patterns = state.get("detected_patterns", [])
        
        # Use LLM to analyze and synthesize
        analysis_prompt = self._build_analysis_prompt(
            state["query"],
            k8s_diag,
            consul_diag,
            proxy_diag,
            patterns
        )
        
        response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
        root_cause = response.content if isinstance(response.content, str) else str(response.content)
        
        # Track execution path
        execution_path = state.get("execution_path", [])
        execution_path.append("analyze_results")
        
        return {
            **state,
            "root_cause": root_cause,
            "execution_path": execution_path,
            "messages": [
                AIMessage(content=f"Root cause analysis: {root_cause}")
            ]
        }
    
    def _generate_remediation_node(self, state: WorkflowState) -> WorkflowState:
        """
        Generate remediation steps based on root cause analysis.
        """
        if self.verbose:
            print("\n[Workflow] Generating remediation steps...")
        
        root_cause = state.get("root_cause", "Unknown")
        patterns = state.get("detected_patterns", [])
        
        # Start with pattern-based solutions
        remediation_steps = []
        
        for pattern in patterns:
            if "solution" in pattern:
                remediation_steps.extend(pattern["solution"])
        
        # Use LLM to generate additional steps if needed
        if not remediation_steps or len(remediation_steps) < 3:
            remediation_prompt = f"""
Based on the root cause analysis:
{root_cause}

Generate 3-5 specific, actionable remediation steps to resolve this issue.
Format as a numbered list.
"""
            response = self.llm.invoke([HumanMessage(content=remediation_prompt)])
            content = response.content if isinstance(response.content, str) else str(response.content)
            llm_steps = content.strip().split("\n")
            remediation_steps.extend([s.strip() for s in llm_steps if s.strip()])
        
        # Track execution path
        execution_path = state.get("execution_path", [])
        execution_path.append("generate_remediation")
        
        return {
            **state,
            "remediation_steps": remediation_steps,
            "execution_path": execution_path,
            "messages": [
                AIMessage(content="Remediation steps generated")
            ]
        }
    
    def _suggest_automation_node(self, state: WorkflowState) -> WorkflowState:
        """
        Suggest automated fixes that can be applied.
        
        This is a Phase 3 feature for automated remediation.
        """
        if self.verbose:
            print("\n[Workflow] Suggesting automated fixes...")
        
        automated_fixes = []
        patterns = state.get("detected_patterns", [])
        
        # Check if any patterns have automated fixes
        for pattern in patterns:
            if pattern.get("automatable", False):
                automated_fixes.append({
                    "pattern": pattern["name"],
                    "fix_type": pattern.get("fix_type", "manual"),
                    "description": pattern.get("automation_description", ""),
                    "safe": pattern.get("safe_to_automate", False)
                })
        
        # Track execution path and end time
        execution_path = state.get("execution_path", [])
        execution_path.append("suggest_automation")
        
        return {
            **state,
            "automated_fixes": automated_fixes,
            "workflow_end_time": datetime.now(),
            "execution_path": execution_path,
            "messages": [
                AIMessage(content=f"Found {len(automated_fixes)} automated fix suggestions")
            ]
        }
    
    def _build_analysis_prompt(
        self,
        query: str,
        k8s_diag: Dict[str, Any],
        consul_diag: Dict[str, Any],
        proxy_diag: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> str:
        """Build a comprehensive analysis prompt for the LLM."""
        
        prompt = f"""Analyze the following troubleshooting data and identify the root cause.

Original Query: {query}

Kubernetes Diagnostics:
{self._format_diagnostics(k8s_diag)}

Consul Diagnostics:
{self._format_diagnostics(consul_diag)}

Proxy Diagnostics:
{self._format_diagnostics(proxy_diag)}

Detected Error Patterns:
{self._format_patterns(patterns)}

Provide a concise root cause analysis (2-3 sentences) that explains:
1. What is the primary issue
2. Why it's happening
3. What component(s) are affected
"""
        return prompt
    
    def _format_diagnostics(self, diag: Dict[str, Any]) -> str:
        """Format diagnostic results for the prompt."""
        if not diag:
            return "No diagnostics available"
        
        lines = []
        for key, value in diag.items():
            if isinstance(value, str):
                # Truncate long strings
                value_str = value[:500] + "..." if len(value) > 500 else value
                lines.append(f"  {key}: {value_str}")
            else:
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines) if lines else "No data"
    
    def _format_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format detected patterns for the prompt."""
        if not patterns:
            return "No patterns detected"
        
        lines = []
        for i, pattern in enumerate(patterns[:3], 1):  # Top 3 patterns
            lines.append(f"  {i}. {pattern.get('name', 'Unknown')} (confidence: {pattern.get('relevance_score', 0):.2f})")
            lines.append(f"     Category: {pattern.get('category', 'Unknown')}")
        
        return "\n".join(lines)
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the troubleshooting workflow for a given query.
        
        Args:
            query: The troubleshooting query
            
        Returns:
            Final workflow state with all results
        """
        initial_state: WorkflowState = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "execution_path": []
        }
        
        # Execute the workflow
        final_state = self.graph.invoke(initial_state)
        
        return final_state
    
    def visualize(self, output_path: str = "workflow_graph.png"):
        """
        Visualize the workflow graph.
        
        Args:
            output_path: Path to save the visualization
        """
        try:
            from IPython.display import Image, display
            display(Image(self.graph.get_graph().draw_mermaid_png()))
        except ImportError:
            print("Visualization requires IPython. Install with: pip install ipython")

# Made with Bob
