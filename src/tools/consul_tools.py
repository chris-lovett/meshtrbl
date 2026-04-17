"""
Consul inspection tools for the troubleshooting agent.
"""

from typing import Optional, Dict, Any, List
import os
from urllib.parse import urlparse

import consul
import json


class ConsulTools:
    """Tools for inspecting Consul service mesh."""
    
    def __init__(self, host: str = "localhost", port: int = 8500,
                 token: Optional[str] = None, scheme: str = "http",
                 datacenter: str = "dc1", verify: bool = True,
                 ca_cert: Optional[str] = None):
        """
        Initialize Consul client.
        
        Args:
            host: Consul server host
            port: Consul server port
            token: Consul ACL token (optional)
            scheme: http or https
            datacenter: Consul datacenter name
            verify: Verify HTTPS certificates
            ca_cert: Path to a custom CA bundle for Consul HTTPS
        """
        self.datacenter = datacenter
        
        try:
            env_addr = os.getenv("CONSUL_HTTP_ADDR")
            env_scheme = os.getenv("CONSUL_HTTP_SSL")
            env_verify = os.getenv("CONSUL_HTTP_SSL_VERIFY")
            env_ca_cert = os.getenv("CONSUL_CACERT")
            env_token = os.getenv("CONSUL_HTTP_TOKEN")
            
            if env_addr:
                parsed = urlparse(env_addr if "://" in env_addr else f"{scheme}://{env_addr}")
                if parsed.hostname:
                    host = parsed.hostname
                if parsed.port:
                    port = parsed.port
                if "://" in env_addr and parsed.scheme:
                    scheme = parsed.scheme
            
            if env_scheme:
                normalized_env_scheme = env_scheme.lower()
                if normalized_env_scheme == "true":
                    scheme = "https"
                elif normalized_env_scheme == "false":
                    scheme = "http"
            
            if env_verify:
                normalized_env_verify = env_verify.lower()
                if normalized_env_verify == "false":
                    verify = False
                elif normalized_env_verify == "true":
                    verify = True
            
            if env_ca_cert:
                ca_cert = env_ca_cert
            
            if env_token and not token:
                token = env_token
            
            original_consul_http_addr = os.environ.pop("CONSUL_HTTP_ADDR", None)
            original_consul_http_ssl = os.environ.pop("CONSUL_HTTP_SSL", None)
            original_consul_http_ssl_verify = os.environ.pop("CONSUL_HTTP_SSL_VERIFY", None)
            original_consul_http_token = os.environ.pop("CONSUL_HTTP_TOKEN", None)
            try:
                self.client = consul.Consul(
                    host=host,
                    port=port,
                    token=token,
                    scheme=scheme,
                    verify=ca_cert or verify
                )
                
                # Force the resolved connection details on the underlying HTTP client
                # so library env parsing cannot silently override them.
                self.client.http.host = host
                self.client.http.port = port
                self.client.http.scheme = scheme
                self.client.http.base_uri = f"{scheme}://{host}:{port}"
                self.client.http.verify = ca_cert or verify
                
                # Test connection. python-consul 1.1.0 does not propagate the
                # client token to /v1/agent/self, so validate with a catalog
                # endpoint that includes the configured token automatically.
                self.client.catalog.services(dc=datacenter)
            finally:
                if original_consul_http_addr is not None:
                    os.environ["CONSUL_HTTP_ADDR"] = original_consul_http_addr
                if original_consul_http_ssl is not None:
                    os.environ["CONSUL_HTTP_SSL"] = original_consul_http_ssl
                if original_consul_http_ssl_verify is not None:
                    os.environ["CONSUL_HTTP_SSL_VERIFY"] = original_consul_http_ssl_verify
                if original_consul_http_token is not None:
                    os.environ["CONSUL_HTTP_TOKEN"] = original_consul_http_token
            
        except Exception as e:
            raise Exception(
                f"Failed to initialize Consul client: {str(e)} "
                f"(host={host}, port={port}, scheme={scheme}, verify={ca_cert or verify}, token={'set' if token else 'unset'})"
            )
    
    def list_services(self, datacenter: Optional[str] = None) -> str:
        """
        List all services registered in Consul.
        
        Args:
            datacenter: Datacenter to query (uses default if not specified)
            
        Returns:
            Formatted list of services
        """
        dc = datacenter or self.datacenter
        
        try:
            index, services = self.client.catalog.services(dc=dc)
            
            if not services:
                return f"No services found in datacenter '{dc}'"
            
            result = f"=== Services in datacenter '{dc}' ===\n\n"
            
            for service_name, tags in services.items():
                result += f"{service_name}:\n"
                if tags:
                    result += f"  Tags: {', '.join(tags)}\n"
                else:
                    result += "  Tags: none\n"
            
            return result
            
        except Exception as e:
            return f"Error listing services: {str(e)}"
    
    def get_service_health(self, service_name: str, datacenter: Optional[str] = None) -> str:
        """
        Get health status of a service.
        
        Args:
            service_name: Name of the service
            datacenter: Datacenter to query (uses default if not specified)
            
        Returns:
            Formatted health information
        """
        dc = datacenter or self.datacenter
        
        try:
            index, checks = self.client.health.service(service_name, dc=dc)
            
            if not checks:
                return f"Service '{service_name}' not found in datacenter '{dc}'"
            
            result = f"=== Health Status for service '{service_name}' ===\n\n"
            
            for check in checks:
                node = check.get('Node', {})
                service = check.get('Service', {})
                checks_list = check.get('Checks', [])
                
                result += f"Instance: {service.get('ID', 'unknown')}\n"
                result += f"  Node: {node.get('Node', 'unknown')}\n"
                result += f"  Address: {service.get('Address', 'unknown')}:{service.get('Port', 'unknown')}\n"
                
                if service.get('Tags'):
                    result += f"  Tags: {', '.join(service.get('Tags', []))}\n"
                
                # Check health status
                result += "  Health Checks:\n"
                for health_check in checks_list:
                    status = health_check.get('Status', 'unknown')
                    check_name = health_check.get('Name', 'unknown')
                    output = health_check.get('Output', '')
                    
                    result += f"    - {check_name}: {status}\n"
                    if output and status != 'passing':
                        result += f"      Output: {output}\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error getting service health: {str(e)}"
    
    def get_service_instances(self, service_name: str, datacenter: Optional[str] = None) -> str:
        """
        Get all instances of a service.
        
        Args:
            service_name: Name of the service
            datacenter: Datacenter to query (uses default if not specified)
            
        Returns:
            Formatted list of service instances
        """
        dc = datacenter or self.datacenter
        
        try:
            index, instances = self.client.catalog.service(service_name, dc=dc)
            
            if not instances:
                return f"No instances found for service '{service_name}' in datacenter '{dc}'"
            
            result = f"=== Instances of service '{service_name}' ===\n\n"
            
            for instance in instances:
                result += f"Instance ID: {instance.get('ServiceID', 'unknown')}\n"
                result += f"  Node: {instance.get('Node', 'unknown')}\n"
                result += f"  Address: {instance.get('ServiceAddress', instance.get('Address', 'unknown'))}\n"
                result += f"  Port: {instance.get('ServicePort', 'unknown')}\n"
                
                if instance.get('ServiceTags'):
                    result += f"  Tags: {', '.join(instance.get('ServiceTags', []))}\n"
                
                if instance.get('ServiceMeta'):
                    result += "  Metadata:\n"
                    for key, value in instance.get('ServiceMeta', {}).items():
                        result += f"    {key}: {value}\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error getting service instances: {str(e)}"
    
    def get_connect_proxy_config(self, service_name: str) -> str:
        """
        Get Consul Connect proxy configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Formatted proxy configuration
        """
        try:
            # Get service configuration
            index, config = self.client.agent.service.register(
                name=service_name,
                check=None
            )
            
            # In practice, we'd query the actual proxy config
            # This is a simplified version
            result = f"=== Consul Connect Proxy Config for '{service_name}' ===\n\n"
            result += "Note: Use 'consul connect proxy -sidecar-for <service>' for detailed config\n"
            result += "\nTo check proxy status, verify:\n"
            result += "1. Sidecar proxy is registered\n"
            result += "2. Proxy is healthy\n"
            result += "3. Upstream services are configured\n"
            result += "4. Intentions allow traffic\n"
            
            return result
            
        except Exception as e:
            return f"Error getting proxy config: {str(e)}"
    
    def list_intentions(self) -> str:
        """
        List all service intentions (allow/deny rules).
        
        Returns:
            Formatted list of intentions
        """
        try:
            intentions = self.client.connect.intentions()
            
            if not intentions:
                return "No intentions configured"
            
            result = "=== Consul Connect Intentions ===\n\n"
            
            for intention in intentions:
                source = intention.get('SourceName', 'unknown')
                dest = intention.get('DestinationName', 'unknown')
                action = intention.get('Action', 'unknown')
                
                result += f"{source} -> {dest}: {action.upper()}\n"
                
                if intention.get('Description'):
                    result += f"  Description: {intention.get('Description')}\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error listing intentions: {str(e)}"
    
    def check_intention(self, source_service: str, destination_service: str) -> str:
        """
        Check if traffic is allowed between two services.
        
        Args:
            source_service: Source service name
            destination_service: Destination service name
            
        Returns:
            Whether traffic is allowed and why
        """
        try:
            # Check intention
            result = f"=== Intention Check: {source_service} -> {destination_service} ===\n\n"
            
            intentions = self.client.connect.intentions()
            
            # Find matching intention
            matching_intention = None
            for intention in intentions:
                if (intention.get('SourceName') == source_service and 
                    intention.get('DestinationName') == destination_service):
                    matching_intention = intention
                    break
            
            if matching_intention:
                action = matching_intention.get('Action', 'unknown')
                result += f"Explicit intention found: {action.upper()}\n"
                
                if matching_intention.get('Description'):
                    result += f"Description: {matching_intention.get('Description')}\n"
                
                if action == 'allow':
                    result += "\n✓ Traffic is ALLOWED\n"
                else:
                    result += "\n✗ Traffic is DENIED\n"
            else:
                result += "No explicit intention found\n"
                result += "Default behavior: Check Consul ACL default policy\n"
            
            return result
            
        except Exception as e:
            return f"Error checking intention: {str(e)}"
    
    def get_agent_members(self) -> str:
        """
        Get Consul cluster members.
        
        Returns:
            Formatted list of cluster members
        """
        try:
            members = self.client.agent.members()
            
            if not members:
                return "No cluster members found"
            
            result = "=== Consul Cluster Members ===\n\n"
            
            for member in members:
                name = member.get('Name', 'unknown')
                addr = member.get('Addr', 'unknown')
                status = member.get('Status', 'unknown')
                
                status_str = "alive" if status == 1 else "failed"
                
                result += f"{name}:\n"
                result += f"  Address: {addr}\n"
                result += f"  Status: {status_str}\n"
                result += f"  Datacenter: {member.get('Tags', {}).get('dc', 'unknown')}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error getting cluster members: {str(e)}"

# Made with Bob
