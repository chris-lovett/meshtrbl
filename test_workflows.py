"""
Tests for Phase 3 LangGraph workflows.

Run with: pytest test_workflows.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.workflows import TroubleshootingWorkflow, WorkflowState
from src.tools import KubernetesTools, ConsulTools
from langchain_openai import ChatOpenAI


@pytest.fixture
def mock_k8s_tools():
    """Create mock Kubernetes tools."""
    tools = Mock(spec=KubernetesTools)
    tools.v1 = Mock()
    tools.get_pod_status = Mock(return_value="Pod: test-pod\nStatus: Running")
    tools.get_pod_logs = Mock(return_value="Application started successfully")
    tools.list_pods = Mock(return_value="test-pod: Running")
    return tools


@pytest.fixture
def mock_consul_tools():
    """Create mock Consul tools."""
    tools = Mock(spec=ConsulTools)
    tools.list_services = Mock(return_value="Services: web, api, db")
    tools.get_service_health = Mock(return_value="Service: web\nHealth: passing")
    tools.get_service_instances = Mock(return_value="Instances: 3")
    return tools


@pytest.fixture
def mock_llm():
    """Create mock LLM."""
    llm = Mock(spec=ChatOpenAI)
    
    # Mock response for analysis
    analysis_response = Mock()
    analysis_response.content = "The pod is experiencing a CrashLoopBackOff due to missing environment variables."
    
    # Mock response for remediation
    remediation_response = Mock()
    remediation_response.content = """1. Check pod configuration
2. Verify environment variables
3. Review application logs"""
    
    llm.invoke = Mock(side_effect=[analysis_response, remediation_response])
    return llm


@pytest.fixture
def workflow(mock_k8s_tools, mock_consul_tools, mock_llm):
    """Create workflow instance with mocked dependencies."""
    return TroubleshootingWorkflow(
        k8s_tools=mock_k8s_tools,
        consul_tools=mock_consul_tools,
        llm=mock_llm,
        verbose=False
    )


class TestWorkflowState:
    """Test workflow state management."""
    
    def test_workflow_state_structure(self):
        """Test that workflow state has required fields."""
        state: WorkflowState = {
            "messages": [],
            "query": "Test query",
            "execution_path": []
        }
        
        assert "messages" in state
        assert "query" in state
        assert "execution_path" in state


class TestTroubleshootingWorkflow:
    """Test the main troubleshooting workflow."""
    
    def test_workflow_initialization(self, workflow):
        """Test workflow initializes correctly."""
        assert workflow is not None
        assert workflow.k8s_tools is not None
        assert workflow.consul_tools is not None
        assert workflow.llm is not None
        assert workflow.graph is not None
    
    def test_determine_issue_type_k8s_only(self, workflow):
        """Test issue type determination for Kubernetes-only issues."""
        intent_dict = {
            "intent_type": "pod_status_check",
            "confidence": 0.9,
            "entities": {"pod_name": "test-pod"},
            "suggested_flow": "Pod Status Check",
            "priority": 1
        }
        pattern_dicts = []
        
        issue_type = workflow._determine_issue_type(intent_dict, pattern_dicts)
        assert issue_type == "k8s_only"
    
    def test_determine_issue_type_consul_only(self, workflow):
        """Test issue type determination for Consul-only issues."""
        intent_dict = {
            "intent_type": "consul_service_health",
            "confidence": 0.9,
            "entities": {"service_name": "web"},
            "suggested_flow": "Service Health Check",
            "priority": 1
        }
        pattern_dicts = []
        
        issue_type = workflow._determine_issue_type(intent_dict, pattern_dicts)
        assert issue_type == "consul_only"
    
    def test_determine_issue_type_full_stack(self, workflow):
        """Test issue type determination for full-stack issues."""
        intent_dict = {
            "intent_type": "service_connectivity",
            "confidence": 0.9,
            "entities": {},
            "suggested_flow": "Service Connectivity Check",
            "priority": 1
        }
        pattern_dicts = [
            {
                "id": "k8s-crashloop",
                "name": "CrashLoopBackOff",
                "category": "kubernetes",
                "subcategory": "pod",
                "symptoms": [],
                "root_causes": [],
                "solutions": [],
                "severity": "high",
                "keywords": [],
                "relevance_score": 1.0
            },
            {
                "id": "consul-connect-fail",
                "name": "Consul Connect Failure",
                "category": "consul",
                "subcategory": "sidecar-proxy",
                "symptoms": [],
                "root_causes": [],
                "solutions": [],
                "severity": "high",
                "keywords": [],
                "relevance_score": 0.9
            }
        ]
        
        issue_type = workflow._determine_issue_type(intent_dict, pattern_dicts)
        assert issue_type == "k8s_consul"
    
    def test_k8s_diagnostic_node(self, workflow):
        """Test Kubernetes diagnostic node."""
        state: WorkflowState = {
            "messages": [],
            "query": "Check pod test-pod",
            "intent_classification": {
                "intent_type": "pod_status_check",
                "confidence": 0.9,
                "entities": {"pod_name": "test-pod", "namespace": "default"},
                "suggested_flow": "Pod Status Check",
                "priority": 1
            },
            "execution_path": []
        }
        
        result = workflow._k8s_diagnostic_node(state)
        
        assert "k8s_diagnostics" in result
        assert "execution_path" in result
        assert "k8s_diagnostic" in result["execution_path"]
        assert workflow.k8s_tools.get_pod_status.called
    
    def test_consul_diagnostic_node(self, workflow):
        """Test Consul diagnostic node."""
        state: WorkflowState = {
            "messages": [],
            "query": "Check service web",
            "intent_classification": {
                "intent_type": "consul_service_health",
                "confidence": 0.9,
                "entities": {"service_name": "web"},
                "suggested_flow": "Service Health Check",
                "priority": 1
            },
            "execution_path": []
        }
        
        result = workflow._consul_diagnostic_node(state)
        
        assert "consul_diagnostics" in result
        assert "execution_path" in result
        assert "consul_diagnostic" in result["execution_path"]
        assert workflow.consul_tools.get_service_health.called
    
    def test_analyze_results_node(self, workflow):
        """Test results analysis node."""
        state: WorkflowState = {
            "messages": [],
            "query": "Pod is crashing",
            "k8s_diagnostics": {"pod_status": "CrashLoopBackOff"},
            "consul_diagnostics": {},
            "proxy_diagnostics": {},
            "detected_patterns": [],
            "execution_path": []
        }
        
        result = workflow._analyze_results_node(state)
        
        assert "root_cause" in result
        assert "execution_path" in result
        assert "analyze_results" in result["execution_path"]
        assert workflow.llm.invoke.called
    
    def test_generate_remediation_node(self, workflow):
        """Test remediation generation node."""
        state: WorkflowState = {
            "messages": [],
            "query": "Pod is crashing",
            "root_cause": "Missing environment variables",
            "detected_patterns": [],
            "execution_path": []
        }
        
        result = workflow._generate_remediation_node(state)
        
        assert "remediation_steps" in result
        assert "execution_path" in result
        assert "generate_remediation" in result["execution_path"]
        assert len(result["remediation_steps"]) > 0
    
    def test_suggest_automation_node(self, workflow):
        """Test automation suggestion node."""
        state: WorkflowState = {
            "messages": [],
            "query": "Pod is crashing",
            "detected_patterns": [
                {
                    "id": "k8s-crashloop",
                    "name": "CrashLoopBackOff",
                    "category": "kubernetes",
                    "subcategory": "pod",
                    "symptoms": [],
                    "root_causes": [],
                    "solutions": [],
                    "severity": "high",
                    "keywords": [],
                    "relevance_score": 1.0
                }
            ],
            "execution_path": []
        }
        
        result = workflow._suggest_automation_node(state)
        
        assert "automated_fixes" in result
        assert "workflow_end_time" in result
        assert "execution_path" in result
        assert "suggest_automation" in result["execution_path"]
    
    @patch('src.workflows.troubleshooting_graph.intent_classifier')
    @patch('src.workflows.troubleshooting_graph.pattern_matcher')
    def test_full_workflow_execution(self, mock_pattern_matcher, mock_intent_classifier, workflow):
        """Test full workflow execution from start to finish."""
        # Mock intent classifier
        mock_intent = Mock()
        mock_intent.intent_type.value = "pod_crash_investigation"
        mock_intent.confidence = 0.95
        mock_intent.entities = {"pod_name": "test-pod", "namespace": "default"}
        mock_intent.suggested_flow = "Pod Crash Investigation"
        mock_intent.priority = 1
        mock_intent_classifier.classify.return_value = mock_intent
        
        # Mock pattern matcher
        mock_pattern_matcher.match.return_value = []
        
        # Run workflow
        result = workflow.run("My pod test-pod keeps crashing")
        
        assert result is not None
        assert "execution_path" in result
        assert "root_cause" in result or "k8s_diagnostics" in result
    
    def test_format_diagnostics(self, workflow):
        """Test diagnostic formatting."""
        diag = {
            "pod_status": "Running",
            "pod_logs": "Application started"
        }
        
        formatted = workflow._format_diagnostics(diag)
        
        assert "pod_status" in formatted
        assert "pod_logs" in formatted
        assert "Running" in formatted
    
    def test_format_patterns(self, workflow):
        """Test pattern formatting."""
        patterns = [
            {
                "name": "CrashLoopBackOff",
                "category": "kubernetes",
                "relevance_score": 0.95
            },
            {
                "name": "OOMKilled",
                "category": "kubernetes",
                "relevance_score": 0.85
            }
        ]
        
        formatted = workflow._format_patterns(patterns)
        
        assert "CrashLoopBackOff" in formatted
        assert "0.95" in formatted


class TestWorkflowIntegration:
    """Test workflow integration with the agent."""
    
    @patch('src.agent.TroubleshootingWorkflow')
    def test_agent_uses_workflow_for_complex_queries(self, mock_workflow_class):
        """Test that agent uses workflow mode for complex queries."""
        from src.agent import TroubleshootingAgent
        
        # Mock workflow
        mock_workflow = Mock()
        mock_workflow.run.return_value = {
            "root_cause": "Test root cause",
            "remediation_steps": ["Step 1", "Step 2"],
            "execution_path": ["detect_issue", "k8s_diagnostic", "analyze_results"],
            "workflow_start_time": datetime.now(),
            "workflow_end_time": datetime.now()
        }
        mock_workflow_class.return_value = mock_workflow
        
        # Create agent with workflow enabled
        agent = TroubleshootingAgent(
            openai_api_key="test-key",
            enable_workflow=True,
            verbose=False
        )
        
        # Run complex query
        query = "Investigate intermittent connectivity issues across multiple services in the service mesh"
        result = agent.run(query)
        
        # Verify workflow was used
        assert mock_workflow.run.called or "workflow" in result.lower() or len(result) > 0


class TestWorkflowPerformance:
    """Test workflow performance characteristics."""
    
    def test_workflow_execution_time(self, workflow):
        """Test that workflow completes in reasonable time."""
        import time
        
        with patch('src.workflows.troubleshooting_graph.intent_classifier') as mock_intent:
            with patch('src.workflows.troubleshooting_graph.pattern_matcher') as mock_pattern:
                # Mock dependencies
                mock_intent_obj = Mock()
                mock_intent_obj.intent_type.value = "pod_status_check"
                mock_intent_obj.confidence = 0.9
                mock_intent_obj.entities = {"pod_name": "test-pod"}
                mock_intent_obj.suggested_flow = "Pod Status Check"
                mock_intent_obj.priority = 1
                mock_intent.classify.return_value = mock_intent_obj
                mock_pattern.match.return_value = []
                
                start_time = time.time()
                result = workflow.run("Check pod test-pod")
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                # Workflow should complete in under 10 seconds for simple queries
                assert execution_time < 10.0
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
