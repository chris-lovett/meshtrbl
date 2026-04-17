"""
Main agent implementation using LangChain.
"""

import os
from typing import Optional
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from .tools import KubernetesTools, ConsulTools
from .prompts.system_prompts import SYSTEM_PROMPT, REACT_PROMPT_TEMPLATE


class TroubleshootingAgent:
    """
    AI agent for troubleshooting Kubernetes and Consul service mesh issues.
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 model: str = "gpt-4-turbo-preview",
                 temperature: float = 0.1,
                 k8s_namespace: str = "default",
                 consul_host: str = "localhost",
                 consul_port: int = 8500,
                 consul_token: Optional[str] = None,
                 verbose: bool = False):
        """
        Initialize the troubleshooting agent.
        
        Args:
            openai_api_key: OpenAI API key (reads from env if not provided)
            model: LLM model to use
            temperature: Temperature for LLM responses
            k8s_namespace: Default Kubernetes namespace
            consul_host: Consul server host
            consul_port: Consul server port
            consul_token: Consul ACL token
            verbose: Enable verbose logging
        """
        # Load environment variables
        load_dotenv()
        
        # Set up OpenAI - ensure API key is in environment
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        # Set the API key in environment if provided as parameter
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize LLM (will automatically use OPENAI_API_KEY from environment)
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature
        )
        
        # Initialize tools
        self.k8s_tools = KubernetesTools(namespace=k8s_namespace)
        self.consul_tools = ConsulTools(
            host=consul_host,
            port=consul_port,
            token=consul_token
        )
        
        # Create LangChain tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent = self._create_agent()
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            max_iterations=10,
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> list:
        """Create LangChain tools from Kubernetes and Consul tools."""
        
        tools = [
            # Kubernetes tools
            Tool(
                name="get_pod_status",
                func=lambda x: self._parse_and_call(self.k8s_tools.get_pod_status, x),
                description="""Get the status of a Kubernetes pod. 
                Input should be: pod_name or pod_name,namespace
                Example: "my-app-pod" or "my-app-pod,production"
                Use this to check if a pod is running, pending, or has errors."""
            ),
            Tool(
                name="get_pod_logs",
                func=lambda x: self._parse_and_call(self.k8s_tools.get_pod_logs, x),
                description="""Get logs from a Kubernetes pod.
                Input should be: pod_name or pod_name,namespace or pod_name,namespace,container
                Example: "my-app-pod" or "my-app-pod,production" or "my-app-pod,production,app-container"
                Use this to investigate application errors or crashes."""
            ),
            Tool(
                name="list_pods",
                func=lambda x: self._parse_and_call(self.k8s_tools.list_pods, x),
                description="""List all pods in a namespace.
                Input should be: namespace or namespace,label_selector
                Example: "default" or "production,app=myapp"
                Use this to see all pods and their status."""
            ),
            Tool(
                name="describe_pod",
                func=lambda x: self._parse_and_call(self.k8s_tools.describe_pod, x),
                description="""Get detailed information about a pod (similar to kubectl describe).
                Input should be: pod_name or pod_name,namespace
                Example: "my-app-pod" or "my-app-pod,production"
                Use this to see events, configuration, and detailed status."""
            ),
            
            # Consul tools
            Tool(
                name="list_consul_services",
                func=lambda x: self.consul_tools.list_services(),
                description="""List all services registered in Consul.
                Input: empty string or datacenter name
                Use this to see what services are available in the service mesh."""
            ),
            Tool(
                name="get_service_health",
                func=lambda x: self.consul_tools.get_service_health(x),
                description="""Get health status of a Consul service.
                Input should be: service_name
                Example: "web-service"
                Use this to check if a service is healthy and see health check details."""
            ),
            Tool(
                name="get_service_instances",
                func=lambda x: self.consul_tools.get_service_instances(x),
                description="""Get all instances of a Consul service.
                Input should be: service_name
                Example: "web-service"
                Use this to see where service instances are running."""
            ),
            Tool(
                name="list_consul_intentions",
                func=lambda x: self.consul_tools.list_intentions(),
                description="""List all Consul Connect intentions (service-to-service access rules).
                Input: empty string
                Use this to see which services can communicate with each other."""
            ),
            Tool(
                name="check_consul_intention",
                func=lambda x: self._parse_and_call(self.consul_tools.check_intention, x),
                description="""Check if traffic is allowed between two services.
                Input should be: source_service,destination_service
                Example: "web,api"
                Use this to troubleshoot service-to-service communication issues."""
            ),
            Tool(
                name="get_consul_members",
                func=lambda x: self.consul_tools.get_agent_members(),
                description="""Get Consul cluster members.
                Input: empty string
                Use this to check cluster health and member status."""
            ),
        ]
        
        return tools
    
    def _parse_and_call(self, func, input_str: str):
        """Parse comma-separated input and call function with appropriate arguments."""
        if not input_str or input_str.strip() == "":
            return func()
        
        parts = [p.strip() for p in input_str.split(',')]
        
        try:
            return func(*parts)
        except TypeError as e:
            return f"Error: Invalid input format. {str(e)}"
    
    def _create_agent(self):
        """Create the ReAct agent."""
        
        # Create prompt with system message
        prompt = PromptTemplate.from_template(
            SYSTEM_PROMPT + "\n\n" + REACT_PROMPT_TEMPLATE
        )
        
        # Create ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return agent
    
    def run(self, query: str) -> str:
        """
        Run the agent with a troubleshooting query.
        
        Args:
            query: The troubleshooting question or issue description
            
        Returns:
            Agent's response with diagnosis and recommendations
        """
        try:
            result = self.agent_executor.invoke({"input": query})
            return result["output"]
        except Exception as e:
            return f"Error running agent: {str(e)}"
    
    def chat(self):
        """
        Start an interactive chat session with the agent.
        """
        print("=" * 70)
        print("Kubernetes & Consul Troubleshooting Agent")
        print("=" * 70)
        print("\nI'm here to help you troubleshoot Kubernetes and Consul issues.")
        print("Type 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye! Happy troubleshooting!")
                    break
                
                if not user_input:
                    continue
                
                print("\nAgent: ", end="", flush=True)
                response = self.run(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! Happy troubleshooting!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")


def main():
    """Main entry point for the agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kubernetes & Consul Troubleshooting Agent")
    parser.add_argument("--model", default="gpt-4-turbo-preview", help="OpenAI model to use")
    parser.add_argument("--namespace", default="default", help="Default Kubernetes namespace")
    parser.add_argument("--consul-host", default="localhost", help="Consul server host")
    parser.add_argument("--consul-port", type=int, default=8500, help="Consul server port")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--query", help="Single query to run (non-interactive mode)")
    
    args = parser.parse_args()
    
    # Create agent
    agent = TroubleshootingAgent(
        model=args.model,
        k8s_namespace=args.namespace,
        consul_host=args.consul_host,
        consul_port=args.consul_port,
        verbose=args.verbose
    )
    
    # Run in appropriate mode
    if args.query:
        # Single query mode
        response = agent.run(args.query)
        print(response)
    else:
        # Interactive chat mode
        agent.chat()


if __name__ == "__main__":
    main()

# Made with Bob
