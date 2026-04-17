"""
Kubernetes inspection tools for the troubleshooting agent.
"""

from typing import Optional, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os


class KubernetesTools:
    """Tools for inspecting Kubernetes clusters."""
    
    def __init__(self, kubeconfig_path: Optional[str] = None, namespace: str = "default"):
        """
        Initialize Kubernetes client.
        
        Args:
            kubeconfig_path: Path to kubeconfig file (None for default)
            namespace: Default namespace to use
        """
        self.namespace = namespace
        
        try:
            if kubeconfig_path and os.path.exists(kubeconfig_path):
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                # Try in-cluster config first, then default kubeconfig
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
            
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            
        except Exception as e:
            raise Exception(f"Failed to initialize Kubernetes client: {str(e)}")
    
    def get_pod_status(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Get the status of a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Formatted string with pod status information
        """
        ns = namespace or self.namespace
        
        try:
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=ns)
            
            status_info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "conditions": [],
                "container_statuses": []
            }
            
            # Get pod conditions
            if pod.status.conditions:
                for condition in pod.status.conditions:
                    status_info["conditions"].append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message
                    })
            
            # Get container statuses
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    container_info = {
                        "name": container.name,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "image": container.image
                    }
                    
                    # Get container state
                    if container.state.running:
                        container_info["state"] = "Running"
                        container_info["started_at"] = str(container.state.running.started_at)
                    elif container.state.waiting:
                        container_info["state"] = "Waiting"
                        container_info["reason"] = container.state.waiting.reason
                        container_info["message"] = container.state.waiting.message
                    elif container.state.terminated:
                        container_info["state"] = "Terminated"
                        container_info["reason"] = container.state.terminated.reason
                        container_info["exit_code"] = container.state.terminated.exit_code
                        container_info["message"] = container.state.terminated.message
                    
                    status_info["container_statuses"].append(container_info)
            
            return self._format_pod_status(status_info)
            
        except ApiException as e:
            if e.status == 404:
                return f"Pod '{pod_name}' not found in namespace '{ns}'"
            return f"Error getting pod status: {e.reason}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_pod_logs(self, pod_name: str, namespace: Optional[str] = None, 
                     container: Optional[str] = None, tail_lines: int = 100) -> str:
        """
        Get logs from a pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace (uses default if not specified)
            container: Specific container name (optional)
            tail_lines: Number of lines to retrieve from the end
            
        Returns:
            Pod logs as a string
        """
        ns = namespace or self.namespace
        
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=ns,
                container=container,
                tail_lines=tail_lines
            )
            
            header = f"=== Logs for pod '{pod_name}' in namespace '{ns}'"
            if container:
                header += f" (container: {container})"
            header += f" (last {tail_lines} lines) ===\n"
            
            return header + logs
            
        except ApiException as e:
            if e.status == 404:
                return f"Pod '{pod_name}' not found in namespace '{ns}'"
            return f"Error getting pod logs: {e.reason}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def list_pods(self, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> str:
        """
        List pods in a namespace.
        
        Args:
            namespace: Namespace (uses default if not specified)
            label_selector: Label selector to filter pods (e.g., "app=myapp")
            
        Returns:
            Formatted list of pods
        """
        ns = namespace or self.namespace
        
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=ns,
                label_selector=label_selector
            )
            
            if not pods.items:
                return f"No pods found in namespace '{ns}'"
            
            result = f"=== Pods in namespace '{ns}' ===\n"
            if label_selector:
                result = f"=== Pods in namespace '{ns}' with labels '{label_selector}' ===\n"
            
            for pod in pods.items:
                status = pod.status.phase
                ready_containers = 0
                total_containers = 0
                
                if pod.status.container_statuses:
                    total_containers = len(pod.status.container_statuses)
                    ready_containers = sum(1 for c in pod.status.container_statuses if c.ready)
                
                restarts = sum(c.restart_count for c in pod.status.container_statuses) if pod.status.container_statuses else 0
                
                result += f"\n{pod.metadata.name}:\n"
                result += f"  Status: {status}\n"
                result += f"  Ready: {ready_containers}/{total_containers}\n"
                result += f"  Restarts: {restarts}\n"
                result += f"  Age: {self._calculate_age(pod.metadata.creation_timestamp)}\n"
            
            return result
            
        except ApiException as e:
            return f"Error listing pods: {e.reason}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def describe_pod(self, pod_name: str, namespace: Optional[str] = None) -> str:
        """
        Get detailed information about a pod (similar to kubectl describe).
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace (uses default if not specified)
            
        Returns:
            Detailed pod information
        """
        ns = namespace or self.namespace
        
        try:
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=ns)
            
            result = f"=== Pod Description: {pod_name} ===\n\n"
            result += f"Namespace: {pod.metadata.namespace}\n"
            result += f"Node: {pod.spec.node_name}\n"
            result += f"Status: {pod.status.phase}\n"
            result += f"IP: {pod.status.pod_ip}\n"
            
            # Labels
            if pod.metadata.labels:
                result += "\nLabels:\n"
                for key, value in pod.metadata.labels.items():
                    result += f"  {key}: {value}\n"
            
            # Annotations (Consul-related ones)
            if pod.metadata.annotations:
                consul_annotations = {k: v for k, v in pod.metadata.annotations.items() 
                                     if 'consul' in k.lower()}
                if consul_annotations:
                    result += "\nConsul Annotations:\n"
                    for key, value in consul_annotations.items():
                        result += f"  {key}: {value}\n"
            
            # Containers
            result += "\nContainers:\n"
            for container in pod.spec.containers:
                result += f"\n  {container.name}:\n"
                result += f"    Image: {container.image}\n"
                if container.resources:
                    if container.resources.requests:
                        result += f"    Requests: {dict(container.resources.requests)}\n"
                    if container.resources.limits:
                        result += f"    Limits: {dict(container.resources.limits)}\n"
            
            # Events
            events = self.v1.list_namespaced_event(
                namespace=ns,
                field_selector=f"involvedObject.name={pod_name}"
            )
            
            if events.items:
                result += "\nRecent Events:\n"
                for event in sorted(events.items, 
                                   key=lambda x: x.last_timestamp or x.event_time, 
                                   reverse=True)[:10]:
                    result += f"  {event.type}: {event.reason} - {event.message}\n"
            
            return result
            
        except ApiException as e:
            if e.status == 404:
                return f"Pod '{pod_name}' not found in namespace '{ns}'"
            return f"Error describing pod: {e.reason}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _format_pod_status(self, status_info: Dict[str, Any]) -> str:
        """Format pod status information for display."""
        result = f"=== Pod Status: {status_info['name']} ===\n\n"
        result += f"Namespace: {status_info['namespace']}\n"
        result += f"Phase: {status_info['phase']}\n\n"
        
        if status_info['conditions']:
            result += "Conditions:\n"
            for condition in status_info['conditions']:
                result += f"  {condition['type']}: {condition['status']}"
                if condition['reason']:
                    result += f" (Reason: {condition['reason']})"
                if condition['message']:
                    result += f"\n    Message: {condition['message']}"
                result += "\n"
        
        if status_info['container_statuses']:
            result += "\nContainer Statuses:\n"
            for container in status_info['container_statuses']:
                result += f"\n  {container['name']}:\n"
                result += f"    Image: {container['image']}\n"
                result += f"    Ready: {container['ready']}\n"
                result += f"    Restart Count: {container['restart_count']}\n"
                result += f"    State: {container['state']}\n"
                
                if 'reason' in container:
                    result += f"    Reason: {container['reason']}\n"
                if 'message' in container:
                    result += f"    Message: {container['message']}\n"
                if 'exit_code' in container:
                    result += f"    Exit Code: {container['exit_code']}\n"
        
        return result
    
    def _calculate_age(self, creation_timestamp) -> str:
        """Calculate age of a resource."""
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        age = now - creation_timestamp
        
        days = age.days
        hours = age.seconds // 3600
        minutes = (age.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d{hours}h"
        elif hours > 0:
            return f"{hours}h{minutes}m"
        else:
            return f"{minutes}m"

# Made with Bob
