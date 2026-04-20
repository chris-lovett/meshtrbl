"""
Tests for intent classification and routing.
"""

import pytest
from src.intent_classifier import (
    IntentClassifier,
    IntentType,
    intent_classifier,
    classify_intent
)


class TestIntentClassifier:
    """Test suite for IntentClassifier."""
    
    def test_pod_status_check_intent(self):
        """Test classification of pod status check queries."""
        queries = [
            "check status of pod web-app-123",
            "what's the status of pod api-server",
            "is pod nginx-xyz running",
            "show me the pod status",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.POD_STATUS_CHECK
            assert intent.confidence >= 0.85
            assert intent.priority <= 3
    
    def test_pod_crash_investigation_intent(self):
        """Test classification of pod crash queries."""
        queries = [
            "pod web-app is crashing",
            "why is pod api-server restarting",
            "pod nginx-xyz keeps crashing",
            "CrashLoopBackOff on pod database",
            "pod won't stay up",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.POD_CRASH_INVESTIGATION
            assert intent.confidence >= 0.9
            assert intent.priority == 1  # Critical priority
    
    def test_pod_logs_review_intent(self):
        """Test classification of log review queries."""
        queries = [
            "show logs for pod web-app",
            "get logs from pod api-server",
            "what do the logs say for nginx",
            "check pod logs",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.POD_LOGS_REVIEW
            assert intent.confidence >= 0.85
    
    def test_pod_not_starting_intent(self):
        """Test classification of pod startup issues."""
        queries = [
            "pod web-app won't start",
            "pod is stuck in pending",
            "ImagePullBackOff error",
            "can't pull image for pod",
            "pod not starting",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.POD_NOT_STARTING
            assert intent.confidence >= 0.9
            assert intent.priority == 1
    
    def test_pod_resource_issue_intent(self):
        """Test classification of resource-related issues."""
        queries = [
            "OOMKilled error",
            "out of memory issue",
            "pod has memory limit problem",
            "insufficient CPU",
            "resource quota exceeded",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.POD_RESOURCE_ISSUE
            assert intent.confidence >= 0.9
            assert intent.priority == 1
    
    def test_service_connectivity_intent(self):
        """Test classification of service connectivity issues."""
        queries = [
            "can't connect to service api",
            "service web is not responding",
            "connection refused to database service",
            "unable to reach service",
            "service connectivity issue",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.SERVICE_CONNECTIVITY
            assert intent.confidence >= 0.85
            assert intent.priority <= 2
    
    def test_consul_service_health_intent(self):
        """Test classification of Consul health check queries."""
        queries = [
            "check consul service health for api",
            "is consul service web healthy",
            "consul health check status",
            "verify service health in consul",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.CONSUL_SERVICE_HEALTH
            assert intent.confidence >= 0.85
    
    def test_consul_intention_check_intent(self):
        """Test classification of Consul intention queries."""
        queries = [
            "check consul intention from web to api",
            "can web talk to database",
            "verify intention between services",
            "is traffic allowed from frontend to backend",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.CONSUL_INTENTION_CHECK
            assert intent.confidence >= 0.85
    
    def test_consul_connect_issue_intent(self):
        """Test classification of Consul Connect issues."""
        queries = [
            "consul connect not working",
            "sidecar proxy issue",
            "envoy proxy error",
            "upstream connect error",
            "503 service unavailable",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.CONSUL_CONNECT_ISSUE
            assert intent.confidence >= 0.9
            assert intent.priority == 1
    
    def test_error_pattern_match_intent(self):
        """Test classification of error pattern queries."""
        queries = [
            "error: connection refused",
            "CrashLoopBackOff",
            "ImagePullBackOff",
            "exit code 137",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.intent_type == IntentType.ERROR_PATTERN_MATCH
            assert intent.confidence >= 0.8
    
    def test_entity_extraction_pod_name(self):
        """Test extraction of pod names from queries."""
        query = "check status of pod web-app-123"
        intent = intent_classifier.classify(query)
        
        assert "pod_name" in intent.entities
        assert intent.entities["pod_name"] == "web-app-123"
    
    def test_entity_extraction_namespace(self):
        """Test extraction of namespace from queries."""
        query = "check pod in namespace production"
        intent = intent_classifier.classify(query)
        
        assert "namespace" in intent.entities
        assert intent.entities["namespace"] == "production"
    
    def test_entity_extraction_service_name(self):
        """Test extraction of service names from queries."""
        query = "check service api-gateway health"
        intent = intent_classifier.classify(query)
        
        assert "service_name" in intent.entities
        assert intent.entities["service_name"] == "api-gateway"
    
    def test_entity_extraction_error_text(self):
        """Test extraction of error messages from queries."""
        query = 'error: "connection refused on port 8080"'
        intent = intent_classifier.classify(query)
        
        assert "error_text" in intent.entities
        assert "connection refused" in intent.entities["error_text"]
    
    def test_entity_extraction_intentions(self):
        """Test extraction of source and destination for intentions."""
        query = "check intention from web to api"
        intent = intent_classifier.classify(query)
        
        assert "source_service" in intent.entities
        assert "destination_service" in intent.entities
        assert intent.entities["source_service"] == "web"
        assert intent.entities["destination_service"] == "api"
    
    def test_should_use_fast_path_high_confidence(self):
        """Test fast-path decision for high-confidence intents."""
        query = "pod web-app is crashing"
        intent = intent_classifier.classify(query)
        
        # High confidence, high priority, has flow
        assert intent_classifier.should_use_fast_path(intent) is True
    
    def test_should_not_use_fast_path_low_confidence(self):
        """Test fast-path decision for low-confidence intents."""
        query = "what is happening with my cluster"
        intent = intent_classifier.classify(query)
        
        # Low confidence should not use fast path
        assert intent_classifier.should_use_fast_path(intent) is False
    
    def test_get_flow_for_intent(self):
        """Test retrieval of troubleshooting flows."""
        flow = intent_classifier.get_flow(IntentType.POD_CRASH_INVESTIGATION)
        
        assert flow is not None
        assert flow.name == "Pod Crash Investigation"
        assert len(flow.steps) > 0
        assert flow.expected_duration is not None
    
    def test_flow_steps_structure(self):
        """Test that flow steps have correct structure."""
        flow = intent_classifier.get_flow(IntentType.POD_STATUS_CHECK)
        
        assert flow is not None
        for step in flow.steps:
            assert "tool" in step
            assert "param" in step
            assert isinstance(step["tool"], str)
            assert isinstance(step["param"], str)
    
    def test_priority_assignment_critical(self):
        """Test priority assignment for critical issues."""
        critical_queries = [
            "pod is crashing",
            "OOMKilled",
            "consul connect not working",
        ]
        
        for query in critical_queries:
            intent = intent_classifier.classify(query)
            assert intent.priority == 1, f"Query '{query}' should have priority 1"
    
    def test_priority_assignment_high(self):
        """Test priority assignment for high-priority issues."""
        high_priority_queries = [
            "can't connect to service",
            "check consul service health",
        ]
        
        for query in high_priority_queries:
            intent = intent_classifier.classify(query)
            assert intent.priority <= 2, f"Query '{query}' should have priority <= 2"
    
    def test_confidence_boost_with_entities(self):
        """Test that confidence is boosted when entities are found."""
        query_without_entity = "check pod status"
        query_with_entity = "check status of pod web-app-123"
        
        intent1 = intent_classifier.classify(query_without_entity)
        intent2 = intent_classifier.classify(query_with_entity)
        
        # Query with entity should have higher or equal confidence
        assert intent2.confidence >= intent1.confidence
    
    def test_general_troubleshooting_fallback(self):
        """Test fallback to general troubleshooting for unclear queries."""
        vague_queries = [
            "something is wrong",
            "help me debug",
            "cluster issues",
        ]
        
        for query in vague_queries:
            intent = intent_classifier.classify(query)
            # Should classify but with lower confidence
            assert intent.confidence < 0.9
    
    def test_multiple_pattern_matches(self):
        """Test queries that could match multiple patterns."""
        query = "pod web-app is crashing with OOMKilled error"
        intent = intent_classifier.classify(query)
        
        # Should pick the most relevant intent
        assert intent.intent_type in [
            IntentType.POD_CRASH_INVESTIGATION,
            IntentType.POD_RESOURCE_ISSUE
        ]
        assert intent.confidence >= 0.9
    
    def test_convenience_function(self):
        """Test the convenience function classify_intent."""
        query = "check pod status"
        intent = classify_intent(query)
        
        assert intent is not None
        assert isinstance(intent.intent_type, IntentType)
        assert 0.0 <= intent.confidence <= 1.0
        assert intent.priority >= 1


class TestIntentFlows:
    """Test suite for troubleshooting flows."""
    
    def test_all_critical_intents_have_flows(self):
        """Test that all critical intents have defined flows."""
        critical_intents = [
            IntentType.POD_CRASH_INVESTIGATION,
            IntentType.POD_NOT_STARTING,
            IntentType.POD_RESOURCE_ISSUE,
            IntentType.CONSUL_CONNECT_ISSUE,
        ]
        
        for intent_type in critical_intents:
            flow = intent_classifier.get_flow(intent_type)
            assert flow is not None, f"Critical intent {intent_type} should have a flow"
    
    def test_flow_tool_names_are_valid(self):
        """Test that flow tool names match actual tool names."""
        valid_tools = [
            "get_pod_status",
            "get_pod_logs",
            "describe_pod",
            "list_pods",
            "match_error_pattern",
            "search_error_patterns",
            "get_service_health",
            "get_service_instances",
            "check_consul_intention",
            "list_consul_intentions",
        ]
        
        for intent_type in IntentType:
            flow = intent_classifier.get_flow(intent_type)
            if flow:
                for step in flow.steps:
                    assert step["tool"] in valid_tools, \
                        f"Tool '{step['tool']}' in flow '{flow.name}' is not valid"
    
    def test_flow_descriptions_are_meaningful(self):
        """Test that flows have meaningful descriptions."""
        for intent_type in IntentType:
            flow = intent_classifier.get_flow(intent_type)
            if flow:
                assert len(flow.description) > 10
                assert flow.name
                assert flow.expected_duration


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_query(self):
        """Test classification of empty query."""
        intent = intent_classifier.classify("")
        assert intent is not None
        assert intent.intent_type == IntentType.GENERAL_TROUBLESHOOTING
    
    def test_very_long_query(self):
        """Test classification of very long query."""
        long_query = "check pod status " * 100
        intent = intent_classifier.classify(long_query)
        assert intent is not None
    
    def test_special_characters_in_query(self):
        """Test queries with special characters."""
        queries = [
            "pod web-app-123_v2 is crashing",
            "check service api.gateway health",
            "error: [FATAL] connection refused",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent is not None
    
    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive."""
        queries = [
            "Pod web-app is CRASHING",
            "CHECK POD STATUS",
            "consul SERVICE health",
        ]
        
        for query in queries:
            intent = intent_classifier.classify(query)
            assert intent.confidence > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
