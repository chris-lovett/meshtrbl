"""
Basic tests for the troubleshooting agent.
"""

import pytest
from unittest.mock import Mock, patch
import os


class TestAgentInitialization:
    """Test agent initialization."""
    
    def test_agent_requires_api_key(self):
        """Test that agent requires OpenAI API key."""
        from src.agent import TroubleshootingAgent
        
        # Clear environment variable if set
        old_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        try:
            with pytest.raises(ValueError, match="OpenAI API key"):
                TroubleshootingAgent()
        finally:
            # Restore environment variable
            if old_key:
                os.environ['OPENAI_API_KEY'] = old_key


class TestKubernetesTools:
    """Test Kubernetes tools."""
    
    @patch('src.tools.kubernetes.config')
    @patch('src.tools.kubernetes.client')
    def test_kubernetes_tools_initialization(self, mock_client, mock_config):
        """Test that Kubernetes tools can be initialized."""
        from src.tools import KubernetesTools
        
        # Mock the config loading
        mock_config.load_kube_config = Mock()
        mock_client.CoreV1Api = Mock()
        mock_client.AppsV1Api = Mock()
        
        tools = KubernetesTools(namespace="test")
        assert tools.namespace == "test"


class TestConsulTools:
    """Test Consul tools."""
    
    @patch('src.tools.consul_tools.consul.Consul')
    def test_consul_tools_initialization(self, mock_consul):
        """Test that Consul tools can be initialized."""
        from src.tools import ConsulTools
        
        # Mock the Consul client
        mock_instance = Mock()
        mock_instance.agent.self.return_value = {}
        mock_consul.return_value = mock_instance
        
        tools = ConsulTools(host="localhost", port=8500)
        assert tools.datacenter == "dc1"


# Note: Full integration tests require actual K8s and Consul clusters
# These are basic unit tests to verify the structure

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
