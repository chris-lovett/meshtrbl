"""
Intent classification and direct routing for common troubleshooting flows.

This module provides intelligent classification of user queries to enable
fast-path routing for common troubleshooting scenarios, reducing latency
and improving user experience.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """Types of troubleshooting intents."""
    
    # Pod-related intents
    POD_STATUS_CHECK = "pod_status_check"
    POD_CRASH_INVESTIGATION = "pod_crash_investigation"
    POD_LOGS_REVIEW = "pod_logs_review"
    POD_NOT_STARTING = "pod_not_starting"
    POD_RESOURCE_ISSUE = "pod_resource_issue"
    
    # Service/Network intents
    SERVICE_CONNECTIVITY = "service_connectivity"
    SERVICE_DISCOVERY = "service_discovery"
    DNS_RESOLUTION = "dns_resolution"
    
    # Consul-specific intents
    CONSUL_SERVICE_HEALTH = "consul_service_health"
    CONSUL_INTENTION_CHECK = "consul_intention_check"
    CONSUL_CONNECT_ISSUE = "consul_connect_issue"
    CONSUL_REGISTRATION = "consul_registration"
    
    # Error pattern intents
    ERROR_PATTERN_MATCH = "error_pattern_match"
    KNOWN_ERROR_DIAGNOSIS = "known_error_diagnosis"
    
    # General intents
    GENERAL_TROUBLESHOOTING = "general_troubleshooting"
    INFORMATION_QUERY = "information_query"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Represents a classified user intent."""
    
    intent_type: IntentType
    confidence: float  # 0.0 to 1.0
    entities: Dict[str, str]  # Extracted entities (pod names, namespaces, etc.)
    suggested_flow: str  # Suggested troubleshooting flow
    priority: int = 1  # 1 (highest) to 5 (lowest)


@dataclass
class TroubleshootingFlow:
    """Defines a direct troubleshooting flow for an intent."""
    
    name: str
    description: str
    steps: List[Dict[str, str]]  # List of tool calls with parameters
    expected_duration: str  # e.g., "5-10 seconds"


class IntentClassifier:
    """Classifies user queries into troubleshooting intents."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.flows = self._initialize_flows()
    
    def _initialize_patterns(self) -> Dict[IntentType, List[Dict]]:
        """Initialize intent recognition patterns."""
        return {
            IntentType.POD_STATUS_CHECK: [
                {
                    "patterns": [
                        r"(?:check|show|get|what(?:'s| is)) (?:the )?status (?:of )?(?:pod|pods?)",
                        r"is (?:the )?pod .+ (?:running|up|healthy)",
                        r"pod .+ status",
                        r"what(?:'s| is) (?:the )?state (?:of )?pod",
                    ],
                    "confidence": 0.9,
                    "priority": 1
                }
            ],
            IntentType.POD_CRASH_INVESTIGATION: [
                {
                    "patterns": [
                        r"pod .+ (?:is )?(?:crash|crashing|crashed)",
                        r"crashloop(?:backoff)?",
                        r"pod .+ (?:keeps )?restart(?:ing|s)",
                        r"why (?:is )?(?:the )?pod .+ (?:crash|restart)",
                        r"pod .+ (?:won't|doesn't|not) (?:stay up|run)",
                    ],
                    "confidence": 0.95,
                    "priority": 1
                }
            ],
            IntentType.POD_LOGS_REVIEW: [
                {
                    "patterns": [
                        r"(?:show|get|check|view) (?:the )?logs? (?:for|from|of) (?:pod )?",
                        r"what (?:do|does) (?:the )?logs? (?:say|show)",
                        r"pod .+ logs?",
                        r"logs? (?:for|from|of) .+",
                    ],
                    "confidence": 0.9,
                    "priority": 2
                }
            ],
            IntentType.POD_NOT_STARTING: [
                {
                    "patterns": [
                        r"pod .+ (?:won't|doesn't|not|can't) start",
                        r"pod .+ (?:is )?(?:stuck|pending)",
                        r"pod .+ (?:not|isn't) (?:starting|running)",
                        r"imagepullbackoff",
                        r"(?:can't|cannot) (?:pull|get) image",
                    ],
                    "confidence": 0.95,
                    "priority": 1
                }
            ],
            IntentType.POD_RESOURCE_ISSUE: [
                {
                    "patterns": [
                        r"oom(?:killed)?",
                        r"out of memory",
                        r"memory (?:limit|issue|problem)",
                        r"cpu (?:limit|issue|problem|throttl)",
                        r"resource (?:quota|limit)",
                        r"insufficient (?:cpu|memory|resources)",
                    ],
                    "confidence": 0.95,
                    "priority": 1
                }
            ],
            IntentType.SERVICE_CONNECTIVITY: [
                {
                    "patterns": [
                        r"(?:can't|cannot|unable to) (?:connect|reach) .+ service",
                        r"service .+ (?:not responding|down|unreachable)",
                        r"connection (?:refused|timeout|failed)",
                        r"(?:can't|cannot) (?:access|reach) .+",
                        r"service .+ (?:connectivity|connection)",
                    ],
                    "confidence": 0.9,
                    "priority": 1
                }
            ],
            IntentType.SERVICE_DISCOVERY: [
                {
                    "patterns": [
                        r"(?:can't|cannot) find service",
                        r"service .+ (?:not found|doesn't exist)",
                        r"(?:list|show|get) (?:all )?services",
                        r"what services (?:are )?(?:available|running)",
                    ],
                    "confidence": 0.85,
                    "priority": 2
                }
            ],
            IntentType.DNS_RESOLUTION: [
                {
                    "patterns": [
                        r"dns (?:issue|problem|error|resolution|not working)",
                        r"(?:can't|cannot) resolve .+",
                        r"name resolution (?:fail|error)",
                        r"coredns (?:issue|problem|not working)",
                    ],
                    "confidence": 0.9,
                    "priority": 1
                }
            ],
            IntentType.CONSUL_SERVICE_HEALTH: [
                {
                    "patterns": [
                        r"consul service .+ (?:health|healthy|unhealthy)",
                        r"(?:check|verify) consul (?:service )?health",
                        r"consul health check",
                        r"service .+ (?:health|status) in consul",
                    ],
                    "confidence": 0.9,
                    "priority": 1
                }
            ],
            IntentType.CONSUL_INTENTION_CHECK: [
                {
                    "patterns": [
                        r"(?:check|verify) (?:consul )?intention",
                        r"(?:can|is) .+ (?:talk to|communicate with|access) .+",
                        r"service(?:-to-)?service (?:communication|access)",
                        r"intention (?:between|from) .+ (?:to|and) .+",
                        r"(?:is )?traffic (?:allowed|blocked)",
                    ],
                    "confidence": 0.9,
                    "priority": 1
                }
            ],
            IntentType.CONSUL_CONNECT_ISSUE: [
                {
                    "patterns": [
                        r"consul connect (?:issue|problem|error|not working)",
                        r"sidecar (?:proxy )?(?:issue|problem|not working)",
                        r"envoy (?:proxy )?(?:issue|problem|error)",
                        r"upstream (?:connect|connection) (?:error|failed)",
                        r"503 (?:error|service unavailable)",
                    ],
                    "confidence": 0.95,
                    "priority": 1
                }
            ],
            IntentType.CONSUL_REGISTRATION: [
                {
                    "patterns": [
                        r"service .+ (?:not registered|not in consul)",
                        r"(?:register|registration) (?:issue|problem|failed)",
                        r"service .+ (?:not showing|missing) in consul",
                        r"consul (?:catalog|registry)",
                    ],
                    "confidence": 0.9,
                    "priority": 1
                }
            ],
            IntentType.ERROR_PATTERN_MATCH: [
                {
                    "patterns": [
                        r"(?:error|exception|failure):\s*.+",
                        r"(?:crashloopbackoff|imagepullbackoff|oomkilled)",
                        r"(?:exit code|status code|error code)\s*\d+",
                        r"(?:failed|error).*(?:message|log)",
                    ],
                    "confidence": 0.85,
                    "priority": 1
                }
            ],
            IntentType.INFORMATION_QUERY: [
                {
                    "patterns": [
                        r"(?:what|how|why|when|where) (?:is|are|does|do|can|should)",
                        r"(?:explain|describe|tell me about)",
                        r"(?:list|show) (?:all|available)",
                    ],
                    "confidence": 0.6,
                    "priority": 3
                }
            ],
        }
    
    def _initialize_flows(self) -> Dict[IntentType, TroubleshootingFlow]:
        """Initialize direct troubleshooting flows."""
        return {
            IntentType.POD_STATUS_CHECK: TroubleshootingFlow(
                name="Quick Pod Status Check",
                description="Fast path for checking pod status",
                steps=[
                    {"tool": "get_pod_status", "param": "pod_name"},
                ],
                expected_duration="2-3 seconds"
            ),
            IntentType.POD_CRASH_INVESTIGATION: TroubleshootingFlow(
                name="Pod Crash Investigation",
                description="Systematic investigation of crashing pods",
                steps=[
                    {"tool": "match_error_pattern", "param": "CrashLoopBackOff"},
                    {"tool": "get_pod_status", "param": "pod_name"},
                    {"tool": "get_pod_logs", "param": "pod_name,namespace,container"},
                    {"tool": "describe_pod", "param": "pod_name"},
                ],
                expected_duration="5-10 seconds"
            ),
            IntentType.POD_NOT_STARTING: TroubleshootingFlow(
                name="Pod Startup Investigation",
                description="Diagnose why pods won't start",
                steps=[
                    {"tool": "get_pod_status", "param": "pod_name"},
                    {"tool": "describe_pod", "param": "pod_name"},
                    {"tool": "match_error_pattern", "param": "status_condition"},
                ],
                expected_duration="5-8 seconds"
            ),
            IntentType.POD_RESOURCE_ISSUE: TroubleshootingFlow(
                name="Resource Issue Investigation",
                description="Diagnose resource-related problems",
                steps=[
                    {"tool": "match_error_pattern", "param": "OOMKilled"},
                    {"tool": "get_pod_status", "param": "pod_name"},
                    {"tool": "describe_pod", "param": "pod_name"},
                ],
                expected_duration="5-8 seconds"
            ),
            IntentType.SERVICE_CONNECTIVITY: TroubleshootingFlow(
                name="Service Connectivity Check",
                description="Diagnose service connectivity issues",
                steps=[
                    {"tool": "match_error_pattern", "param": "connection refused"},
                    {"tool": "list_pods", "param": "namespace,label_selector"},
                    {"tool": "get_pod_status", "param": "pod_name"},
                ],
                expected_duration="5-10 seconds"
            ),
            IntentType.CONSUL_SERVICE_HEALTH: TroubleshootingFlow(
                name="Consul Service Health Check",
                description="Check Consul service health status",
                steps=[
                    {"tool": "get_service_health", "param": "service_name"},
                    {"tool": "get_service_instances", "param": "service_name"},
                ],
                expected_duration="3-5 seconds"
            ),
            IntentType.CONSUL_INTENTION_CHECK: TroubleshootingFlow(
                name="Consul Intention Verification",
                description="Verify service-to-service access",
                steps=[
                    {"tool": "check_consul_intention", "param": "source,destination"},
                    {"tool": "list_consul_intentions", "param": ""},
                ],
                expected_duration="3-5 seconds"
            ),
            IntentType.CONSUL_CONNECT_ISSUE: TroubleshootingFlow(
                name="Consul Connect Troubleshooting",
                description="Diagnose Consul Connect issues",
                steps=[
                    {"tool": "match_error_pattern", "param": "upstream connect error,consul"},
                    {"tool": "get_service_health", "param": "service_name"},
                    {"tool": "check_consul_intention", "param": "source,destination"},
                ],
                expected_duration="5-10 seconds"
            ),
            IntentType.ERROR_PATTERN_MATCH: TroubleshootingFlow(
                name="Error Pattern Recognition",
                description="Match against known error patterns",
                steps=[
                    {"tool": "match_error_pattern", "param": "error_text"},
                ],
                expected_duration="1-2 seconds"
            ),
        }
    
    def classify(self, query: str) -> Intent:
        """
        Classify a user query into an intent.
        
        Args:
            query: User's troubleshooting query
        
        Returns:
            Intent object with classification results
        """
        query_lower = query.lower().strip()
        
        # Extract entities first
        entities = self._extract_entities(query)
        
        # Try to match against patterns
        best_match = None
        best_confidence = 0.0
        
        for intent_type, pattern_groups in self.patterns.items():
            for pattern_group in pattern_groups:
                for pattern in pattern_group["patterns"]:
                    if re.search(pattern, query_lower):
                        confidence = pattern_group["confidence"]
                        
                        # Boost confidence if entities are found
                        if entities:
                            confidence = min(1.0, confidence + 0.05)
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = intent_type
        
        # Default to general troubleshooting if no match
        if best_match is None:
            best_match = IntentType.GENERAL_TROUBLESHOOTING
            best_confidence = 0.5
        
        # Get suggested flow
        flow = self.flows.get(best_match)
        suggested_flow = flow.name if flow else "Standard Agent Flow"
        
        # Determine priority
        priority = self._get_priority(best_match, entities)
        
        return Intent(
            intent_type=best_match,
            confidence=best_confidence,
            entities=entities,
            suggested_flow=suggested_flow,
            priority=priority
        )
    
    def _extract_entities(self, query: str) -> Dict[str, str]:
        """
        Extract entities from the query (pod names, namespaces, services, etc.).
        
        Args:
            query: User query
        
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract pod names (common patterns)
        pod_match = re.search(r"pod\s+([a-z0-9][-a-z0-9]*)", query.lower())
        if pod_match:
            entities["pod_name"] = pod_match.group(1)
        
        # Extract namespace
        ns_match = re.search(r"(?:namespace|ns)\s+([a-z0-9][-a-z0-9]*)", query.lower())
        if ns_match:
            entities["namespace"] = ns_match.group(1)
        
        # Extract service names
        svc_match = re.search(r"service\s+([a-z0-9][-a-z0-9]*)", query.lower())
        if svc_match:
            entities["service_name"] = svc_match.group(1)
        
        # Extract error messages (quoted text or after "error:")
        error_match = re.search(r'(?:error|exception):\s*["\']?([^"\']+)["\']?', query, re.IGNORECASE)
        if error_match:
            entities["error_text"] = error_match.group(1).strip()
        
        # Extract source and destination for intentions
        intention_match = re.search(r"(?:from|source)\s+([a-z0-9][-a-z0-9]*)\s+(?:to|destination|and)\s+([a-z0-9][-a-z0-9]*)", query.lower())
        if intention_match:
            entities["source_service"] = intention_match.group(1)
            entities["destination_service"] = intention_match.group(2)
        
        return entities
    
    def _get_priority(self, intent_type: IntentType, entities: Dict[str, str]) -> int:
        """
        Determine priority based on intent type and entities.
        
        Args:
            intent_type: Classified intent type
            entities: Extracted entities
        
        Returns:
            Priority level (1-5, where 1 is highest)
        """
        # Critical issues get priority 1
        critical_intents = [
            IntentType.POD_CRASH_INVESTIGATION,
            IntentType.POD_NOT_STARTING,
            IntentType.POD_RESOURCE_ISSUE,
            IntentType.CONSUL_CONNECT_ISSUE,
        ]
        
        if intent_type in critical_intents:
            return 1
        
        # High priority issues
        high_priority_intents = [
            IntentType.SERVICE_CONNECTIVITY,
            IntentType.CONSUL_SERVICE_HEALTH,
            IntentType.CONSUL_INTENTION_CHECK,
        ]
        
        if intent_type in high_priority_intents:
            return 2
        
        # Medium priority
        medium_priority_intents = [
            IntentType.POD_STATUS_CHECK,
            IntentType.ERROR_PATTERN_MATCH,
        ]
        
        if intent_type in medium_priority_intents:
            return 3
        
        # Lower priority for informational queries
        return 4
    
    def get_flow(self, intent_type: IntentType) -> Optional[TroubleshootingFlow]:
        """
        Get the troubleshooting flow for an intent type.
        
        Args:
            intent_type: Intent type
        
        Returns:
            TroubleshootingFlow or None
        """
        return self.flows.get(intent_type)
    
    def should_use_fast_path(self, intent: Intent) -> bool:
        """
        Determine if fast-path routing should be used.
        
        Args:
            intent: Classified intent
        
        Returns:
            True if fast-path should be used
        """
        # Use fast path for high-confidence, high-priority intents with flows
        return (
            intent.confidence >= 0.85 and
            intent.priority <= 2 and
            intent.intent_type in self.flows
        )


# Global classifier instance
intent_classifier = IntentClassifier()


def classify_intent(query: str) -> Intent:
    """
    Convenience function to classify a query.
    
    Args:
        query: User query
    
    Returns:
        Intent object
    """
    return intent_classifier.classify(query)


# Made with Bob